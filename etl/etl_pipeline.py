import os
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from sqlalchemy import create_engine


@dataclass
class EtlConfig:
    source_csv: str
    chunksize: int = 200_000
    database_url: str = ""


def load_config() -> EtlConfig:
    source_csv = os.environ.get("SOURCE_CSV", "")
    database_url = os.environ.get("DATABASE_URL", "")
    chunksize = int(os.environ.get("CHUNKSIZE", "200000"))

    if not source_csv:
        raise ValueError("SOURCE_CSV is required")
    if not database_url:
        raise ValueError("DATABASE_URL is required")

    return EtlConfig(
        source_csv=source_csv, chunksize=chunksize, database_url=database_url
    )


def read_chunks(config: EtlConfig) -> Iterable[pd.DataFrame]:
    return pd.read_csv(
        config.source_csv,
        chunksize=config.chunksize,
        low_memory=False,
    )


def transform_chunk(df: pd.DataFrame) -> pd.DataFrame:
    # 数据清洗和类型转换
    # 1. 过滤空值
    df = df.dropna(subset=['user_id', 'product_id'])
    
    # 2. 时间戳转换
    df['event_time'] = pd.to_datetime(df['event_time'])
    
    # 3. 价格处理
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df[df['price'] > 0]
    
    # 4. 事件类型校验
    valid_event_types = ['view', 'cart', 'purchase']
    df = df[df['event_type'].isin(valid_event_types)]
    
    # 5. 类目解析
    def parse_category_code(code):
        if pd.isna(code):
            return ['unknown', 'unknown', 'unknown']
        parts = str(code).split('.')
        if len(parts) >= 3:
            return [parts[0], parts[1], parts[2]]
        elif len(parts) == 2:
            return [parts[0], parts[1], 'other']
        elif len(parts) == 1:
            return [parts[0], 'other', 'other']
        else:
            return ['unknown', 'unknown', 'unknown']
    
    # 6. 品牌处理
    df['brand'] = df['brand'].fillna('Unknown')
    
    # 7. 提取类目层级
    df[['category_l1', 'category_l2', 'category_l3']] = df['category_code'].apply(parse_category_code).apply(pd.Series)
    
    # 8. 计算time_key (YYYYMMDD格式)
    df['time_key'] = df['event_time'].dt.strftime('%Y%m%d').astype(int)
    
    # 9. 计算revenue
    df['revenue'] = df['price'] * 1
    
    return df


def load_chunk(df: pd.DataFrame, engine) -> None:
    # 写入临时表
    df.to_sql("staging_events", engine, if_exists="append", index=False)
    
    # 写入维度表和事实表的逻辑将在local_import.py中实现


def run() -> None:
    config = load_config()
    engine = create_engine(config.database_url)

    for chunk in read_chunks(config):
        cleaned = transform_chunk(chunk)
        load_chunk(cleaned, engine)


if __name__ == "__main__":
    run()
