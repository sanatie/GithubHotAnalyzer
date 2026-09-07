from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RepositoryBase(BaseModel):
    """仓库基础信息模型"""
    full_name: str = Field(..., min_length=1, max_length=255, description="仓库唯一标识（owner/repo）")
    name: str = Field(..., min_length=1, max_length=255, description="仓库名称")
    owner: str = Field(..., min_length=1, max_length=255, description="仓库所有者")
    description: Optional[str] = Field("", max_length=5000, description="仓库描述")
    html_url: str = Field(..., max_length=500, description="仓库主页 URL")
    language: Optional[str] = Field(None, max_length=100, description="主要编程语言")
    stargazers_count: int = Field(0, ge=0, description="Star 数量")
    forks_count: int = Field(0, ge=0, description="Fork 数量")
    watchers_count: int = Field(0, ge=0, description="观察者数量")
    open_issues_count: int = Field(0, ge=0, description="开放 Issue 数量")
    topics: Optional[List[str]] = Field(default_factory=list, description="主题标签列表")
    license: Optional[str] = Field(None, max_length=100, description="开源许可证")
    default_branch: Optional[str] = Field("main", max_length=100, description="默认分支")


class RepositoryCreate(BaseModel):
    """创建仓库请求模型"""
    full_name: str = Field(..., min_length=1, max_length=255, description="仓库唯一标识（owner/repo）")
    name: str = Field(..., min_length=1, max_length=255, description="仓库名称")
    owner: str = Field(..., min_length=1, max_length=255, description="仓库所有者")
    description: Optional[str] = Field("", max_length=5000, description="仓库描述")
    html_url: Optional[str] = Field(None, max_length=500, description="仓库主页 URL")
    language: Optional[str] = Field(None, max_length=100, description="主要编程语言")
    stargazers_count: int = Field(0, ge=0, description="Star 数量")
    forks_count: int = Field(0, ge=0, description="Fork 数量")
    watchers_count: int = Field(0, ge=0, description="观察者数量")
    open_issues_count: int = Field(0, ge=0, description="开放 Issue 数量")
    topics: Optional[List[str]] = Field(default_factory=list, description="主题标签列表")
    license: Optional[str] = Field(None, max_length=100, description="开源许可证")
    default_branch: Optional[str] = Field("main", max_length=100, description="默认分支")


class Repository(RepositoryBase):
    """仓库响应模型"""
    id: int = Field(..., description="仓库 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        orm_mode = True


class RepositoryListResponse(BaseModel):
    """仓库列表响应"""
    total: int = Field(..., ge=0, description="总数量")
    page: int = Field(1, ge=1, description="当前页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    total_pages: int = Field(0, ge=0, description="总页数")
    items: List[Repository] = Field(default_factory=list, description="仓库列表")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")
