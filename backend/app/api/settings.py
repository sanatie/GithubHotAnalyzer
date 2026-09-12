import time

import httpx
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.config import get_ai_config, update_ai_config, ai_base_url_allowed, AI_VERIFY_SSL
from app.schemas.settings import (
    AIConfigUpdate,
    AIConfigResponse,
    AIConfigTestRequest,
    AIConfigTestResponse,
)


router = APIRouter()


def _mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]


@router.get("/ai", response_model=AIConfigResponse)
def get_ai_config_endpoint():
    """
    Get current AI configuration (API Key masked)
    """
    logger.info("Fetching AI configuration")
    cfg = get_ai_config()
    return AIConfigResponse(
        api_key_masked=_mask_api_key(cfg["api_key"]),
        api_base_url=cfg["api_base_url"],
        model=cfg["model"],
    )


@router.put("/ai")
def update_ai_config_endpoint(body: AIConfigUpdate):
    """
    Update AI configuration

    Request body: {"api_key": "...", "api_base_url": "...", "model": "..."}
    """
    logger.info(f"Updating AI configuration: model={body.model}, base_url={body.api_base_url}")
    success = update_ai_config(
        api_key=body.api_key,
        api_base_url=body.api_base_url,
        model=body.model,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Configuration update failed")
    cfg = get_ai_config()
    return AIConfigResponse(
        api_key_masked=_mask_api_key(cfg["api_key"]),
        api_base_url=cfg["api_base_url"],
        model=cfg["model"],
    )


@router.post("/ai/test", response_model=AIConfigTestResponse)
async def test_ai_connection(body: AIConfigTestRequest):
    """
    Test AI API connection

    Sends a minimal request to verify the API key and endpoint are valid.
    """
    logger.info(f"Testing AI connection: model={body.model}, base_url={body.api_base_url}")

    # Use saved key if sentinel value is passed
    api_key = body.api_key
    if api_key == "use_saved":
        cfg = get_ai_config()
        api_key = cfg["api_key"]
        logger.info("Using saved API key for test")

    url = f"{body.api_base_url.rstrip('/')}/chat/completions"
    _ok, _reason = ai_base_url_allowed(body.api_base_url)
    if not _ok:
        return AIConfigTestResponse(
            success=False,
            message=f"API 地址未通过安全校验：{_reason}",
            latency_ms=0,
        )
    if any(ord(c) > 127 for c in api_key):
        return AIConfigTestResponse(
            success=False,
            message="API Key 配置不正确（混入了中文或特殊字符），请填写真实的 API Key",
            latency_ms=0,
        )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": body.model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5,
    }

    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=AI_VERIFY_SSL) as client:
            response = await client.post(url, headers=headers, json=payload)
            elapsed = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                logger.info(f"AI connection test succeeded: {elapsed}ms")
                return AIConfigTestResponse(
                    success=True,
                    message=f"连接成功，模型 {body.model} 可正常调用",
                    latency_ms=elapsed,
                )

            # HTTP error - parse error message
            error_msg = _parse_error_response(response)
            logger.warning(f"AI connection test failed: {response.status_code} - {error_msg}")
            return AIConfigTestResponse(
                success=False,
                message=error_msg,
                latency_ms=elapsed,
            )

    except httpx.ConnectError:
        return AIConfigTestResponse(
            success=False,
            message="无法连接到 API 地址，请检查 API Base URL 是否正确",
            latency_ms=int((time.time() - start_time) * 1000),
        )
    except httpx.TimeoutException:
        return AIConfigTestResponse(
            success=False,
            message="连接超时，API 服务未在 15 秒内响应，请检查网络或更换 API 地址",
            latency_ms=int((time.time() - start_time) * 1000),
        )
    except Exception as e:
        logger.error(f"AI connection test error: {e}")
        return AIConfigTestResponse(
            success=False,
            message=f"连接测试异常: {str(e)}",
            latency_ms=int((time.time() - start_time) * 1000),
        )


def _parse_error_response(response: httpx.Response) -> str:
    """Parse HTTP error response into Chinese message"""
    status = response.status_code

    try:
        data = response.json()
        api_msg = data.get("error", {}).get("message", "")
    except Exception:
        api_msg = ""

    if status == 401:
        return f"认证失败（401）：API Key 无效或已过期{f' - {api_msg}' if api_msg else ''}"
    elif status == 403:
        return f"访问被拒绝（403）：API Key 权限不足或已达调用限制{f' - {api_msg}' if api_msg else ''}"
    elif status == 404:
        return f"接口不存在（404）：请检查 API Base URL 是否正确，模型名称是否匹配"
    elif status == 429:
        return f"请求过多（429）：API 调用频率超限，请稍后重试"
    elif 400 <= status < 500:
        return f"请求错误（{status}）{f' - {api_msg}' if api_msg else ''}"
    elif 500 <= status < 600:
        return f"AI 服务异常（{status}）：服务端暂时不可用，请稍后重试"

    return f"连接失败（HTTP {status}）{f' - {api_msg}' if api_msg else ''}"