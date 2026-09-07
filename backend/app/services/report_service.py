import json
from typing import Dict, Optional, Tuple, List

from loguru import logger
from sqlalchemy.orm import Session

from app.models.report import Report
from app.models.favorite import Favorite
from app.schemas.report import ReportCreate


def save_report(db: Session, repo_id: int, repo_full_name: str, analysis_result: Dict) -> Report:
    """
    保存分析报告到数据库

    参数:
        db: 数据库会话
        repo_id: 仓库 ID
        repo_full_name: 仓库完整名称
        analysis_result: AI 分析结果字典

    返回:
        保存后的 Report 对象
    """
    logger.info(f"保存分析报告: repo={repo_full_name}, score={analysis_result.get('overall_score', 0)}")

    tech_stack = analysis_result.get("tech_stack", [])
    highlights = analysis_result.get("highlights", [])

    db_report = Report(
        repo_id=repo_id,
        repo_full_name=repo_full_name,
        content=json.dumps(analysis_result, ensure_ascii=False),
        overall_score=analysis_result.get("overall_score", 0),
        tech_stack=json.dumps(tech_stack, ensure_ascii=False),
        highlights="\n".join(highlights),
        learning_advice=analysis_result.get("learning_advice", "")
    )

    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    logger.info(f"报告保存成功: id={db_report.id}, repo={repo_full_name}")
    return db_report


def get_latest_report(db: Session, repo_full_name: str) -> Optional[Report]:
    """
    获取某个仓库最新的分析报告

    参数:
        db: 数据库会话
        repo_full_name: 仓库完整名称（owner/repo）

    返回:
        最新的 Report 对象，如果没有则返回 None
    """
    logger.debug(f"查询最新报告: repo={repo_full_name}")
    report = db.query(Report).filter(
        Report.repo_full_name == repo_full_name
    ).order_by(Report.created_at.desc()).first()

    if report:
        logger.debug(f"找到报告: id={report.id}, score={report.overall_score}")
    else:
        logger.debug(f"未找到报告: repo={repo_full_name}")

    return report


def get_report_by_id(db: Session, report_id: int) -> Optional[Report]:
    """
    根据 ID 获取报告

    参数:
        db: 数据库会话
        report_id: 报告 ID

    返回:
        Report 对象，不存在则返回 None
    """
    logger.debug(f"查询报告: id={report_id}")
    report = db.query(Report).filter(Report.id == report_id).first()

    if report:
        logger.debug(f"找到报告: repo={report.repo_full_name}")
    else:
        logger.debug(f"未找到报告: id={report_id}")

    return report


def get_report_history(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    keyword: Optional[str] = None
) -> Tuple[int, List[Report]]:
    """
    获取报告历史列表

    参数:
        db: 数据库会话
        skip: 跳过数量
        limit: 返回数量
        keyword: 搜索关键词（仓库名称）

    返回:
        (总数, 列表) 元组
    """
    logger.debug(f"查询报告历史: skip={skip}, limit={limit}, keyword={keyword}")
    query = db.query(Report)

    if keyword:
        keyword_lower = keyword.lower()
        query = query.filter(Report.repo_full_name.ilike(f"%{keyword_lower}%"))

    total = query.count()
    items = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    logger.debug(f"报告历史查询完成: total={total}, returned={len(items)}")
    return total, items


def parse_report_content(report: Report) -> Dict:
    """
    解析报告内容，从 JSON 字符串转为字典

    参数:
        report: Report 对象

    返回:
        解析后的内容字典
    """
    try:
        content = json.loads(report.content)
        logger.debug(f"报告内容解析成功: id={report.id}")
        return content
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"报告内容解析失败: id={report.id}, error={e}")
        return {}


def delete_report(db: Session, report_id: int) -> bool:
    """
    删除报告（同步删除对应收藏）

    参数:
        db: 数据库会话
        report_id: 报告 ID

    返回:
        是否删除成功
    """
    logger.info(f"删除报告: id={report_id}")
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        logger.warning(f"报告不存在: id={report_id}")
        return False

    repo_full_name = report.repo_full_name
    db.delete(report)

    fav = db.query(Favorite).filter(Favorite.repo_full_name == repo_full_name).first()
    if fav:
        db.delete(fav)
        logger.info(f"同步删除收藏: repo={repo_full_name}")

    db.commit()
    logger.info(f"报告删除成功: id={report_id}")
    return True


def delete_reports_batch(db: Session, report_ids: List[int]) -> int:
    """
    批量删除报告（同步删除对应收藏）

    参数:
        db: 数据库会话
        report_ids: 报告 ID 列表

    返回:
        删除的数量
    """
    logger.info(f"批量删除报告: ids={report_ids}")
    if not report_ids:
        return 0

    reports = db.query(Report).filter(Report.id.in_(report_ids)).all()
    repo_full_names = [r.repo_full_name for r in reports]

    result = db.query(Report).filter(Report.id.in_(report_ids)).delete(synchronize_session=False)

    if repo_full_names:
        fav_count = db.query(Favorite).filter(Favorite.repo_full_name.in_(repo_full_names)).delete(synchronize_session=False)
        if fav_count > 0:
            logger.info(f"同步删除收藏: count={fav_count}")

    db.commit()
    logger.info(f"批量删除成功: count={result}")
    return result


def delete_all_reports(db: Session) -> int:
    """
    删除所有报告（同步删除所有收藏）

    参数:
        db: 数据库会话

    返回:
        删除的数量
    """
    logger.info("删除所有报告")
    result = db.query(Report).delete(synchronize_session=False)
    fav_count = db.query(Favorite).delete(synchronize_session=False)
    if fav_count > 0:
        logger.info(f"同步删除所有收藏: count={fav_count}")
    db.commit()
    logger.info(f"全部删除成功: count={result}")
    return result


def delete_old_reports(db: Session, repo_full_name: str, keep_latest: bool = True) -> int:
    """
    删除旧报告（保留最新）

    参数:
        db: 数据库会话
        repo_full_name: 仓库完整名称
        keep_latest: 是否保留最新报告

    返回:
        删除的报告数量
    """
    logger.info(f"清理旧报告: repo={repo_full_name}, keep_latest={keep_latest}")

    query = db.query(Report).filter(Report.repo_full_name == repo_full_name)

    if keep_latest:
        latest = query.order_by(Report.created_at.desc()).first()
        if latest:
            query = query.filter(Report.id != latest.id)

    deleted_count = query.delete()
    db.commit()

    logger.info(f"删除旧报告完成: count={deleted_count}")
    return deleted_count
