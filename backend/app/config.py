import os
import sys
from pathlib import Path


def _get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _get_base_dir()


def _get_env_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path(__file__).resolve().parent.parent / ".env"


def _load_env():
    env_paths = []
    if getattr(sys, '_MEIPASS', False):
        env_paths.append(Path(sys._MEIPASS) / ".env")
    env_paths.append(_get_env_path())
    
    try:
        from dotenv import load_dotenv
        for p in env_paths:
            if p.exists():
                load_dotenv(dotenv_path=p, override=True)
    except ImportError:
        pass


_load_env()


DATABASE_URL = f"sqlite:///{BASE_DIR / 'data' / 'github_analyzer.db'}"

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_BASE_URL = os.getenv("AI_API_BASE_URL", "")
AI_MODEL = os.getenv("AI_MODEL", "qwen-plus")

# AI 服务安全开关
# - AI_VERIFY_SSL：是否校验 TLS 证书，默认开启
# - AI_BASE_ALLOWLIST：允许的 AI base url 官方域名白名单（逗号分隔，默认仅 DeepSeek）
# - AI_STRICT_BASE：默认从严，base url 必须命中白名单且禁止纯 IP/内网地址；置 false 放行任意地址（不推荐）
AI_VERIFY_SSL = os.getenv("AI_VERIFY_SSL", "true").strip().lower() in ("1", "true", "yes", "on")
AI_BASE_ALLOWLIST = [
    d.strip().lower().lstrip(".")
    for d in os.getenv(
        "AI_BASE_ALLOWLIST",
        ",".join(
            [
                # 国内主流
                "api.deepseek.com",                    # DeepSeek
                "dashscope.aliyuncs.com",              # 阿里百炼 Qwen
                "open.bigmodel.cn",                    # 智谱 GLM
                "api.moonshot.cn",                     # 月之暗面 Kimi
                "ark.cn-beijing.volces.com",           # 火山方舟 豆包
                "api.siliconflow.cn",                  # 硅基流动
                "spark-api-open.xf-yun.com",           # 讯飞星火
                "qianfan.baidubce.com",                # 百度千帆
                "api.stepfun.com",                     # 阶跃星辰
                "api.lingyiwanwu.com",                 # 零一万物 01.AI
                "api.baichuan-ai.com",                 # 百川智能
                "api.minimax.io",                      # MiniMax
                # 国际主流
                "api.openai.com",                      # OpenAI
                "api.anthropic.com",                   # Anthropic Claude
                "generativelanguage.googleapis.com",   # Google Gemini
                "api.mistral.ai",                      # Mistral
                "api.x.ai",                            # xAI Grok
                "api.groq.com",                        # Groq
                "api.together.xyz",                    # Together
                "api.fireworks.ai",                    # Fireworks
                "openrouter.ai",                       # OpenRouter 聚合
                "api.perplexity.ai",                   # Perplexity Sonar
                "api.cohere.com",                      # Cohere
            ]
        ),
    ).split(",")
    if d.strip()
]
AI_STRICT_BASE = os.getenv("AI_STRICT_BASE", "true").strip().lower() in ("1", "true", "yes", "on")


def ai_base_url_allowed(base_url: str) -> tuple:
    """校验 AI 服务 base_url 是否允许。返回 (ok: bool, reason: str)。"""
    from urllib.parse import urlparse
    if not base_url or not base_url.strip():
        return False, "AI_API_BASE_URL 未配置或无法解析"
    host = (urlparse(base_url.strip()).hostname or "").lower()
    if not host:
        return False, "无法解析 AI 服务地址"
    if not AI_STRICT_BASE:
        return True, ""
    # 拒绝纯 IP / 内网地址，防止 AI_API_KEY 被引导到不可信主机
    try:
        import ipaddress
        ipaddress.ip_address(host)
        return False, "AI 服务地址不允许使用纯 IP 地址"
    except ValueError:
        pass
    if host in ("localhost", "127.0.0.1") or host.endswith(".local") or host.endswith(".localhost"):
        return False, "AI 服务地址不允许使用内网地址"
    for d in AI_BASE_ALLOWLIST:
        if host == d or host.endswith("." + d):
            return True, ""
    return False, f"AI 服务域名 {host} 不在白名单 {AI_BASE_ALLOWLIST} 内"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]


def get_ai_config() -> dict:
    return {
        "api_key": AI_API_KEY,
        "api_base_url": AI_API_BASE_URL,
        "model": AI_MODEL,
    }


def update_ai_config(api_key: str, api_base_url: str, model: str) -> bool:
    global AI_API_KEY, AI_API_BASE_URL, AI_MODEL

    env_path = _get_env_path()
    try:
        lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        keys_found = {
            "AI_API_KEY": False,
            "AI_API_BASE_URL": False,
            "AI_MODEL": False,
        }

        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("AI_API_KEY="):
                new_lines.append(f"AI_API_KEY={api_key}\n")
                keys_found["AI_API_KEY"] = True
            elif stripped.startswith("AI_API_BASE_URL="):
                new_lines.append(f"AI_API_BASE_URL={api_base_url}\n")
                keys_found["AI_API_BASE_URL"] = True
            elif stripped.startswith("AI_MODEL="):
                new_lines.append(f"AI_MODEL={model}\n")
                keys_found["AI_MODEL"] = True
            else:
                new_lines.append(line)

        if not keys_found["AI_API_KEY"]:
            new_lines.append(f"AI_API_KEY={api_key}\n")
        if not keys_found["AI_API_BASE_URL"]:
            new_lines.append(f"AI_API_BASE_URL={api_base_url}\n")
        if not keys_found["AI_MODEL"]:
            new_lines.append(f"AI_MODEL={model}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        AI_API_KEY = api_key
        AI_API_BASE_URL = api_base_url
        AI_MODEL = model

        os.environ["AI_API_KEY"] = api_key
        os.environ["AI_API_BASE_URL"] = api_base_url
        os.environ["AI_MODEL"] = model

        return True
    except Exception as e:
        print(f"更新配置失败: {e}")
        return False

