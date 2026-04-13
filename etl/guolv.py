from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parents[1]
src = project_root / "data/processed/kaggle_outputs/outputs"
dst = project_root / "data/processed/kaggle_outputs/outputs_7d_sample10"
fact_src = src / "fact_user_behavior_parts"
fact_dst = dst / "fact_user_behavior_parts"
fact_dst.mkdir(parents=True, exist_ok=True)

start_key = 20191001
end_key = 20191007

user_ids = set()
product_ids = set()
time_keys = set()

# 过滤事实表分片 + 抽样用户（10%）
for p in sorted(fact_src.glob("fact_user_behavior_*.parquet")):
    df = pd.read_parquet(
        p,
        columns=[
            "time_key",
            "user_id",
            "product_id",
            "event_type",
            "price",
            "user_session",
            "quantity",
            "revenue",
        ],
    )
    df = df[(df["time_key"] >= start_key) & (df["time_key"] <= end_key)]
    if df.empty:
        continue

    # 抽样用户：保留 10%
    df = df[df["user_id"] % 10 == 0]
    if df.empty:
        continue

    user_ids.update(df["user_id"].dropna().astype(int).tolist())
    product_ids.update(df["product_id"].dropna().astype(int).tolist())
    time_keys.update(df["time_key"].dropna().astype(int).tolist())

    out_path = fact_dst / p.name
    df.to_parquet(out_path, index=False)
    print("saved:", out_path.name, len(df))

# 过滤 dim_users
dim_users = pd.read_parquet(src / "dim_users.parquet")
dim_users = dim_users[dim_users["user_id"].isin(user_ids)]
dim_users.to_parquet(dst / "dim_users.parquet", index=False)

# 过滤 dim_products
dim_products = pd.read_parquet(src / "dim_products.parquet")
dim_products = dim_products[dim_products["product_id"].isin(product_ids)]
dim_products.to_parquet(dst / "dim_products.parquet", index=False)

# 过滤 dim_time（只保留 7 天）
dim_time = pd.read_parquet(src / "dim_time.parquet")
dim_time = dim_time[dim_time["time_key"].isin(time_keys)]
dim_time.to_parquet(dst / "dim_time.parquet", index=False)
