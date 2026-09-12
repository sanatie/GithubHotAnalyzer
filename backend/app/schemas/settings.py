from pydantic import BaseModel, Field


class AIConfigUpdate(BaseModel):
    """更新 AI 配置请求模型"""
    api_key: str = Field(..., min_length=1, max_length=500, description="AI API Key")
    api_base_url: str = Field(..., min_length=1, max_length=500, description="AI API 基础地址")
    model: str = Field(..., min_length=1, max_length=100, description="AI 模型名称")


class AIConfigResponse(BaseModel):
    """AI 配置响应模型"""
    api_key_masked: str = Field(..., description="脱敏后的 API Key")
    api_base_url: str = Field(..., description="AI API 基础地址")
    model: str = Field(..., description="AI 模型名称")
    ai_available: bool = Field(True, description="AI 是否可用（Key 与 base url 均已配置）")


class AIConfigTestRequest(BaseModel):
    """AI 连接测试请求模型"""
    api_key: str = Field(..., min_length=1, max_length=500, description="AI API Key")
    api_base_url: str = Field(..., min_length=1, max_length=500, description="AI API 基础地址")
    model: str = Field(..., min_length=1, max_length=100, description="AI 模型名称")


class AIConfigTestResponse(BaseModel):
    """AI 连接测试响应模型"""
    success: bool = Field(..., description="是否连接成功")
    message: str = Field(..., description="结果信息")
    latency_ms: int = Field(0, description="响应耗时(毫秒)")
