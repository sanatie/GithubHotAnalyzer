from typing import List, Optional

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """评分细分模型"""
    popularity: int = Field(0, ge=0, le=100, description="流行度评分")
    code_quality: int = Field(0, ge=0, le=100, description="代码质量评分")
    documentation: int = Field(0, ge=0, le=100, description="文档完善度评分")
    activity: int = Field(0, ge=0, le=100, description="活跃度评分")


class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    repo_url: str = Field(..., description="GitHub 仓库地址，例如 https://github.com/owner/repo")
    force_refresh: bool = Field(False, description="是否强制重新分析，忽略缓存")


class AnalyzeResponse(BaseModel):
    """分析响应模型"""
    repo_full_name: str = Field(..., description="仓库完整名称")
    overall_score: int = Field(0, ge=0, le=100, description="综合评分（0-100）")
    summary: str = Field("", description="项目概述")
    tech_stack: List[str] = Field(default_factory=list, description="技术栈列表")
    highlights: List[str] = Field(default_factory=list, description="项目亮点列表")
    learning_advice: str = Field("", description="学习建议")
    score_breakdown: Optional[ScoreBreakdown] = Field(None, description="评分细分")
    suitable_for: Optional[List[str]] = Field(None, description="适合人群")
    report_id: Optional[int] = Field(None, description="关联的报告 ID")
    repository: Optional[dict] = Field(None, description="仓库信息（包含 stars、forks 等）")


class AnalysisItem(BaseModel):
    """单条分析项"""
    title: str = Field(..., min_length=1, description="分析项标题")
    content: str = Field(..., description="分析项内容")
