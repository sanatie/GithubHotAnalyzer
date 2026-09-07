from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.schemas.chat import ChatRecommendItem


class ChatHistoryOut(BaseModel):
    """对话记录查询返回项"""

    id: int
    query: str
    items: List[ChatRecommendItem]
    total: int
    injection_detected: bool
    created_at: datetime


class ChatHistoryListResponse(BaseModel):
    """对话记录分页查询返回"""

    items: List[ChatHistoryOut]
    total: int
    page: int
    page_size: int