from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL


# 创建数据库引擎
# SQLite 需要添加 check_same_thread=False 以支持多线程
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据库模型基类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    # 兼容旧库：favorites 表新增 tags 列
    # create_all 只会建"新表"，不会给已存在的表加列，需手动 ALTER TABLE（幂等）
    with engine.begin() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(favorites)")).fetchall()]
        # cols 非空说明表已存在；缺 tags 列则补
        if cols and "tags" not in cols:
            conn.execute(text("ALTER TABLE favorites ADD COLUMN tags VARCHAR(500) DEFAULT ''"))
