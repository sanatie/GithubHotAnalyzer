from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.favorite import Favorite
from app.models.repository import Repository
from app.models.report import Report
from app.schemas.favorite import FavoriteBatchCreate, FavoriteCreate, FavoriteUpdate
from app.services.repository_service import (
    get_repository_by_full_name,
    get_repository_by_id,
)

router = APIRouter()


@router.get("")
def get_favorites(
    page: int = 1,
    page_size: int = 20,
    tag: Optional[str] = Query(None, description="按标签过滤（匹配收藏里任一标签）"),
    db: Session = Depends(get_db),
):
    """
    Get favorites list

    - **page**: Page number
    - **page_size**: Items per page
    - **tag**: Optional tag to filter by
    """
    skip = (page - 1) * page_size
    query = db.query(Favorite).order_by(Favorite.created_at.desc())
    if tag and tag.strip():
        # tags 为逗号分隔串，用分隔符包围匹配单个标签，避免 "ai" 误配 "daily"
        query = query.filter(Favorite.tags.contains(f",{tag.strip()}")
                             | Favorite.tags.startswith(f"{tag.strip()},")
                             | (Favorite.tags == tag.strip()))
    total = query.count()
    items = query.offset(skip).limit(page_size).all()

    result = []
    for fav in items:
        repo = db.query(Repository).filter(Repository.id == fav.repo_id).first()
        latest_report = db.query(Report).filter(
            Report.repo_full_name == fav.repo_full_name
        ).order_by(Report.created_at.desc()).first()
        avatar_url = f"https://github.com/{repo.owner}.png" if repo and repo.owner else ""
        item = {
            "id": fav.id,
            "repo_id": fav.repo_id,
            "repo_full_name": fav.repo_full_name,
            "note": fav.note,
            "tags": fav.tags or "",
            "created_at": fav.created_at,
            "report_id": latest_report.id if latest_report else None,
            "overall_score": latest_report.overall_score if latest_report else None,
            "repository": {
                "name": repo.name if repo else "",
                "description": repo.description if repo else "",
                "language": repo.language if repo else "",
                "stargazers_count": repo.stargazers_count if repo else 0,
                "html_url": repo.html_url if repo else "",
                "avatar_url": avatar_url,
            } if repo else None,
        }
        result.append(item)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": result,
    }


@router.post("")
def add_favorite(fav_data: FavoriteCreate, db: Session = Depends(get_db)):
    """
    Add a favorite

    - **repo_id**: Repository ID
    - **repo_full_name**: Repository full name
    - **note**: Note (optional)
    """
    repo = get_repository_by_id(db, fav_data.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    existing = db.query(Favorite).filter(Favorite.repo_id == fav_data.repo_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Repository already favorited")

    db_fav = Favorite(
        repo_id=fav_data.repo_id,
        repo_full_name=fav_data.repo_full_name,
        note=fav_data.note,
        tags=fav_data.tags or "",
    )
    db.add(db_fav)
    db.commit()
    db.refresh(db_fav)
    return db_fav


@router.post("/batch")
def add_favorites_batch(payload: FavoriteBatchCreate, db: Session = Depends(get_db)):
    """
    Batch add favorites（兼容购物车/推荐数据结构）

    - **items**: 待收藏的仓库列表（author/name 或 repository_id）
    自动为未入库仓库建档；已收藏的自动跳过。
    """
    success, already, failed = [], [], []
    for item in payload.items:
        full_name = (item.repo_full_name or "").strip() or \
            (f"{item.author}/{item.name}".strip("/") if item.author and item.name else "")

        if not full_name and not item.repository_id:
            failed.append({"full_name": full_name or item.name, "reason": "缺少仓库标识"})
            continue

        # 1) 找到或创建 Repository（收藏列表依赖 join，仓库行必须存在）
        repo = get_repository_by_id(db, item.repository_id) if item.repository_id else None
        if not repo:
            repo = get_repository_by_full_name(db, full_name) if full_name else None
        if not repo:
            repo = Repository(
                full_name=full_name,
                name=item.name,
                owner=item.author,
                description=item.description,
                html_url=item.html_url,
                language=item.language,
                stargazers_count=item.stargazers_count,
                forks_count=item.forks_count,
            )
            db.add(repo)
            try:
                db.commit()
                db.refresh(repo)
            except IntegrityError:
                db.rollback()
                repo = get_repository_by_full_name(db, full_name)

        # 2) 去重：同一仓库只收藏一次
        if db.query(Favorite).filter(Favorite.repo_id == repo.id).first():
            already.append(repo.full_name)
            continue

        # 3) 写收藏
        tags_str = ",".join(filter(None, item.tags))
        fav = Favorite(
            repo_id=repo.id,
            repo_full_name=repo.full_name,
            note=item.note or "",
            tags=tags_str,
        )
        db.add(fav)
        try:
            db.commit()
            success.append(repo.full_name)
        except IntegrityError:
            db.rollback()
            failed.append({"full_name": repo.full_name, "reason": "写入冲突"})

    return {
        "success": success,
        "already_exists": already,
        "failed": failed,
        "success_count": len(success),
        "already_count": len(already),
        "failed_count": len(failed),
    }


@router.delete("/{fav_id}")
def delete_favorite(fav_id: int, db: Session = Depends(get_db)):
    """
    Remove a favorite

    - **fav_id**: Favorite record ID
    """
    fav = db.query(Favorite).filter(Favorite.id == fav_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(fav)
    db.commit()
    return {"message": "Favorite removed successfully"}


@router.put("/{fav_id}")
def update_favorite(fav_id: int, fav_data: FavoriteUpdate, db: Session = Depends(get_db)):
    """
    Update favorite note / tags

    - **fav_id**: Favorite record ID
    - **note**: Note content
    - **tags**: Tags, comma separated
    """
    fav = db.query(Favorite).filter(Favorite.id == fav_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    # 仅当字段显式传入时才更新，避免用 None 覆盖已有值
    if fav_data.note is not None:
        fav.note = fav_data.note
    if fav_data.tags is not None:
        fav.tags = fav_data.tags
    db.commit()
    db.refresh(fav)
    return fav


@router.get("/check/{repo_id}")
def check_favorite(repo_id: int, db: Session = Depends(get_db)):
    """
    Check if a repository is already favorited

    - **repo_id**: Repository ID
    """
    fav = db.query(Favorite).filter(Favorite.repo_id == repo_id).first()
    return {
        "is_favorited": fav is not None,
        "favorite_id": fav.id if fav else None,
    }