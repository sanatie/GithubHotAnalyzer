from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from app.database import Base


class DownloadCreate(BaseModel):
    author: str = Field(..., description="作者/组织")
    repository: str = Field(..., description="仓库名")
    content_type: str = Field(..., description="zip / release / readme / gitclone")
    save_dir: str = Field("", description="保存目录，留空用默认目录")
    url: str = Field("", description="目标URL，gitclone必填")
    filename: str = Field("", description="保存文件名")
    mirror: str = Field("", description="git clone 镜像前缀，留空用直连/全局默认镜像")


class DownloadTaskOut(BaseModel):
    id: int
    author: str
    repository: str
    content_type: str
    save_dir: str
    url: str
    filename: str
    total_size: float
    downloaded: float
    progress: float = Field(0, description="0-100 进度")
    speed: float
    status: str
    error: str

    class Config:
        from_attributes = True


class ProjectContentInfo(BaseModel):
    author: str
    repository: str
    default_branch: str = "main"
    html_url: str = ""
    zip_url: str = ""
    has_readme: bool = False
    readme_url: str = ""
    has_release: bool = False
    releases: List[dict] = Field(default_factory=list)
    clone_url: str = ""
    github_url: str = ""


class DownloadTaskListResponse(BaseModel):
    items: List[DownloadTaskOut]
    total: int