from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class FavoriteBase(BaseModel):
    """收藏基础信息模型"""
    repo_id: int = Field(..., gt=0, description="关联的仓库 ID")
    repo_full_name: str = Field(..., min_length=1, max_length=255, description="仓库完整名称")
    note: Optional[str] = Field("", max_length=500, description="收藏备注")
    tags: Optional[str] = Field("", max_length=500, description="收藏标签，逗号分隔")


class FavoriteCreate(BaseModel):
    """创建收藏请求模型"""
    repo_id: int = Field(..., gt=0, description="关联的仓库 ID")
    repo_full_name: str = Field(..., min_length=1, max_length=255, description="仓库完整名称")
    note: Optional[str] = Field("", max_length=500, description="收藏备注")
    tags: Optional[str] = Field("", max_length=500, description="收藏标签，逗号分隔")


class FavoriteUpdate(BaseModel):
    """更新收藏请求模型"""
    note: Optional[str] = Field(None, max_length=500, description="收藏备注")
    tags: Optional[str] = Field(None, max_length=500, description="收藏标签，逗号分隔")


class FavoriteBatchItem(BaseModel):
    """批量收藏单项（兼容购物车/推荐数据结构）"""
    author: str = Field("", max_length=255, description="仓库所有者")
    name: str = Field("", max_length=255, description="仓库名")
    repo_full_name: Optional[str] = Field(None, max_length=255, description="仓库完整名称，缺省为 author/name")
    repository_id: Optional[int] = Field(None, gt=0, description="已存在的仓库 ID，可选")
    html_url: Optional[str] = Field("", max_length=500, description="仓库主页")
    description: Optional[str] = Field("", max_length=2000, description="仓库描述")
    language: Optional[str] = Field("", max_length=100, description="主要语言")
    stargazers_count: Optional[int] = Field(0, ge=0, description="Star 数量")
    forks_count: Optional[int] = Field(0, ge=0, description="Fork 数量")
    note: Optional[str] = Field("", max_length=500, description="收藏备注")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表，按逗号拼接存储")


class FavoriteBatchCreate(BaseModel):
    """批量收藏请求"""
    items: List[FavoriteBatchItem] = Field(..., min_items=1, max_items=200, description="待收藏的仓库列表")


class Favorite(FavoriteBase):
    """收藏响应模型"""
    id: int = Field(..., description="收藏记录 ID")
    created_at: datetime = Field(..., description="收藏时间")

    class Config:
        orm_mode = True
