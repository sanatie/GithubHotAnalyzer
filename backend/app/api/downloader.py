import asyncio
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.models.download_task import DownloadTask
from app.schemas.downloader import (
    DownloadCreate,
    DownloadTaskOut,
    DownloadTaskListResponse,
    ProjectContentInfo,
)
from app.services import downloader_service as ds

router = APIRouter()


def _remove_artifact(task: DownloadTask, force_files: bool = False):
    """删除任务落地文件/目录，避免残留。

    gitclone 落地为目录（save_dir/repository），无论任务状态都清理残留；
    文件类型仅删除已完成任务（除非 force_files，用于取消时清半成品）。
    """
    if task.content_type == "gitclone":
        for sub in (task.repository, task.filename):
            if not sub:
                continue
            path = Path(task.save_dir) / ds._safe_filename(sub)
            try:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                elif path.exists():
                    path.unlink()
            except Exception:
                pass
        return
    if not task.filename:
        return
    if task.status != "completed" and not force_files:
        return
    try:
        path = Path(task.save_dir) / task.filename
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()
    except Exception:
        pass


def _to_out(task: DownloadTask) -> DownloadTaskOut:
    total = task.total_size or 0
    downloaded = task.downloaded or 0
    if total > 0:
        progress = min(100.0, round((downloaded / total) * 100, 1))
    else:
        # 无法获取总大小（如 raw README 无 content-length）：完成则显示100%
        progress = 100.0 if task.status == "completed" else 0.0
    return DownloadTaskOut(
        id=task.id,
        author=task.author,
        repository=task.repository,
        content_type=task.content_type,
        save_dir=task.save_dir,
        url=task.url,
        filename=task.filename or "",
        total_size=total,
        downloaded=downloaded,
        progress=progress,
        speed=task.speed or 0,
        status=task.status,
        error=task.error or "",
    )


@router.get("/probe/{author}/{repository:path}", response_model=ProjectContentInfo)
async def probe_project(author: str, repository: str):
    """探测项目可下载内容（默认分支/zip/readme/release/clone）"""
    repo = repository.split(":path")[0] if ":path" in repository else repository
    logger.info(f"探测项目内容: {author}/{repo}")
    try:
        return await ds.probe_project(author, repo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"探测失败: {e}")


@router.post("", response_model=DownloadTaskOut)
async def create_download(request: DownloadCreate, db: Session = Depends(get_db)):
    """创建下载任务，立即异步执行"""
    save_dir = ds.get_default_download_dir() if not request.save_dir.strip() else request.save_dir.strip()
    content_type = request.content_type.strip().lower()

    if content_type not in ("zip", "release", "readme", "gitclone"):
        raise HTTPException(status_code=400, detail="content_type 必须为 zip/release/readme/gitclone")

    url = request.url.strip()
    if content_type == "gitclone":
        if not url:
            # 仅给仓库名时自动补全为 github clone 地址
            url = ds.build_clone_url(request.author.strip(), request.repository.strip())
        # 应用镜像源：优先请求中填写的 mirror，其次全局 GITHUB_CLONE_MIRROR
        mirror = request.mirror.strip() or os.getenv("GITHUB_CLONE_MIRROR", "")
        if mirror:
            url = ds.apply_mirror(url, mirror)
    else:
        if not url:
            raise HTTPException(status_code=400, detail="缺少下载 URL")

    task = DownloadTask(
        author=request.author.strip(),
        repository=request.repository.strip(),
        content_type=content_type,
        save_dir=save_dir,
        url=url,
        filename=request.filename.strip(),
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 异步启动下载
    asyncio.create_task(_run_task(task.id, content_type))

    return _to_out(task)


async def _run_task(task_id: int, content_type: str):
    from app.database import SessionLocal
    db = SessionLocal()
    task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
    db.close()
    if not task:
        return
    if content_type == "gitclone":
        await ds.clone_repo(task)
    else:
        await ds.download_file(task)


@router.get("", response_model=DownloadTaskListResponse)
async def list_tasks(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    """获取下载任务列表（按创建时间倒序）"""
    query = db.query(DownloadTask).order_by(DownloadTask.created_at.desc())
    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()
    return DownloadTaskListResponse(
        items=[_to_out(t) for t in tasks],
        total=total,
    )


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: int, db: Session = Depends(get_db)):
    """取消下载任务"""
    task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status in ("pending", "downloading"):
        task.status = "cancelled"
        task.finished_at = datetime.utcnow()
        db.commit()

        # 终止 git clone 进程
        proc_id = task.proc_id or ""
        if proc_id and proc_id.isdigit():
            try:
                subprocess.run(["taskkill", "/F", "/PID", proc_id], capture_output=True)
            except Exception:
                pass

        # 删除已产生的文件/目录残留
        _remove_artifact(task, force_files=True)

    return {"status": "cancelled"}


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务记录（同时尝试删除文件）"""
    task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 删除落地文件/目录（gitclone 无论状态都清理；文件类型仅清理已完成）
    _remove_artifact(task)

    db.delete(task)
    db.commit()
    return {"status": "deleted"}


@router.post("/{task_id}/open-dir")
async def open_dir(task_id: int, db: Session = Depends(get_db)):
    """打开任务文件所在目录"""
    task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    path = Path(task.save_dir)
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.startfile(str(path))  # noqa: S606
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法打开目录: {e}")
    return {"status": "opened"}


@router.get("/default-dir")
async def get_default_dir():
    """获取默认下载目录"""
    return {"default_dir": ds.get_default_download_dir()}