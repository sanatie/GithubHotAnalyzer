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

