import json
from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate


def upsert_repository(db: Session, repo_data: dict) -> Repository:
    """
    新增或更新仓库信息

    参数:
        db: 数据库会话
        repo_data: GitHub API 返回的仓库数据

    返回:
        Repository 对象
    """
    full_name = repo_data.get("full_name", "")
    owner = repo_data.get("owner", {}).get("login", "") if isinstance(repo_data.get("owner"), dict) else ""
    topics = repo_data.get("topics", [])

    existing = db.query(Repository).filter(Repository.full_name == full_name).first()

    if existing:
        # 更新已有记录
        logger.info(f"更新仓库信息: {full_name}")
        existing.name = repo_data.get("name", existing.name)
        existing.owner = owner
        existing.description = repo_data.get("description", existing.description)
        existing.html_url = repo_data.get("html_url", existing.html_url)
        existing.language = repo_data.get("language", existing.language)
        existing.stargazers_count = repo_data.get("stargazers_count", existing.stargazers_count)
        existing.forks_count = repo_data.get("forks_count", existing.forks_count)
        existing.watchers_count = repo_data.get("watchers_count", existing.watchers_count)
        existing.open_issues_count = repo_data.get("open_issues_count", existing.open_issues_count)
        existing.topics = json.dumps(topics, ensure_ascii=False)
        existing.license = repo_data.get("license", {}).get("spdx_id", "") if isinstance(repo_data.get("license"), dict) else ""
        existing.default_branch = repo_data.get("default_branch", "main")
        db.commit()
        db.refresh(existing)
        logger.debug(f"仓库更新成功: {full_name}, stars={existing.stargazers_count}")
        return existing
    else:
        # 创建新记录
        logger.info(f"创建仓库记录: {full_name}")
        db_repo = Repository(
            full_name=full_name,
            name=repo_data.get("name", ""),
            owner=owner,
            description=repo_data.get("description", ""),
            html_url=repo_data.get("html_url", ""),
            language=repo_data.get("language", ""),
            stargazers_count=repo_data.get("stargazers_count", 0),
            forks_count=repo_data.get("forks_count", 0),
            watchers_count=repo_data.get("watchers_count", 0),
            open_issues_count=repo_data.get("open_issues_count", 0),
            topics=json.dumps(topics, ensure_ascii=False),
            license=repo_data.get("license", {}).get("spdx_id", "") if isinstance(repo_data.get("license"), dict) else "",
            default_branch=repo_data.get("default_branch", "main"),
        )
        db.add(db_repo)
        db.commit()
        db.refresh(db_repo)
        logger.info(f"仓库创建成功: {full_name}, id={db_repo.id}")
        return db_repo


def get_repository_by_full_name(db: Session, full_name: str) -> Optional[Repository]:
    """
    根据完整名称获取仓库

    参数:
        db: 数据库会话
        full_name: 仓库完整名称（owner/repo）

    返回:
        Repository 对象，不存在则返回 None
    """
    logger.debug(f"查询仓库: full_name={full_name}")
    repo = db.query(Repository).filter(Repository.full_name == full_name).first()

    if repo:
        logger.debug(f"找到仓库: id={repo.id}, stars={repo.stargazers_count}")
    else:
        logger.debug(f"未找到仓库: full_name={full_name}")

    return repo


def get_repository_by_id(db: Session, repo_id: int) -> Optional[Repository]:
    """
    根据 ID 获取仓库

    参数:
        db: 数据库会话
        repo_id: 仓库 ID

    返回:
        Repository 对象，不存在则返回 None
    """
    logger.debug(f"查询仓库: id={repo_id}")
    repo = db.query(Repository).filter(Repository.id == repo_id).first()

    if repo:
        logger.debug(f"找到仓库: full_name={repo.full_name}")
    else:
        logger.debug(f"未找到仓库: id={repo_id}")

    return repo


def list_repositories(
    db: Session,
    keyword: str = "",
    language: str = "",
    skip: int = 0,
    limit: int = 20
) -> Tuple[int, List[Repository]]:
    """
    分页查询仓库列表

    参数:
        db: 数据库会话
        keyword: 关键词搜索（匹配名称或描述）
        language: 编程语言筛选
        skip: 跳过数量
        limit: 返回数量

    返回:
        (总数, 列表) 元组
    """
    logger.debug(f"查询仓库列表: keyword={keyword}, language={language}, skip={skip}, limit={limit}")

    query = db.query(Repository)

    if keyword:
        query = query.filter(
            (Repository.full_name.contains(keyword)) |
            (Repository.description.contains(keyword))
        )

    if language:
        query = query.filter(Repository.language == language)

    total = query.count()
    items = query.order_by(Repository.stargazers_count.desc()).offset(skip).limit(limit).all()

    logger.debug(f"仓库列表查询完成: total={total}, returned={len(items)}")
    return total, items


def enrich_repo_with_topics(repo: Repository) -> dict:
    """
    将 Repository 对象转为字典，并解析 topics 字段

    参数:
        repo: Repository 对象

    返回:
        包含 topics 列表的字典
    """
    result = {
        "id": repo.id,
        "full_name": repo.full_name,
        "name": repo.name,
        "owner": repo.owner,
        "description": repo.description,
        "html_url": repo.html_url,
        "language": repo.language,
        "stargazers_count": repo.stargazers_count,
        "forks_count": repo.forks_count,
        "watchers_count": repo.watchers_count,
        "open_issues_count": repo.open_issues_count,
        "topics": [],
        "license": repo.license,
        "default_branch": repo.default_branch,
        "created_at": repo.created_at,
        "updated_at": repo.updated_at,
    }
    try:
        result["topics"] = json.loads(repo.topics) if repo.topics else []
    except (json.JSONDecodeError, TypeError):
        pass
    return result


def delete_repository(db: Session, repo_id: int) -> bool:
    """
    删除仓库记录

    参数:
        db: 数据库会话
        repo_id: 仓库 ID

    返回:
        是否删除成功
    """
    logger.info(f"删除仓库: id={repo_id}")
    repo = db.query(Repository).filter(Repository.id == repo_id).first()

    if repo:
        full_name = repo.full_name
        db.delete(repo)
        db.commit()
        logger.info(f"仓库删除成功: {full_name}")
        return True

    logger.warning(f"仓库不存在，无法删除: id={repo_id}")
    return False
