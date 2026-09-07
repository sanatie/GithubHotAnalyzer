from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger
import httpx

from app.database import get_db
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, ScoreBreakdown
from app.schemas.report import ReportListResponse
from app.services.github_service import parse_repo_url, fetch_repository, fetch_readme, fetch_security_relevant_files
from app.services.ai_service import analyze_repository, analyze_security
from app.services.report_service import (
    save_report,
    get_latest_report,
    get_report_by_id,
    get_report_history,
    parse_report_content,
    delete_report,
    delete_reports_batch,
    delete_all_reports,
)
from app.services.repository_service import upsert_repository

router = APIRouter()


class BatchDeleteRequest(BaseModel):
    report_ids: list[int]


@router.post("/repositories", response_model=AnalyzeResponse)
async def analyze_repo(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyze a GitHub repository and generate a Chinese analysis report

    - **repo_url**: GitHub repository URL
    - **force_refresh**: Whether to force re-analysis (ignore cache)
    """
    # 1. Parse repository URL
    try:
        owner, repo = parse_repo_url(request.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    full_name = f"{owner}/{repo}"

    # 2. Check cache if not forced refresh
    if not request.force_refresh:
        cached_report = get_latest_report(db, full_name)
        if cached_report:
            result = parse_report_content(cached_report)
            score_breakdown_data = result.get("score_breakdown", {})
            score_breakdown = ScoreBreakdown(
                popularity=score_breakdown_data.get("popularity", 0),
                code_quality=score_breakdown_data.get("code_quality", 0),
                documentation=score_breakdown_data.get("documentation", 0),
                activity=score_breakdown_data.get("activity", 0),
            ) if score_breakdown_data else None

            repo_info = {}
            if cached_report.repository:
                repo = cached_report.repository
                repo_info = {
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "watchers_count": repo.watchers_count,
                    "open_issues_count": repo.open_issues_count,
                    "language": repo.language,
                    "license": repo.license,
                    "default_branch": repo.default_branch,
                    "created_at": repo.created_at,
                    "updated_at": repo.updated_at,
                    "homepage": repo.html_url,
                }

            return AnalyzeResponse(
                repo_full_name=full_name,
                overall_score=result.get("overall_score", 0),
                summary=result.get("summary", ""),
                tech_stack=result.get("tech_stack", []),
                highlights=result.get("highlights", []),
                learning_advice=result.get("learning_advice", ""),
                score_breakdown=score_breakdown,
                suitable_for=result.get("suitable_for"),
                report_id=cached_report.id,
                repository=repo_info,
            )

    # 3. Fetch repository info and README from GitHub API
    try:
        repo_info = await fetch_repository(owner, repo)
        readme_content = await fetch_readme(owner, repo)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"GitHub 上未找到仓库 {full_name}，请检查仓库名是否正确")
        raise HTTPException(status_code=502, detail=f"Failed to fetch repository info: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch repository info: {str(e)}")

    # 4. Save or update repository in local database
    db_repo = upsert_repository(db, repo_info)

    # 5. Analyze with AI
    try:
        analysis_result = await analyze_repository(repo_info, readme_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    # 6. Save analysis report
    db_report = save_report(db, db_repo.id, full_name, analysis_result)

    # 7. Build score breakdown
    score_breakdown_data = analysis_result.get("score_breakdown", {})
    score_breakdown = ScoreBreakdown(
        popularity=score_breakdown_data.get("popularity", 0),
        code_quality=score_breakdown_data.get("code_quality", 0),
        documentation=score_breakdown_data.get("documentation", 0),
        activity=score_breakdown_data.get("activity", 0),
    ) if score_breakdown_data else None

    # 8. Return result
    repo_data = {
        "stargazers_count": db_repo.stargazers_count,
        "forks_count": db_repo.forks_count,
        "watchers_count": db_repo.watchers_count,
        "open_issues_count": db_repo.open_issues_count,
        "language": db_repo.language,
        "license": db_repo.license,
        "default_branch": db_repo.default_branch,
        "created_at": db_repo.created_at,
        "updated_at": db_repo.updated_at,
        "homepage": db_repo.html_url,
    }

    return AnalyzeResponse(
        repo_full_name=full_name,
        overall_score=analysis_result.get("overall_score", 0),
        summary=analysis_result.get("summary", ""),
        tech_stack=analysis_result.get("tech_stack", []),
        highlights=analysis_result.get("highlights", []),
        learning_advice=analysis_result.get("learning_advice", ""),
        score_breakdown=score_breakdown,
        suitable_for=analysis_result.get("suitable_for"),
        report_id=db_report.id,
        repository=repo_data,
    )


@router.get("/reports")
def get_analysis_history(
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
    db: Session = Depends(get_db),
):
    """
    Get analysis report history list

    - **page**: Page number
    - **page_size**: Items per page
    - **keyword**: Search keyword (repository name)
    """
    skip = (page - 1) * page_size
    total, items = get_report_history(db, skip=skip, limit=page_size, keyword=keyword)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    item_list = []
    for r in items:
        content = parse_report_content(r) or {}
        item_list.append({
            "id": r.id,
            "repo_id": r.repo_id,
            "repo_full_name": r.repo_full_name,
            "overall_score": r.overall_score,
            "language": r.repository.language if r.repository else None,
            "stars": r.repository.stargazers_count if r.repository else 0,
            "forks": r.repository.forks_count if r.repository else 0,
            "watchers": r.repository.watchers_count if r.repository else 0,
            "open_issues": r.repository.open_issues_count if r.repository else 0,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.created_at.isoformat() if r.created_at else None,
            "summary": content.get("summary", ""),
            "content": content,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "items": item_list,
    }


@router.delete("/reports/{report_id}")
def delete_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    """
    Delete an analysis report

    - **report_id**: Report ID
    """
    success = delete_report(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Deleted successfully", "report_id": report_id}


@router.post("/reports/batch-delete")
def delete_reports_batch_endpoint(
    body: BatchDeleteRequest,
    db: Session = Depends(get_db),
):
    """
    Batch delete analysis reports

    Request body: {"report_ids": [1, 2, 3]}
    """
    report_ids = body.report_ids
    if not report_ids:
        raise HTTPException(status_code=400, detail="Please select reports to delete")
    count = delete_reports_batch(db, report_ids)
    return {"message": f"Deleted {count} reports", "count": count}


@router.delete("/reports")
def delete_all_reports_endpoint(db: Session = Depends(get_db)):
    """
    Delete all analysis reports (clear all)
    """
    count = delete_all_reports(db)
    return {"message": f"Deleted all {count} reports", "count": count}


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    """
    Get analysis report detail by ID

    - **report_id**: Report ID
    """
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content = parse_report_content(report)

    repo_info = {}
    if report.repository:
        repo = report.repository
        repo_info = {
            "language": repo.language,
            "stargazers_count": repo.stargazers_count,
            "forks_count": repo.forks_count,
            "watchers_count": repo.watchers_count,
            "open_issues_count": repo.open_issues_count,
            "license": repo.license,
            "default_branch": repo.default_branch,
            "created_at": repo.created_at,
            "updated_at": repo.updated_at,
            "homepage": repo.html_url,
        }

    return {
        "id": report.id,
        "repo_id": report.repo_id,
        "repo_full_name": report.repo_full_name,
        "overall_score": report.overall_score,
        "content": content,
        "repository": repo_info,
        "created_at": report.created_at,
    }


@router.post("/security-scan/{report_id}")
async def security_check(report_id: int, db: Session = Depends(get_db)):
    """
    Perform security risk scan on an analyzed repository

    - **report_id**: Report ID

    Scans for: malicious code, suspicious network requests, dangerous permissions, dependency risks, install script risks, obfuscated code
    """
    import json

    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    full_name = report.repo_full_name
    parts = full_name.split("/")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid repository name format")
    owner, repo = parts

    try:
        repo_info = await fetch_repository(owner, repo)
        file_contents = await fetch_security_relevant_files(owner, repo)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch repository files: {str(e)}")

    try:
        security_result = await analyze_security(repo_info, file_contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security scan failed: {str(e)}")

    content = parse_report_content(report)
    content["security"] = security_result
    report.content = json.dumps(content, ensure_ascii=False)
    db.commit()

    logger.info(f"Security scan completed and saved: report_id={report_id}")

    return {
        "report_id": report_id,
        "security": security_result,
    }