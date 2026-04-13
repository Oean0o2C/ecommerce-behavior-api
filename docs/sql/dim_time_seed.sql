-- 用途：初始化时间维度（dim_time）
-- 使用阶段：Phase 1 数据入库前（schema.sql 之后执行）
-- 说明：作为备用生成方案；使用 ETL 导入 dim_time 时请勿执行本脚本。

INSERT INTO dim_time (
    time_key,
    date_actual,
    year,
    quarter,
    month,
    week,
    day_of_week,
    is_weekend,
    is_holiday
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS time_key,
    d::DATE AS date_actual,
    EXTRACT(YEAR FROM d)::SMALLINT AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT AS quarter,
    EXTRACT(MONTH FROM d)::SMALLINT AS month,
    EXTRACT(WEEK FROM d)::SMALLINT AS week,
    EXTRACT(DOW FROM d)::SMALLINT AS day_of_week,
    CASE WHEN EXTRACT(DOW FROM d) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
    FALSE AS is_holiday
FROM generate_series(
    DATE '2019-10-01',
    DATE '2019-11-30',
    INTERVAL '1 day'
) AS d;
