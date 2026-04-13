-- 用途：创建核心表与物化视图
-- 使用阶段：Phase 1 建模与建表（先执行本文件）
-- 说明：仅创建表与物化视图，不包含索引与触发器。
-- 生产库：在 Supabase 中与 docs/README.md 约定一致，须完整执行本文件（含 mv_daily_sales、mv_category_stats、mv_user_rfm）。

-- 星型模型结构：维度表 dim_time、dim_users、dim_products + 事实表 fact_user_behavior，用于支持 OLAP 指标查询。

-- 时间维度表：包含日期、年、季度、月、周、工作日/周末、节假日等信息
CREATE TABLE IF NOT EXISTS dim_time (
    time_key INTEGER PRIMARY KEY,
    date_actual DATE NOT NULL,
    year SMALLINT NOT NULL,
    quarter SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    week SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE
);

-- 用户维度表：包含用户注册时间、活跃时间、用户分群等信息
CREATE TABLE IF NOT EXISTS dim_users (
    user_key SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    first_seen_date DATE NOT NULL,
    last_seen_date DATE NOT NULL,
    user_segment VARCHAR(20) DEFAULT 'new',
    region VARCHAR(50) DEFAULT 'unknown',
    device_type VARCHAR(20) DEFAULT 'desktop'
);

-- 商品维度表：包含产品分类和品牌信息
CREATE TABLE IF NOT EXISTS dim_products (
    product_key SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE NOT NULL,
    category_id BIGINT NOT NULL,
    category_l1 VARCHAR(50) NOT NULL,
    category_l2 VARCHAR(50) NOT NULL,
    category_l3 VARCHAR(50) DEFAULT 'other',
    brand VARCHAR(50) DEFAULT 'Unknown',
    price_range VARCHAR(20)
);

-- 用户行为事实表：记录每次事件的时间、用户、产品、事件类型、价格、数量等信息
CREATE TABLE IF NOT EXISTS fact_user_behavior (
    event_id BIGSERIAL PRIMARY KEY,
    time_key INTEGER NOT NULL REFERENCES dim_time(time_key),
    user_id INTEGER NOT NULL REFERENCES dim_users(user_id),
    product_id INTEGER NOT NULL REFERENCES dim_products(product_id),
    event_type VARCHAR(20) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    quantity SMALLINT DEFAULT 1,
    revenue DECIMAL(12, 2),
    user_session VARCHAR(50) NOT NULL
);

-- 说明：revenue 与 price_range 由触发器维护，保持字段物化以便查询。

-- 物化视图
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_sales AS -- 每日销售统计，包含 UV、PV、订单数、GMV、AOV 等指标
SELECT 
    t.date_actual,
    COUNT(DISTINCT f.user_id) AS uv,
    COUNT(*) AS pv,
    COUNT(*) FILTER (WHERE f.event_type = 'purchase') AS order_count,
    SUM(f.revenue) FILTER (WHERE f.event_type = 'purchase') AS gmv,
    AVG(f.revenue) FILTER (WHERE f.event_type = 'purchase') AS avg_order_value
FROM fact_user_behavior f
JOIN dim_time t ON f.time_key = t.time_key
GROUP BY t.date_actual;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_category_stats AS -- 产品分类统计，包含浏览量、加购量、购买量、GMV 等指标
SELECT 
    p.category_l1,
    p.category_l2,
    COUNT(*) AS view_count,
    COUNT(*) FILTER (WHERE f.event_type = 'cart') AS cart_count,
    COUNT(*) FILTER (WHERE f.event_type = 'purchase') AS purchase_count,
    SUM(f.revenue) AS gmv
FROM fact_user_behavior f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.category_l1, p.category_l2;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_rfm AS -- 用户 RFM 评分，包含最近一次购买时间、购买频率、购买金额等信息
WITH user_stats AS (
    SELECT 
        user_id,
        MAX(t.date_actual) AS last_purchase_date,
        COUNT(*) FILTER (WHERE event_type = 'purchase') AS frequency,
        SUM(revenue) FILTER (WHERE event_type = 'purchase') AS monetary
    FROM fact_user_behavior f
    JOIN dim_time t ON f.time_key = t.time_key
    WHERE f.event_type = 'purchase'
    GROUP BY user_id
)
SELECT 
    user_id,
    CURRENT_DATE - last_purchase_date AS recency,
    frequency,
    monetary,
    NTILE(5) OVER (ORDER BY CURRENT_DATE - last_purchase_date) AS r_score,
    NTILE(5) OVER (ORDER BY frequency DESC) AS f_score,
    NTILE(5) OVER (ORDER BY monetary DESC) AS m_score
FROM user_stats;
