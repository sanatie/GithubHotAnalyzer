from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Report(Base):
    """分析报告模型"""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 关联的仓库 ID
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    # 仓库完整名称（冗余存储，方便查询）
    repo_full_name = Column(String(255), index=True, nullable=False)
    # AI 分析后的中文报告内容（JSON 格式存储结构化数据）
    content = Column(Text, nullable=False)
    # 综合评分（0-100）
    overall_score = Column(Integer, default=0)
    # 技术栈（JSON 字符串存储）
    tech_stack = Column(Text, default="")
    # 项目亮点
    highlights = Column(Text, default="")
    # 学习建议
    learning_advice = Column(Text, default="")
    # 报告生成时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联仓库
    repository = relationship("Repository", backref="reports")

    def __repr__(self):
        return f"<Report(id={self.id}, repo='{self.repo_full_name}', score={self.overall_score})>"
