from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.repository import RepositoryListResponse
from app.services.repository_service import (
    get_repository_by_id,
    get_repository_by_full_name,
    list_repositories,
    enrich_repo_with_topics,
)
from app.services.github_service import search_repositories

router = APIRouter()


@router.get("", response_model=RepositoryListResponse)
def get_repositories(
    keyword: str = Query("", description="Search keyword"),
    language: str = Query("", description="Programming language filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Paginated query of local repository list

    - **keyword**: Search keyword (matches name or description)
    - **language**: Programming language filter
    - **page**: Page number
    - **page_size**: Items per page
    """
    skip = (page - 1) * page_size
    total, items = list_repositories(db, keyword=keyword, language=language, skip=skip, limit=page_size)

    enriched_items = [enrich_repo_with_topics(item) for item in items]

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return RepositoryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=enriched_items,
    )


@router.get("/{repo_id}")
def get_repository(repo_id: int, db: Session = Depends(get_db)):
    """
    Get repository detail by ID

    - **repo_id**: Repository ID
    """
    repo = get_repository_by_id(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return enrich_repo_with_topics(repo)


@router.get("/by-name/{full_name:path}")
def get_repository_by_name(full_name: str, db: Session = Depends(get_db)):
    """
    Get repository detail by full name (owner/repo)

    - **full_name**: Repository full name, e.g. tiangolo/fastapi
    """
    repo = get_repository_by_full_name(db, full_name)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return enrich_repo_with_topics(repo)


@router.get("/search")
async def search_github_repos(
    q: str = Query(..., description="Search keyword"),
    language: Optional[str] = Query(None, description="Programming language filter"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Search repositories from GitHub (real-time GitHub API call)

    - **q**: Search keyword
    - **language**: Programming language filter
    - **page**: Page number
    - **per_page**: Items per page
    """
    try:
        result = await search_repositories(q, language=language, page=page, per_page=per_page)
        return {
            "total": result.get("total_count", 0),
            "items": result.get("items", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub search failed: {str(e)}")