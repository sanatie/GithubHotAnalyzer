from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Favorite(Base):
    """收藏记录模型"""

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 关联的仓库 ID
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, unique=True)
    # 仓库完整名称（冗余存储，方便查询）
    repo_full_name = Column(String(255), index=True, nullable=False)
    # 收藏备注
    note = Column(String(500), default="")
    # 收藏标签（逗号分隔，如 "web,ai"）
    tags = Column(String(500), default="")
    # 收藏时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联仓库
    repository = relationship("Repository", backref="favorites")

    def __repr__(self):
        return f"<Favorite(id={self.id}, repo='{self.repo_full_name}')>"
