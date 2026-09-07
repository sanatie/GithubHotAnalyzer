from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class Repository(Base):
    """仓库信息模型"""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 仓库唯一标识（owner/repo）
    full_name = Column(String(255), unique=True, index=True, nullable=False)
    # 仓库名称
    name = Column(String(255), nullable=False)
    # 仓库所有者
    owner = Column(String(255), nullable=False)
    # 仓库描述
    description = Column(Text, default="")
    # 仓库主页
    html_url = Column(String(500), default="")
    # 主要语言
    language = Column(String(100), default="")
    # Star 数量
    stargazers_count = Column(Integer, default=0)
    # Fork 数量
    forks_count = Column(Integer, default=0)
    # 观察者数量
    watchers_count = Column(Integer, default=0)
    # 开放 Issue 数量
    open_issues_count = Column(Integer, default=0)
    # 主题标签（JSON 字符串存储）
    topics = Column(Text, default="")
    # 开源许可证
    license = Column(String(100), default="")
    # 默认分支
    default_branch = Column(String(100), default="main")
    # 首次创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    # 最后更新时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Repository(id={self.id}, full_name='{self.full_name}', stars={self.stargazers_count})>"
