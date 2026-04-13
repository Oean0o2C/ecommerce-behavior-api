from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 获取数据库连接字符串
DATABASE_URL = os.getenv("DATABASE_URL", "")

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 读取schema.sql文件
with open("../../docs/sql/schema.sql", "r", encoding="utf-8") as f:
    schema_sql = f.read()

# 执行SQL语句
with engine.begin() as conn:
    conn.execute(text(schema_sql))

print("数据库表结构创建完成！")
