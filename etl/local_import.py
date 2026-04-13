"""
将 Parquet 批量导入 PostgreSQL（Supabase 与其它托管库通用）。

- 使用同步 SQLAlchemy + pandas；`.env` 若为 FastAPI 准备的 `postgresql+asyncpg://`
  会自动换成 `postgresql+psycopg://` 再建引擎。
- Supabase Session pooler（端口 5432）与本脚本的多段事务兼容；连接串建议带
  `?sslmode=require`。
"""
import argparse
import math
import os
import time
from pathlib import Path
from typing import Iterable

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import make_url
from tqdm import tqdm

try:
    import pyarrow.parquet as pq
except Exception:
    pq = None


def iter_parquet_batches(path: Path, batch_size: int) -> Iterable[pd.DataFrame]:
    if pq is None:
        yield pd.read_parquet(path)
        return

    parquet_file = pq.ParquetFile(path)
    for batch in parquet_file.iter_batches(batch_size=batch_size):
        yield batch.to_pandas()


def get_parquet_rows(path: Path) -> int:
    if pq is not None:
        return pq.ParquetFile(path).metadata.num_rows
    return len(pd.read_parquet(path))


def sync_engine_database_url(url: str) -> str:
    """将异步驱动 URL 转为同步 psycopg3，供 `create_engine` + `to_sql` 使用。"""
    u = url.strip()
    if u.startswith("postgresql+asyncpg://"):
        return u.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return u


def truncate_star_schema_tables(engine) -> None:
    """清空星型模型四张表并重置自增序列（与 project_decisions 中单条 CASCADE 一致）。"""
    sql = (
        "TRUNCATE TABLE fact_user_behavior, dim_users, dim_products, dim_time "
        "RESTART IDENTITY CASCADE"
    )
    with engine.begin() as conn:
        conn.execute(text(sql))


def prepare_dim_products(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = df.sort_values("product_key").reset_index(drop=True)
    dedup = df.drop_duplicates(subset=["product_id"], keep="first").copy()
    return dedup


def write_in_chunks(df: pd.DataFrame, table: str, engine, chunksize: int) -> None:
    safe_chunksize = max(1, min(chunksize, 2000))
    df.to_sql(
        name=table,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=safe_chunksize,
    )


def write_in_chunks_on_conflict(
    df: pd.DataFrame,
    table: str,
    conflict_cols: list[str],
    engine,
    chunksize: int,
) -> None:
    if df.empty:
        return

    metadata = MetaData()
    target = Table(table, metadata, autoload_with=engine)
    safe_chunksize = max(1, min(chunksize, 2000))

    for start in range(0, len(df), safe_chunksize):
        records = df.iloc[start : start + safe_chunksize].to_dict(orient="records")
        stmt = insert(target).values(records)
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
        with engine.begin() as conn:
            conn.execute(stmt)


def get_max_time_key(engine, table: str) -> int | None:
    metadata = MetaData()
    target = Table(table, metadata, autoload_with=engine)
    stmt = select(func.max(target.c.time_key))
    with engine.connect() as conn:
        result = conn.execute(stmt).scalar()
    return int(result) if result is not None else None


def load_table(
    path: Path,
    table: str,
    engine,
    batch_size: int,
    chunksize: int,
    global_bar: tqdm,
    bar_position: int,
    incremental: bool,
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing parquet file: {path}")

    total_rows_expected = get_parquet_rows(path)
    total_batches = max(1, math.ceil(total_rows_expected / batch_size))

    total_rows = 0
    start_time = time.perf_counter()
    batch_iter = tqdm(
        iter_parquet_batches(path, batch_size=batch_size),
        total=total_batches,
        desc=f"📊 {table}",
        unit="batch",
        position=bar_position,
        leave=False,
        ncols=110,
        colour="#4e79a7",
        mininterval=0.5,
    )

    for df in batch_iter:
        if table == "dim_time":
            if "week" not in df.columns or df["week"].isna().any():
                df["date_actual"] = pd.to_datetime(df["date_actual"]).dt.date
                df["week"] = (
                    pd.to_datetime(df["date_actual"]).dt.isocalendar().week.astype(int)
                )

        batch_rows = len(df)
        if incremental and table == "dim_time":
            write_in_chunks_on_conflict(
                df,
                table,
                conflict_cols=["time_key"],
                engine=engine,
                chunksize=chunksize,
            )
        elif incremental and table == "dim_users":
            write_in_chunks_on_conflict(
                df,
                table,
                conflict_cols=["user_id"],
                engine=engine,
                chunksize=chunksize,
            )
        elif incremental and table == "dim_products":
            write_in_chunks_on_conflict(
                df,
                table,
                conflict_cols=["product_id"],
                engine=engine,
                chunksize=chunksize,
            )
        else:
            write_in_chunks(df, table, engine, chunksize=chunksize)
        total_rows += batch_rows
        global_bar.update(batch_rows)

        elapsed = time.perf_counter() - start_time
        batch_iter.set_postfix(
            rows=f"{batch_rows:,}",
            loaded=f"{total_rows:,}",
            rate=f"{(total_rows / elapsed):.0f}/s",
        )

    batch_iter.close()
    print(
        f"[{table}] 完成 | 总行数：{total_rows:,} | 耗时：{time.perf_counter() - start_time:.1f}s"
    )


def load_dataframe_table(
    df: pd.DataFrame,
    table: str,
    engine,
    chunksize: int,
    global_bar: tqdm,
    bar_position: int,
    incremental: bool,
    conflict_cols: list[str] | None,
) -> None:
    if df.empty:
        print(f"[{table}] 完成 | 总行数：0 | 耗时：0.0s")
        return

    total_rows = 0
    start_time = time.perf_counter()
    total_batches = max(1, math.ceil(len(df) / chunksize))

    batch_iter = tqdm(
        range(0, len(df), chunksize),
        total=total_batches,
        desc=f"📊 {table}",
        unit="batch",
        position=bar_position,
        leave=False,
        ncols=110,
        colour="#4e79a7",
        mininterval=0.5,
    )

    for start in batch_iter:
        chunk = df.iloc[start : start + chunksize]
        batch_rows = len(chunk)
        if incremental and conflict_cols:
            write_in_chunks_on_conflict(
                chunk,
                table,
                conflict_cols=conflict_cols,
                engine=engine,
                chunksize=chunksize,
            )
        else:
            write_in_chunks(chunk, table, engine, chunksize=chunksize)

        total_rows += batch_rows
        global_bar.update(batch_rows)

        elapsed = time.perf_counter() - start_time
        batch_iter.set_postfix(
            rows=f"{batch_rows:,}",
            loaded=f"{total_rows:,}",
            rate=f"{(total_rows / elapsed):.0f}/s",
        )

    batch_iter.close()
    print(
        f"[{table}] 完成 | 总行数：{total_rows:,} | 耗时：{time.perf_counter() - start_time:.1f}s"
    )


def load_fact_parts(
    parts_dir: Path,
    table: str,
    engine,
    batch_size: int,
    chunksize: int,
    global_bar: tqdm,
    file_bar_position: int,
    batch_bar_position: int,
    incremental: bool,
    max_fact_time_key: int | None,
    quiet: bool,
) -> None:
    if not parts_dir.exists():
        raise FileNotFoundError(f"Missing fact directory: {parts_dir}")

    part_files = sorted(parts_dir.glob("fact_user_behavior_*.parquet"))
    if not part_files:
        raise FileNotFoundError("No fact files found")

    total_rows = 0
    start_time = time.perf_counter()
    last_file_update = start_time

    file_iter = tqdm(
        part_files,
        total=len(part_files),
        desc=f"📂 {table}",
        unit="file",
        position=file_bar_position,
        leave=False,
        ncols=110,
        colour="#59a14f",
        mininterval=0.5,
        disable=False,
    )

    validated = False

    for path in file_iter:
        file_rows = 0
        file_total_rows = get_parquet_rows(path)
        file_total_batches = max(1, math.ceil(file_total_rows / batch_size))

        batch_iter = tqdm(
            iter_parquet_batches(path, batch_size=batch_size),
            total=file_total_batches,
            desc=f"   └─ 批次",
            unit="batch",
            position=batch_bar_position,
            leave=False,
            ncols=110,
            colour="#f28e2b",
            mininterval=0.5,
            disable=False,
        )

        for df in batch_iter:
            if not validated:
                required_cols = {"time_key", "user_id", "product_id"}
                missing = required_cols - set(df.columns)
                if missing:
                    legacy_cols = {"user_key", "product_key"}
                    if legacy_cols.issubset(df.columns):
                        raise ValueError(
                            "fact parquet uses legacy surrogate keys; "
                            "regenerate outputs with user_id/product_id."
                        )
                    raise ValueError(
                        f"fact parquet missing required columns: {sorted(missing)}"
                    )
                validated = True

            # Do not filter by max(time_key); rely on unique key conflict handling.
            original_rows = len(df)
            df = df.drop_duplicates(
                subset=[
                    "user_id",
                    "product_id",
                    "time_key",
                    "event_type",
                    "user_session",
                ]
            )
            if df.empty:
                global_bar.update(original_rows)
                continue
            batch_rows = len(df)
            write_in_chunks_on_conflict(
                df,
                table,
                conflict_cols=[
                    "user_id",
                    "product_id",
                    "time_key",
                    "event_type",
                    "user_session",
                ],
                engine=engine,
                chunksize=chunksize,
            )
            file_rows += original_rows
            total_rows += original_rows
            global_bar.update(original_rows)

        batch_iter.close()
        now = time.perf_counter()
        if now - last_file_update >= 2:
            file_iter.set_postfix(file=path.name[:25], rows=f"{file_rows:,}")
            last_file_update = now

    file_iter.close()
    print(
        f"[{table}] 完成 | 总行数：{total_rows:,} | 耗时：{time.perf_counter() - start_time:.1f}s"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL 导入工具（全进度条 + 防刷屏）")
    parser.add_argument(
        "--data-dir",
        default="data/processed/kaggle_outputs/outputs",
        help="Parquet 目录（outputs_7d_sample10）",
    )
    parser.add_argument(
        "--batch-size", type=int, default=200_000, help="Parquet 读取批次"
    )
    parser.add_argument("--chunksize", type=int, default=2000, help="插入批次")
    parser.add_argument("--truncate", action="store_true", help="清空表")
    parser.add_argument("--incremental", action="store_true", help="增量导入")
    parser.add_argument("--only-fact", action="store_true", help="仅导入事实表")
    parser.add_argument("--quiet", action="store_true", help="减少进度输出")
    args = parser.parse_args()

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("请配置 DATABASE_URL")

    sync_url = sync_engine_database_url(database_url)
    db_url = make_url(sync_url)
    print(
        f"连接目标：{db_url.host}:{db_url.port or 'default'} | 数据库：{db_url.database}"
    )

    data_dir = Path(args.data_dir)
    dim_time_path = data_dir / "dim_time.parquet"
    dim_users_path = data_dir / "dim_users.parquet"
    dim_products_path = data_dir / "dim_products.parquet"
    fact_parts_dir = data_dir / "fact_user_behavior_parts"

    connect_timeout = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "30"))
    engine = create_engine(
        sync_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=2,
        max_overflow=3,
        connect_args={"connect_timeout": connect_timeout},
    )

    if args.truncate:
        print("执行 TRUNCATE（清空 fact + 维表，RESTART IDENTITY CASCADE）…")
        truncate_star_schema_tables(engine)

    if args.incremental:
        print("启用增量导入。")

    dim_products_df = None
    if not args.only_fact:
        dim_products_df = prepare_dim_products(dim_products_path)

    fact_rows = sum(
        get_parquet_rows(p) for p in fact_parts_dir.glob("fact_user_behavior_*.parquet")
    )

    if args.only_fact:
        total_rows = fact_rows
    else:
        total_rows = sum(
            [
                get_parquet_rows(dim_time_path),
                get_parquet_rows(dim_users_path),
                len(dim_products_df),
                fact_rows,
            ]
        )

    max_fact_time_key = None
    if args.incremental:
        max_fact_time_key = get_max_time_key(engine, "fact_user_behavior")

    try:
        with tqdm(
            total=total_rows,
            desc="总导入进度",
            unit="row",
            position=0,
            leave=True,
            ncols=110,
            colour="#9c755f",
            mininterval=2.0,
            disable=False,
        ) as global_bar:

            if not args.only_fact:
                load_table(
                    dim_time_path,
                    "dim_time",
                    engine,
                    args.batch_size,
                    args.chunksize,
                    global_bar,
                    bar_position=1,
                    incremental=args.incremental,
                )
                load_table(
                    dim_users_path,
                    "dim_users",
                    engine,
                    args.batch_size,
                    args.chunksize,
                    global_bar,
                    bar_position=1,
                    incremental=args.incremental,
                )
                load_dataframe_table(
                    dim_products_df,
                    "dim_products",
                    engine,
                    args.chunksize,
                    global_bar,
                    bar_position=1,
                    incremental=args.incremental,
                    conflict_cols=["product_id"],
                )
            load_fact_parts(
                fact_parts_dir,
                "fact_user_behavior",
                engine,
                args.batch_size,
                args.chunksize,
                global_bar,
                1,
                2,
                incremental=args.incremental,
                max_fact_time_key=max_fact_time_key,
                quiet=args.quiet,
            )

    except Exception as exc:
        print("\n导入失败")
        print(f"错误：{type(exc).__name__} | {str(exc).splitlines()[0]}")
        return

    print("\n所有数据导入完成！")


if __name__ == "__main__":
    main()
