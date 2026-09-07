import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.database import get_db
from app.models.chat_history import ChatHistory
from app.schemas.chat_history import ChatHistoryOut, ChatHistoryListResponse

router = APIRouter()


def _serialize_record(record: ChatHistory) -> ChatHistoryOut:
    """将 DB 记录序列化为响应模型"""
    try:
        items = json.loads(record.items) if record.items else []
    except (json.JSONDecodeError, TypeError):
        items = []
    return ChatHistoryOut(
        id=record.id,
        query=record.query,
        items=items,
        total=record.total or len(items),
        injection_detected=record.injection_detected,
        created_at=record.created_at,
    )


@router.get("/history", response_model=ChatHistoryListResponse)
def get_chat_history(
    page: int = 1,
    page_size: int = 10,
    keyword: str = "",
    db: Session = Depends(get_db),
):
    """分页查询 AI 对话记录，支持按关键词搜索"""
    logger.info(f"Fetching chat history: page={page}, page_size={page_size}, keyword={keyword}")

    query = db.query(ChatHistory)
    if keyword:
        query = query.filter(ChatHistory.query.contains(keyword))

    total = query.count()
    records = (
        query.order_by(ChatHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ChatHistoryListResponse(
        items=[_serialize_record(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/history/{record_id}")
def delete_chat_history(record_id: int, db: Session = Depends(get_db)):
    """删除单条对话记录"""
    record = db.query(ChatHistory).filter(ChatHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="对话记录不存在")
    db.delete(record)
    db.commit()
    logger.info(f"Deleted chat history record {record_id}")
    return {"success": True, "message": "删除成功"}


@router.delete("/history")
def clear_chat_history(db: Session = Depends(get_db)):
    """清空全部对话记录"""
    count = db.query(ChatHistory).delete()
    db.commit()
    logger.info(f"Cleared all chat history, deleted {count} records")
    return {"success": True, "message": f"已清空 {count} 条对话记录"}