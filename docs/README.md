# 文档说明

本目录存放项目文档与设计记录。

关键文件：
- environment_setup.md：本地环境配置与运行步骤。
- project_decisions_and_issues.md：关键决策与问题复盘。
- sql/：数据库建表与索引脚本（含触发器与维度初始化）。

**生产库（Supabase）**：在 **SQL Editor** 中按下列顺序**完整执行**脚本（含 `schema.sql` 内全部表与物化视图），再导入数据、刷新物化视图（见 `etl/README.md`）。

SQL 脚本用途：
- sql/schema.sql：创建核心表与物化视图。
- sql/indexes_constraints.sql：添加索引与数据质量约束。
- sql/generated_columns_triggers.sql：为 revenue 与 price_range 提供自动计算逻辑。
- sql/dim_time_seed.sql：备用生成 dim_time（与 ETL 导入二选一）。

执行顺序（默认由 ETL 导入 `dim_time` 时）：
1) sql/schema.sql
2) sql/generated_columns_triggers.sql
3) sql/indexes_constraints.sql  

若不用 ETL 生成 `dim_time.parquet`，再用 sql/dim_time_seed.sql 生成时间维（与上一步二选一，勿重复灌入冲突数据）。

适用阶段：
- Phase 1 建表：schema.sql → generated_columns_triggers.sql → indexes_constraints.sql
- dim_time_seed.sql：仅在不走 ETL 导入 dim_time 时使用

目录结构：
```
docs/
	README.md
	environment_setup.md
	project_decisions_and_issues.md
	sql/
		dim_time_seed.sql
		generated_columns_triggers.sql
		indexes_constraints.sql
		schema.sql
```
