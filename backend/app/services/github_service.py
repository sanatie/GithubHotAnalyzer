import base64
import re
from typing import Dict, List, Optional

import httpx
from loguru import logger

from app.config import GITHUB_API_BASE_URL, GITHUB_TOKEN


# 请求超时配置
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3


def parse_repo_url(repo_url: str) -> tuple:
    """
    从 GitHub 仓库 URL 中解析出 owner 和 repo 名称

    参数:
        repo_url: GitHub 仓库地址，支持多种格式
            - https://github.com/owner/repo
            - https://github.com/owner/repo.git
            - github.com/owner/repo
            - owner/repo

    返回:
        (owner, repo) 元组

    异常:
        ValueError: URL 格式不正确时抛出
    """
    # 去除末尾的 .git 和斜杠
    repo_url = repo_url.strip().rstrip("/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    # 匹配 owner/repo 格式
    pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, repo_url)
    if match:
        return match.group(1), match.group(2)

    # 直接是 owner/repo 格式
    if "/" in repo_url and not repo_url.startswith("http"):
        parts = repo_url.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]

    raise ValueError(f"无法解析仓库地址: {repo_url}，请输入正确的 GitHub 仓库 URL")


def _get_headers() -> Dict[str, str]:
    """构造 GitHub API 请求头"""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Analyzer",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


async def _request_with_retry(url: str, method: str = "GET", **kwargs) -> httpx.Response:
    """
    带重试机制的 HTTP 请求

    参数:
        url: 请求 URL
        method: 请求方法
        **kwargs: 其他请求参数

    返回:
        httpx.Response 对象
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, verify=False, follow_redirects=True) as client:
                response = await client.request(method, url, **kwargs)
                # GitHub API 限流时返回 403
                if response.status_code == 403:
                    logger.warning(f"GitHub API 限流，尝试次数: {attempt + 1}/{MAX_RETRIES}")
                    continue
                response.raise_for_status()
                return response
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            last_error = e
            logger.warning(f"请求失败，尝试次数: {attempt + 1}/{MAX_RETRIES}，错误: {e}")
            continue

    raise last_error or Exception(f"请求失败，已重试 {MAX_RETRIES} 次")


async def fetch_repository(owner: str, repo: str) -> Dict:
    """
    获取仓库基本信息

    参数:
        owner: 仓库所有者
        repo: 仓库名称

    返回:
        仓库信息字典
    """
    url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}"
    logger.info(f"获取仓库信息: {owner}/{repo}")

    response = await _request_with_retry(url, headers=_get_headers())
    result = response.json()
    logger.debug(f"仓库信息获取成功: {owner}/{repo}, stars: {result.get('stargazers_count', 0)}")
    return result


async def fetch_readme(owner: str, repo: str) -> str:
    """
    获取仓库 README 内容

    参数:
        owner: 仓库所有者
        repo: 仓库名称

    返回:
        README 文本内容（解码后）
    """
    url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/readme"
    logger.info(f"获取 README: {owner}/{repo}")

    try:
        response = await _request_with_retry(url, headers=_get_headers())
        data = response.json()
        # README 内容是 base64 编码的
        content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        logger.debug(f"README 获取成功，长度: {len(content)} 字符")
        return content
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"README 不存在: {owner}/{repo}")
            return ""
        raise


async def fetch_trending_repos(
    language: Optional[str] = None,
    since: str = "daily",
    limit: int = 25
) -> List[Dict]:
    """
    获取 GitHub 热榜项目

    注意：GitHub 官方没有 trending API，这里使用搜索 API 模拟热门项目
    实际项目中建议使用第三方 trending API 或爬虫

    参数:
        language: 编程语言筛选
        since: 时间范围（daily, weekly, monthly）
        limit: 返回数量

    返回:
        热门仓库列表
    """
    # 构造搜索查询：按 star 数排序的热门项目
    query = "stars:>100"
    if language:
        query += f" language:{language}"

    logger.info(f"获取热榜项目: language={language}, since={since}, limit={limit}")

    url = f"{GITHUB_API_BASE_URL}/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }
    response = await _request_with_retry(url, headers=_get_headers(), params=params)
    data = response.json()
    items = data.get("items", [])
    logger.debug(f"获取到 {len(items)} 个热榜项目")
    return items


async def fetch_file_tree(owner: str, repo: str, branch: str = None) -> List[Dict]:
    """
    获取仓库文件树

    参数:
        owner: 仓库所有者
        repo: 仓库名称
        branch: 分支名，默认为默认分支

    返回:
        文件列表，每项包含 path、type、size
    """
    # 未指定分支时先获取默认分支
    if not branch:
        repo_info = await fetch_repository(owner, repo)
        branch = repo_info.get("default_branch", "main")

    url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    logger.info(f"获取文件树: {owner}/{repo}, branch={branch}")

    try:
        response = await _request_with_retry(url, headers=_get_headers())
        data = response.json()
        tree = data.get("tree", [])
        logger.debug(f"文件树获取成功，共 {len(tree)} 个节点")
        return tree
    except Exception as e:
        logger.warning(f"获取文件树失败: {e}")
        return []


# 安全检测需要关注的关键文件模式
SECURITY_KEY_FILES = [
    "package.json", "requirements.txt", "setup.py", "Pipfile", "pyproject.toml",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", ".env",
]
SECURITY_KEY_EXTENSIONS = [".sh", ".bat", ".ps1", ".vbs"]
SECURITY_KEY_PATHS = [".github/workflows/", "scripts/", "install"]


def _is_security_relevant_file(filepath: str) -> bool:
    """判断文件是否与安全检测相关"""
    lower = filepath.lower()
    basename = lower.split("/")[-1]

    # 匹配关键文件名
    if basename in SECURITY_KEY_FILES:
        return True
    # 匹配关键扩展名
    for ext in SECURITY_KEY_EXTENSIONS:
        if lower.endswith(ext):
            return True
    # 匹配关键路径
    for key_path in SECURITY_KEY_PATHS:
        if key_path in lower:
            return True
    # CI/CD 配置
    if lower.startswith(".github/") and lower.endswith((".yml", ".yaml")):
        return True
    return False


async def fetch_file_content(owner: str, repo: str, filepath: str, ref: str = None) -> str:
    """
    获取仓库中单个文件的内容

    参数:
        owner: 仓库所有者
        repo: 仓库名称
        filepath: 文件路径
        ref: 分支或 commit

    返回:
        文件文本内容（解码后），失败时返回空字符串
    """
    url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/contents/{filepath}"
    params = {}
    if ref:
        params["ref"] = ref

    try:
        response = await _request_with_retry(url, headers=_get_headers(), params=params)
        data = response.json()
        if data.get("encoding") == "base64" and data.get("content"):
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            return content
        return ""
    except Exception as e:
        logger.debug(f"获取文件内容失败: {filepath}, {e}")
        return ""


async def fetch_security_relevant_files(owner: str, repo: str) -> Dict[str, str]:
    """
    获取仓库中与安全检测相关的文件内容

    参数:
        owner: 仓库所有者
        repo: 仓库名称

    返回:
        {文件路径: 文件内容} 字典，总内容不超过限制
    """
    MAX_FILES = 10
    MAX_FILE_CHARS = 2000
    MAX_TOTAL_CHARS = 8000

    tree = await fetch_file_tree(owner, repo)
    if not tree:
        return {}

    # 筛选关键文件
    relevant_files = [
        item for item in tree
        if item.get("type") == "blob" and _is_security_relevant_file(item.get("path", ""))
    ]

    logger.info(f"筛选出 {len(relevant_files)} 个安全相关文件")

    result = {}
    total_chars = 0

    for item in relevant_files[:MAX_FILES]:
        filepath = item["path"]
        content = await fetch_file_content(owner, repo, filepath)

        if not content:
            continue

        # 截断过长的文件
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS] + "\n...（内容已截断）"

        result[filepath] = content
        total_chars += len(content)

        if total_chars >= MAX_TOTAL_CHARS:
            break

    logger.info(f"成功获取 {len(result)} 个文件内容，总字符数: {total_chars}")
    return result


async def search_repositories(
    keyword: str,
    language: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> Dict:
    """
    搜索 GitHub 仓库

    参数:
        keyword: 搜索关键词
        language: 编程语言筛选
        page: 页码
        per_page: 每页数量

    返回:
        搜索结果字典（包含 total_count 和 items）
    """
    query = keyword
    if language:
        query += f" language:{language}"

    logger.info(f"搜索仓库: keyword={keyword}, language={language}, page={page}")

    url = f"{GITHUB_API_BASE_URL}/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "page": page,
        "per_page": per_page,
    }
    response = await _request_with_retry(url, headers=_get_headers(), params=params)
    result = response.json()
    logger.debug(f"搜索到 {result.get('total_count', 0)} 个结果")
    return result
