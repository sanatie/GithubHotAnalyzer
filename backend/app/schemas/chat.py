from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRecommendRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="用户需求描述")


class ChatRecommendItem(BaseModel):
    name: str = Field(..., description="项目名称")
    author: str = Field(..., description="项目作者/组织")
    description: str = Field(..., description="项目描述")
    language: str = Field(..., description="主要编程语言")
    stars: str = Field(..., description="Star 数量（约数）")
    use_case: str = Field(..., description="应用场景")
    reason: str = Field(..., description="推荐理由")
    github_url: str = Field(..., description="GitHub 仓库地址")


class ChatRecommendResponse(BaseModel):
    query: str = Field(..., description="用户原始查询")
    injection_detected: bool = Field(..., description="是否检测到 Prompt 注入")
    items: List[ChatRecommendItem] = Field(default_factory=list, description="推荐项目列表")
    total: int = Field(..., description="推荐项目数量")
