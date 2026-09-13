"""
内置下载器服务
下载项目源码 ZIP / Release 文件 / README / git clone
与 ABDownloadManager 思路一致：任务由独立工作线程流式下载，进度实时更新
"""
import asyncio
import subprocess
import os
import re
from pathlib import Path
from datetime import datetime

import httpx
from loguru import logger

from app.database import SessionLocal
from app.models.download_task import DownloadTask
from app.services.github_service import _get_headers
from app.config import GITHUB_API_BASE_URL, BASE_DIR, GITHUB_TOKEN, GITHUB_VERIFY_SSL

# 默认下载目录（项目根目录下的 downloads，与用户指定的桌面路径一致）
DEFAULT_DOWNLOAD_DIR = BASE_DIR.parent / "downloads"


def get_default_download_dir() -> str:
    DEFAULT_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return str(DEFAULT_DOWNLOAD_DIR)


def _resolve_save_dir(save_dir: str) -> Path:
    """解析保存目录：留空用默认目录，绝对路径则使用之"""
    if save_dir and save_dir.strip():
        path = Path(save_dir.strip())
    else:
        path = DEFAULT_DOWNLOAD_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    """净化文件名，避免路径注入"""
    name = name.replace("/", "_").replace("\\", "_").replace("..", "_")
    name = "".join(c for c in name if c not in '<>:"|?*').strip()
    return name or "download"


def _update_task(task_id: int, **fields):
    """更新任务字段（独立会话写库）"""
    db = SessionLocal()
    try:
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        if task:
            for k, v in fields.items():
                setattr(task, k, v)
            db.commit()
    except Exception as e:
        logger.error(f"更新任务 {task_id} 失败: {e}")
    finally:
        db.close()


def _sanitize_url(url: str) -> str:
    """校验 URL 仅允许 GitHub 相关域名，防止 SSRF/路径注入"""
    if not url:
        return ""
    allowed_prefixes = (
        "https://github.com/",
        "https://codeload.github.com/",
        "https://raw.githubusercontent.com/",
        "https://api.github.com/",
        "https://objects.githubusercontent.com/",
        "https://release-assets.githubusercontent.com/",
    )
    if not url.startswith(allowed_prefixes):
        raise ValueError("仅支持下载 GitHub 域名的资源")
    return url


def _normalize_download_url(url: str) -> str:
    """将慢速的 github.com archive/releases 重定向链接转成可直连的 codeload 链"""
    if not url:
        return url
    # github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip -> codeload 直链
    # 注意：codeload 的正确格式不带 .zip 后缀
    import re
    m = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/archive/refs/heads/([^/]+?)(?:\.zip)?/?$",
        url,
    )
    if m:
        owner, repo, branch = m.group(1), m.group(2), m.group(3)
        return f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
    return url


# ---------- 各类别下载链接构造 ----------

def build_zip_url(author: str, repo: str, default_branch: str = "main") -> str:
    # 使用 codeload.github.com 直链，避免 github.com 的 archive 重定向超时
    return f"https://codeload.github.com/{author}/{repo}/zip/refs/heads/{default_branch}"


def build_readme_url(author: str, repo: str, default_branch: str = "main") -> str:
    return f"https://raw.githubusercontent.com/{author}/{repo}/{default_branch}/README.md"


def build_clone_url(author: str, repo: str, use_http: bool = True) -> str:
    if use_http:
        return f"https://github.com/{author}/{repo}.git"
    return f"git@github.com:{author}/{repo}.git"


_ORIGIN_RE = re.compile(r"^https?://github\.com/(.+)$")


def is_direct_github_url(url: str) -> bool:
    """判断 URL 是否是需要镜像加持的 github.com 直连地址"""
    u = url.strip()
    return u.startswith("git@github.com:") or bool(_ORIGIN_RE.match(u))


def apply_mirror(url: str, mirror: str) -> str:
    """用镜像前缀拼接出可 clone 的地址。

    mirror 填法（任选其一）：
      - https://ghfast.top/            -> .../ghfast.top/https://github.com/o/r.git
      - https://ghproxy.com/https://github.com  -> 直接拼
    ssh 地址不支持镜像，原样返回。
    """
    mirror = (mirror or "").strip().rstrip("/")
    url = url.strip()
    if not mirror:
        return url
    if url.startswith("git@github.com:") or url.startswith("ssh://"):
        return url
    m = _ORIGIN_RE.match(url)
    path = m.group(1) if m else url.lstrip("/")
    return f"{mirror}/{path}"


def load_clone_mirrors() -> list:
    """读取 .env 配置的全局镜像回退列表（GITHUB_CLONE_MIRRORS，逗号分隔）。
    直连失败时依次尝试，列表为空则只直连。
    """
    raw = os.getenv("GITHUB_CLONE_MIRRORS", "")
    return [x.strip().strip("/").strip() for x in raw.split(",") if x.strip()]


def _build_ssh443_url(url: str):
    """github.com 的 443/HTTPS 被 SNI 干扰时，回退到 GitHub 官方备用通道 ssh.github.com:443。

    返回 `ssh://git@ssh.github.com:443/{owner}/{repo}.git`；非 github.com 直连地址返回 None。
    """
    if url.startswith("git@github.com:") or url.startswith("ssh://"):
        return None
    m = _ORIGIN_RE.match(url.strip())
    if not m:
        return None
    path = m.group(1).strip().lstrip("/")
    if not path or "/" not in path:
        return None
    if not path.endswith(".git"):
        path = path.rstrip("/") + ".git"
    return f"ssh://git@ssh.github.com:443/{path}"


def _locate_ssh_private_key() -> str:
    """定位 SSH 私钥：优先系统 ~/.ssh（标准、安全），其次环境变量 GITHUB_SSH_KEY。"""
    home_ssh = Path.home() / ".ssh"
    for cand in (home_ssh / "id_ed25519", home_ssh / "id_rsa", home_ssh / "id_ecdsa"):
        if os.path.exists(cand):
            return str(cand)
    p = os.getenv("GITHUB_SSH_KEY", "").strip()
    if p and os.path.exists(p):
        return p
    return ""


def _ssh_clone_command() -> str:
    """构造 ssh 备用通道的 core.sshCommand，自动带上本地私钥"""
    sc = "ssh -o StrictHostKeyChecking=accept-new"
    key = _locate_ssh_private_key()
    if key:
        sc += f' -i "{key}" -o IdentitiesOnly=yes'
    return sc


# ---------- 探测项目内容 ----------

async def probe_project(author: str, repo: str) -> dict:
    """探测仓库可下载的内容：默认分支、zip链接、README、release、clone链接"""
    info = {
        "author": author,
        "repository": repo,
        "default_branch": "main",
        "zip_url": build_zip_url(author, repo),
        "has_readme": False,
        "readme_url": "",
        "has_release": False,
        "releases": [],
        "clone_url": build_clone_url(author, repo),
        "github_url": f"https://github.com/{author}/{repo}",
    }

    try:
        from app.services.github_service import fetch_repository
        repo_info = await fetch_repository(author, repo)
        branch = repo_info.get("default_branch", "main")
        info["default_branch"] = branch
        info["zip_url"] = build_zip_url(author, repo, branch)
        info["clone_url"] = build_clone_url(author, repo)
    except Exception as e:
        logger.warning(f"探测仓库失败 {author}/{repo}: {e}")

    # 检查 README
    readme_url = build_readme_url(author, repo, info["default_branch"])
    try:
        async with httpx.AsyncClient(timeout=10, verify=GITHUB_VERIFY_SSL, follow_redirects=True) as client:
            r = await client.get(readme_url)
            if r.status_code == 200:
                info["has_readme"] = True
                info["readme_url"] = readme_url
    except Exception:
        pass

    # 检查最新 release
    try:
        url = f"{GITHUB_API_BASE_URL}/repos/{author}/{repo}/releases/latest"
        headers = _get_headers(url)
        headers["Accept"] = "application/vnd.github.v3+json"
        async with httpx.AsyncClient(timeout=15, verify=GITHUB_VERIFY_SSL, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                assets = data.get("assets", [])
                info["has_release"] = True
                info["releases"] = [
                    {
                        "tag": data.get("tag_name", ""),
                        "name": a.get("name", ""),
                        "size": a.get("size", 0),
                        "browser_download_url": a.get("browser_download_url", ""),
                        "content_type": a.get("content_type", ""),
                    }
                    for a in assets
                ]
    except Exception as e:
        logger.warning(f"探测 release 失败 {author}/{repo}: {e}")

    return info


# ---------- 流式下载实现 ----------

async def download_file(task: DownloadTask):
    """流式下载文件到磁盘，实时更新进度（approximation ABDownloadManager）"""
    task_id = task.id
    url = task.url

    # 规范化 URL：github.com 的产物/archive 链接转成可直连的 codeload 直链
    url = _normalize_download_url(url)
    # 安全校验，仅允许 GitHub 相关域名
    _sanitize_url(url)
    if url != task.url:
        _update_task(task_id, url=url)

    save_dir = _resolve_save_dir(task.save_dir)
    filename = task.filename or _safe_filename(task.repository + ".zip")

    _update_task(task_id, status="downloading", filename=filename)

    dest = save_dir / filename
    try:
        # Accept-Encoding: identity 禁用传输层压缩，保证读到的字节数与 content-length 一致，
        # 否则 httpx 自动解压会导致 downloaded > total_size、进度超过 100%
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=30.0), verify=GITHUB_VERIFY_SSL, follow_redirects=True) as client:
            async with client.stream(
                "GET", url,
                headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"},
            ) as resp:
                if resp.status_code != 200:
                    raise RuntimeError(f"下载失败: HTTP {resp.status_code}")
                total = int(resp.headers.get("content-length", 0)) or 0
                _update_task(task_id, total_size=total)

                downloaded = 0
                last_time = asyncio.get_event_loop().time()
                last_bytes = 0
                speed = 0.0

                with open(dest, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        f.write(chunk)
                        downloaded += len(chunk)

                        now = asyncio.get_event_loop().time()
                        if now - last_time >= 1.0:
                            speed = (downloaded - last_bytes) / (now - last_time)
                            last_time = now
                            last_bytes = downloaded

                        # 每约 256KB 更新一次进度，降低写库频率
                        if downloaded % (256 * 1024) < 65536:
                            _update_task(
                                task_id,
                                downloaded=downloaded,
                                speed=speed,
                            )

                _update_task(task_id, downloaded=downloaded, speed=0, status="completed",
                             finished_at=datetime.utcnow())
                logger.success(f"下载完成: {filename}, 大小: {downloaded} bytes")
    except Exception as e:
        # 任务被取消则不改状态为 failed
        current = _get_task_status(task_id)
        if current == "cancelled":
            logger.info(f"任务 {task_id} 已取消，跳过")
            try:
                if dest.exists():
                    dest.unlink()
            except Exception:
                pass
            return
        logger.error(f"下载失败 {filename}: {e}")
        _update_task(task_id, status="failed", error=str(e)[:500],
                     finished_at=datetime.utcnow())


def _get_task_status(task_id: int) -> str:
    db = SessionLocal()
    try:
        task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
        return task.status if task else ""
    finally:
        db.close()


async def clone_repo(task: DownloadTask):
    """git clone 拉取完整仓库（保留 git 历史），直连失败时自动回退镜像源"""
    import shutil

    task_id = task.id
    save_dir = _resolve_save_dir(task.save_dir)
    repo_dir = save_dir / _safe_filename(task.repository)

    _update_task(task_id, status="downloading", filename=task.repository, total_size=0)

    def cleanup_partial():
        # clone 失败会残留目录，先删掉以便回退重试
        try:
            if repo_dir.exists():
                shutil.rmtree(repo_dir, ignore_errors=True)
        except Exception:
            pass

    if is_direct_github_url(task.url):
        candidates = [task.url] + [apply_mirror(task.url, m) for m in load_clone_mirrors()]
    else:
        # task.url 已经是镜像/其他地址，直接使用
        candidates = [task.url]
    # github.com 的 443/HTTPS 被干扰时，回退官方备用通道 ssh.github.com:443（需已配 SSH key）
    ssh_url = _build_ssh443_url(task.url)
    if ssh_url:
        candidates.append(ssh_url)
    seen, ordered = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    candidates = ordered

    def run_clone():
        errors = []
        for idx, clone_url in enumerate(candidates, 1):
            cleanup_partial()
            if clone_url != task.url:
                _update_task(task_id, url=clone_url)
            logger.info(f"git clone 尝试 {idx}/{len(candidates)}: {clone_url}")
            if clone_url.startswith("ssh://"):
                # ssh.github.com:443 官方备用通道，首次连接自动接受 host key，避免交互卡死
                cmd = ["git", "-c", f"core.sshCommand={_ssh_clone_command()}",
                       "clone", "--progress", clone_url, str(repo_dir)]
            else:
                cmd = ["git", "clone", "--progress", clone_url, str(repo_dir)]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            _update_task(task_id, status="downloading", proc_id=str(proc.pid))
            procs[task_id] = proc
            try:
                _, err = proc.communicate(timeout=None)
            finally:
                procs.pop(task_id, None)
            if proc.returncode == 0:
                _update_task(task_id, status="completed", error="",
                             finished_at=datetime.utcnow())
                logger.success(f"clone 完成: {task.repository}")
                return
            errors.append(f"[{clone_url}] {(err or 'git clone 失败').strip()[:300]}")
        cleanup_partial()
        _update_task(task_id, status="failed", error="; ".join(errors)[:500],
                     finished_at=datetime.utcnow())

    await asyncio.get_event_loop().run_in_executor(None, run_clone)


# 进行中的 git 进程（用于取消）
procs: dict = {}