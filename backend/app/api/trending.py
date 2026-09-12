from typing import Optional
from datetime import datetime, timedelta
import time

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.schemas.trending import TrendingItem, TrendingResponse
from app.services.github_service import _get_headers, _request_with_retry
from app.config import GITHUB_API_BASE_URL

router = APIRouter()

# 内存 TTL 缓存：同一 (language, since, limit) 组合在 TTL 内的请求不重复打 GitHub，
# 缓解 GitHub 搜索接口限流。进程重启即清空，属轻量提速，非持久化。
TREND_TTL = 300  # 秒
_TREND_CACHE: dict = {}

# 各周期的时间窗口（按仓库创建时间过滤，以近似该周期的热点项目）
# daily 门槛最低，因为刚创建的仓库星数普遍较少；monthly 窗口较宽、门槛最高
SINCE_WINDOW_DAYS = {
    "daily": 3,
    "weekly": 7,
    "monthly": 30,
}
SINCE_MIN_STARS = {
    "daily": 60,
    "weekly": 500,
    "monthly": 1000,
}


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

    返回按 Star 数降序排列的热门项目列表（带 TTL 缓存）
    """
    buster = f"{(language or '').lower()}|{since}|{limit}"
    now = time.time()
    hit = _TREND_CACHE.get(buster)
    if hit and now - hit[0] < TREND_TTL:
        logger.info(f"排行榜命中缓存: {buster}")
        return hit[1]

    query = "stars:>1000"

    # 用仓库创建时间窗口区分各周期，使不同周期的榜单产生差异
    if since in SINCE_WINDOW_DAYS:
        days = SINCE_WINDOW_DAYS[since]
        min_stars = SINCE_MIN_STARS.get(since, 500)
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = f"stars:>{min_stars} created:>{cutoff}"

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
                created_at=item.get("created_at"),
                topics=item.get("topics", []),
            ))

        logger.info(f"排行榜获取成功，共 {len(trending_items)} 个项目")

        response = TrendingResponse(
            total=data.get("total_count", 0),
            language=language,
            since=since,
            items=trending_items,
        )
        # 成功后写入缓存，失败/异常不缓存
        _TREND_CACHE[buster] = (time.time(), response)
        return response
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending: {str(e)}")
