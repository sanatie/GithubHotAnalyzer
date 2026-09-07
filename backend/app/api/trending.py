from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.schemas.trending import TrendingItem, TrendingResponse
from app.services.github_service import _get_headers, _request_with_retry
from app.config import GITHUB_API_BASE_URL

router = APIRouter()


@router.get("", response_model=TrendingResponse)
async def get_trending(
    language: Optional[str] = Query(None, description="编程语言筛选，如 python、javascript"),
    since: str = Query("weekly", description="时间范围（daily/weekly/monthly）"),
    limit: int = Query(20, ge=1, le=50, description="返回数量，最多50"),
):
    """
    获取 GitHub 热门项目排行榜

    - **language**: 编程语言筛选（可选）
    - **since**: 时间范围，默认 weekly
    - **limit**: 返回数量，默认20，最多50

    返回按 Star 数降序排列的热门项目列表
    """
    query = "stars:>1000"
    if language:
        query += f" language:{language}"

    logger.info(f"获取排行榜: language={language}, since={since}, limit={limit}")

    url = f"{GITHUB_API_BASE_URL}/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }

    try:
        response = await _request_with_retry(url, headers=_get_headers(), params=params)
        data = response.json()
        items = data.get("items", [])

        trending_items = []
        for i, item in enumerate(items):
            trending_items.append(TrendingItem(
                rank=i + 1,
                name=item.get("name", ""),
                full_name=item.get("full_name", ""),
                html_url=item.get("html_url", ""),
                description=item.get("description", "") or "",
                language=item.get("language"),
                stargazers_count=item.get("stargazers_count", 0),
                forks_count=item.get("forks_count", 0),
                open_issues_count=item.get("open_issues_count", 0),
                watchers_count=item.get("watchers_count", 0),
                avatar_url=item.get("owner", {}).get("avatar_url", ""),
                topics=item.get("topics", []),
            ))

        logger.info(f"排行榜获取成功，共 {len(trending_items)} 个项目")

        return TrendingResponse(
            total=data.get("total_count", 0),
            language=language,
            since=since,
            items=trending_items,
        )
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending: {str(e)}")
