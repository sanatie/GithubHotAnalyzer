from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReportBase(BaseModel):
    """报告基础信息模型"""
    repo_id: int = Field(..., gt=0, description="关联的仓库 ID")
    repo_full_name: str = Field(..., min_length=1, max_length=255, description="仓库完整名称")
    overall_score: int = Field(0, ge=0, le=100, description="综合评分（0-100）")
    tech_stack: Optional[List[str]] = Field(default_factory=list, description="技术栈列表")
    highlights: str = Field("", description="项目亮点")
    learning_advice: str = Field("", description="学习建议")


class ReportCreate(ReportBase):
    """创建报告请求模型"""
    content: str = Field(..., description="AI 分析报告内容（JSON 格式）")


class Report(ReportBase):
    """报告响应模型"""
    id: int = Field(..., description="报告 ID")
    content: str = Field(..., description="AI 分析报告内容（JSON 格式）")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        orm_mode = True


class ReportListResponse(BaseModel):
    """报告列表响应"""
    total: int = Field(..., ge=0, description="总数量")
    page: int = Field(1, ge=1, description="当前页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    total_pages: int = Field(0, ge=0, description="总页数")
    items: List[Report] = Field(default_factory=list, description="报告列表")
