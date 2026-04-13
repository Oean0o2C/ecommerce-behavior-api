# ETL 说明

本目录包含 Kaggle 数据集的 ETL Notebook 与导入脚本。

关键文件：
- kaggle_etl.ipynb：Kaggle 端分块 ETL，输出 Parquet。
- local_import.py：将 Parquet 导入 Supabase/PostgreSQL。

典型流程：
1) 在 Kaggle 运行 kaggle_etl.ipynb 生成输出。
2) 下载输出到 `data/processed/kaggle_outputs/outputs/`（或你生成的目录，如 `outputs_7d_sample10/`）。
3) 执行：python local_import.py --truncate

目录结构：
```
etl/
	README.md
	etl_pipeline.py
	kaggle_etl.ipynb
	local_import.py
```

---
## Kaggle 输出与本地导入

Kaggle 产出文件放在：

```
data/processed/kaggle_outputs/outputs/
```

目录内应包含：

- dim_time.parquet
- dim_users.parquet
- dim_products.parquet
- user_daily_features.parquet
- fact_user_behavior_parts/

导入示例（全量目录）：

```
python local_import.py --data-dir data/processed/kaggle_outputs/outputs --truncate
```

### 导入到 Supabase（Session pooler）

1. 在 Supabase **SQL Editor** 中按 `docs/README.md` 顺序**完整执行** `docs/sql/`：先 **`schema.sql`**（含 `mv_daily_sales`、`mv_category_stats`、`mv_user_rfm` 三个物化视图），再 **`generated_columns_triggers.sql`**，最后 **`indexes_constraints.sql`**。`dim_time_seed.sql` 仅在不用 ETL 导入 `dim_time` 时使用。
2. 在项目根目录 `.env` 配置 `DATABASE_URL`：**Session pooler**（`*.pooler.supabase.com:5432`）+ `sslmode=require`；FastAPI 用 `postgresql+asyncpg://`。`local_import.py` 会把 `postgresql+asyncpg://` 自动换成 `postgresql+psycopg://`。
3. `pip install -r requirements.txt`
4. 在仓库根目录执行（示例为 7 天 + 10% 抽样目录）：

```
python etl/local_import.py --data-dir data/processed/kaggle_outputs/outputs_7d_sample10 --truncate
```

- **首次导入或整表重导**：`--truncate`（脚本内会 `TRUNCATE ... RESTART IDENTITY CASCADE` 四张星型表）。
- **增量追加、依赖 `ON CONFLICT DO NOTHING`，且维表与事实表键已对齐**：`--incremental`。
5. 刷新物化视图（与 `schema.sql` 中三个 MV 一一对应）：在 **SQL Editor** 执行：

```sql
REFRESH MATERIALIZED VIEW mv_daily_sales;
REFRESH MATERIALIZED VIEW mv_category_stats;
REFRESH MATERIALIZED VIEW mv_user_rfm;
```

默认使用上述非 `CONCURRENTLY` 形式；只有已为某物化视图建立**唯一索引**并需在线刷新时，再对该视图使用 `REFRESH MATERIALIZED VIEW CONCURRENTLY ...`（见 PostgreSQL 文档）。

网络较慢时设置 `DATABASE_CONNECT_TIMEOUT`（秒，默认 30）。