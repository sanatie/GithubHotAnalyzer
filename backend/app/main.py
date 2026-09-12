from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import engine, init_db
from app.api.analysis import router as analysis_router
from app.api.repositories import router as repositories_router
from app.api.favorites import router as favorites_router
from app.api.settings import router as settings_router
from app.api.trending import router as trending_router
from app.api.chat import router as chat_router
from app.api.chat_history import router as chat_history_router
from app.api.downloader import router as downloader_router
# 确保模型被导入以注册到数据库元数据
import app.models.chat_history  # noqa: F401
import app.models.download_task  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库，关闭时清理资源"""
    # 启动时：创建数据库表
    init_db()
    yield
    # 关闭时：关闭数据库连接池
    engine.dispose()
    print("数据库连接已关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title="GitHub 热榜项目分析器 API",
    description="AI 驱动的 GitHub 项目分析工具，输入仓库地址自动生成中文分析报告",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 注册路由 ----------
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(repositories_router, prefix="/api/v1/repositories", tags=["Repositories"])
app.include_router(favorites_router, prefix="/api/v1/favorites", tags=["Favorites"])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(trending_router, prefix="/api/v1/trending", tags=["Trending"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(chat_history_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(downloader_router, prefix="/api/v1/download", tags=["Download"])


@app.get("/api/v1/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "服务运行正常"}


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
