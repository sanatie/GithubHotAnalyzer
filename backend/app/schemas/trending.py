from typing import List, Optional

from pydantic import BaseModel, Field


class TrendingItem(BaseModel):
    """排行榜单项"""
    rank: int = Field(..., ge=1, description="排名")
    name: str = Field(..., description="仓库名称")
    full_name: str = Field(..., description="完整名称 (owner/repo)")
    html_url: str = Field(..., description="仓库主页 URL")
    description: Optional[str] = Field("", description="仓库描述")
    language: Optional[str] = Field(None, description="主要编程语言")
    stargazers_count: int = Field(0, ge=0, description="Star 数量")
    forks_count: int = Field(0, ge=0, description="Fork 数量")
    open_issues_count: int = Field(0, ge=0, description="开放 Issue 数量")
    watchers_count: int = Field(0, ge=0, description="观察者数量")
    avatar_url: Optional[str] = Field("", description="所有者头像 URL")
    created_at: Optional[str] = Field(None, description="仓库创建时间")
    topics: Optional[List[str]] = Field(default_factory=list, description="主题标签")


class TrendingResponse(BaseModel):
    """排行榜响应"""
    total: int = Field(..., ge=0, description="结果总数")
    language: Optional[str] = Field(None, description="编程语言筛选")
    since: str = Field("weekly", description="时间范围")
    items: List[TrendingItem] = Field(default_factory=list, description="排行榜列表")
