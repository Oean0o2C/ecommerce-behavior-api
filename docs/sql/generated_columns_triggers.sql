-- 用途：为 revenue 与 price_range 提供自动计算逻辑
-- 使用阶段：Phase 1 数据导入前或导入后（schema.sql 之后执行）
-- 说明：revenue 由 price * quantity 计算；price_range 按价格分段。

-- 计算 revenue
CREATE OR REPLACE FUNCTION set_fact_revenue()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.quantity IS NULL THEN
        NEW.quantity := 1;
    END IF;

    NEW.revenue := NEW.price * NEW.quantity;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_fact_revenue ON fact_user_behavior;
CREATE TRIGGER trg_fact_revenue
BEFORE INSERT OR UPDATE OF price, quantity
ON fact_user_behavior
FOR EACH ROW
EXECUTE FUNCTION set_fact_revenue();

-- 计算 price_range
CREATE OR REPLACE FUNCTION set_product_price_range()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.price_range IS NOT NULL THEN
        RETURN NEW;
    END IF;

    IF NEW.price < 50 THEN
        NEW.price_range := 'low';
    ELSIF NEW.price < 200 THEN
        NEW.price_range := 'mid';
    ELSE
        NEW.price_range := 'high';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_product_price_range ON dim_products;
CREATE TRIGGER trg_product_price_range
BEFORE INSERT OR UPDATE OF price_range
ON dim_products
FOR EACH ROW
EXECUTE FUNCTION set_product_price_range();
