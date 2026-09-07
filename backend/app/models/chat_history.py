from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime

from app.database import Base


class ChatHistory(Base):
    """AI 对话推荐记录模型"""

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 用户输入的需求描述
    query = Column(String(500), index=True, nullable=False)
    # AI 返回的推荐项目列表（JSON 字符串存储完整列表）
    items = Column(Text, nullable=False)
    # 推荐项目数量
    total = Column(Integer, default=0)
    # 是否检测到 Prompt 注入
    injection_detected = Column(Boolean, default=False)
    # 对话时间
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, query='{self.query[:30]}', total={self.total})>"