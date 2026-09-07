from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FavoriteBase(BaseModel):
    """收藏基础信息模型"""
    repo_id: int = Field(..., gt=0, description="关联的仓库 ID")
    repo_full_name: str = Field(..., min_length=1, max_length=255, description="仓库完整名称")
    note: Optional[str] = Field("", max_length=500, description="收藏备注")


class FavoriteCreate(BaseModel):
    """创建收藏请求模型"""
    repo_id: int = Field(..., gt=0, description="关联的仓库 ID")
    repo_full_name: str = Field(..., min_length=1, max_length=255, description="仓库完整名称")
    note: Optional[str] = Field("", max_length=500, description="收藏备注")


class FavoriteUpdate(BaseModel):
    """更新收藏请求模型"""
    note: Optional[str] = Field(None, max_length=500, description="收藏备注")


class Favorite(FavoriteBase):
    """收藏响应模型"""
    id: int = Field(..., description="收藏记录 ID")
    created_at: datetime = Field(..., description="收藏时间")

    class Config:
        orm_mode = True
