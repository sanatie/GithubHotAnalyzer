from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.favorite import Favorite
from app.models.repository import Repository
from app.models.report import Report
from app.schemas.favorite import FavoriteCreate, FavoriteUpdate
from app.services.repository_service import get_repository_by_id

router = APIRouter()


@router.get("")
def get_favorites(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """
    Get favorites list

    - **page**: Page number
    - **page_size**: Items per page
    """
    skip = (page - 1) * page_size
    query = db.query(Favorite).order_by(Favorite.created_at.desc())
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
    )
    db.add(db_fav)
    db.commit()
    db.refresh(db_fav)
    return db_fav


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
    Update favorite note

    - **fav_id**: Favorite record ID
    - **note**: Note content
    """
    fav = db.query(Favorite).filter(Favorite.id == fav_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    fav.note = fav_data.note
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