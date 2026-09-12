from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime

from app.database import Base


class DownloadTask(Base):
    """内置下载器任务模型"""

    __tablename__ = "download_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 作者/组织
    author = Column(String(100), nullable=False)
    # 仓库名
    repository = Column(String(200), nullable=False)
    # 下载内容类型：zip / release / readme / gitclone
    content_type = Column(String(20), nullable=False)
    # 保存目录
    save_dir = Column(String(500), nullable=False)
    # 目标 URL（git clone 时为远程仓库地址）
    url = Column(String(1000), nullable=False)
    # 保存文件名
    filename = Column(String(300), default="")
    # 总字节数
    total_size = Column(Float, default=0)
    # 已下载字节数
    downloaded = Column(Float, default=0)
    # 实时下载速度（字节/秒）
    speed = Column(Float, default=0)
    # 状态：pending / downloading / completed / failed / cancelled
    status = Column(String(20), default="pending")
    # 错误信息
    error = Column(String(500), default="")
    # 进程 ID（用于取消异步任务）
    proc_id = Column(String(64), default="")
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    # 完成时间
    finished_at = Column(DateTime, default=None)

    def __repr__(self):
        return f"<DownloadTask(id={self.id}, {self.author}/{self.repository}, {self.content_type}, {self.status})>"