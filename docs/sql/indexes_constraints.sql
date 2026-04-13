-- 用途：添加索引与数据质量约束
-- 使用阶段：Phase 1 数据导入后（schema.sql 之后执行）
-- 说明：在 schema.sql 之后执行，每个环境只需执行一次。

-- 事实表索引：常用筛选与关联字段
CREATE INDEX IF NOT EXISTS idx_fact_time_key ON fact_user_behavior (time_key);
CREATE INDEX IF NOT EXISTS idx_fact_event_type ON fact_user_behavior (event_type);
CREATE INDEX IF NOT EXISTS idx_fact_user_id ON fact_user_behavior (user_id);
CREATE INDEX IF NOT EXISTS idx_fact_product_id ON fact_user_behavior (product_id);
CREATE INDEX IF NOT EXISTS idx_fact_time_event ON fact_user_behavior (time_key, event_type);

-- 维表索引：自然键检索
CREATE INDEX IF NOT EXISTS idx_dim_users_user_id ON dim_users (user_id);
CREATE INDEX IF NOT EXISTS idx_dim_products_product_id ON dim_products (product_id);

-- 物化视图索引：提升刷新与查询性能
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_sales_date ON mv_daily_sales (date_actual);
CREATE INDEX IF NOT EXISTS idx_mv_category_stats_l1_l2 ON mv_category_stats (category_l1, category_l2);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_user_rfm_user_id ON mv_user_rfm (user_id);

-- 数据质量约束：仅需执行一次，历史数据冲突时需评估后再加
ALTER TABLE fact_user_behavior
    ADD CONSTRAINT chk_fact_event_type
    CHECK (event_type IN ('view', 'cart', 'purchase'));

ALTER TABLE fact_user_behavior
    ADD CONSTRAINT uniq_fact_dedupe_key
    UNIQUE (user_id, product_id, time_key, event_type, user_session);

ALTER TABLE fact_user_behavior
    ADD CONSTRAINT chk_fact_price_non_negative
    CHECK (price >= 0);

ALTER TABLE fact_user_behavior
    ADD CONSTRAINT chk_fact_quantity_positive
    CHECK (quantity >= 1);

ALTER TABLE fact_user_behavior
    ADD CONSTRAINT chk_fact_revenue_non_negative
    CHECK (revenue IS NULL OR revenue >= 0);
