from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 获取数据库连接字符串
DATABASE_URL = os.getenv("DATABASE_URL", "")

# 转换异步驱动URL为同步驱动URL
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

# 创建数据库引擎，优化连接池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接池预ping，确保连接有效
    pool_recycle=3600,  # 连接回收时间（秒）
    echo=False  # 关闭SQL日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 依赖注入函数，用于获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 测试数据库连接
def test_db_connection():
    import time
    start_time = time.time()
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        print(f"Database connection successful, took {time.time() - start_time:.2f} seconds")
        return True
    except Exception as e:
        print(f"Database connection error: {e}, took {time.time() - start_time:.2f} seconds")
        return False
