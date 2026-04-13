from sqlalchemy import func, text
from ..database import SessionLocal
from ..models.models import FactUserBehavior, DimProducts

# 添加内存缓存
products_cache = {}

class ProductsRepository:
    def get_top_products(self, metric: str, limit: int, start_date, end_date):
        """获取热销商品数据"""
        # 转换日期为time_key格式 (YYYYMMDD)
        start_time_key = int(start_date.strftime('%Y%m%d')) if start_date else None
        end_time_key = int(end_date.strftime('%Y%m%d')) if end_date else None
        
        # 检查缓存
        cache_key = f"products_{metric}_{limit}_{start_time_key}_{end_time_key}"
        if cache_key in products_cache:
            return products_cache[cache_key]
        
        db = SessionLocal()
        try:
            # 构建时间范围条件
            time_condition = ""
            if start_time_key and end_time_key:
                time_condition = f"AND f.time_key >= {start_time_key} AND f.time_key <= {end_time_key}"
            
            # 根据指标选择排序字段和查询语句
            if metric == 'sales':
                # 使用直接SQL查询提高性能
                results = db.execute(
                    text(f"""
                    SELECT 
                        d.product_id,
                        d.brand,
                        d.category_l1 || '.' || d.category_l2 as category,
                        SUM(f.revenue) as metric_value
                    FROM 
                        fact_user_behavior f
                    JOIN 
                        dim_products d ON f.product_id = d.product_id
                    WHERE 
                        f.event_type = 'purchase'
                        {time_condition}
                    GROUP BY 
                        d.product_id, d.brand, d.category_l1, d.category_l2
                    ORDER BY 
                        metric_value DESC
                    LIMIT :limit
                    """),
                    {"limit": limit}
                ).all()
            elif metric == 'views':
                # 使用直接SQL查询提高性能
                results = db.execute(
                    text(f"""
                    SELECT 
                        d.product_id,
                        d.brand,
                        d.category_l1 || '.' || d.category_l2 as category,
                        COUNT(f.event_id) as metric_value
                    FROM 
                        fact_user_behavior f
                    JOIN 
                        dim_products d ON f.product_id = d.product_id
                    WHERE 
                        f.event_type = 'view'
                        {time_condition}
                    GROUP BY 
                        d.product_id, d.brand, d.category_l1, d.category_l2
                    ORDER BY 
                        metric_value DESC
                    LIMIT :limit
                    """),
                    {"limit": limit}
                ).all()
            elif metric == 'carts':
                # 使用直接SQL查询提高性能
                results = db.execute(
                    text(f"""
                    SELECT 
                        d.product_id,
                        d.brand,
                        d.category_l1 || '.' || d.category_l2 as category,
                        COUNT(f.event_id) as metric_value
                    FROM 
                        fact_user_behavior f
                    JOIN 
                        dim_products d ON f.product_id = d.product_id
                    WHERE 
                        f.event_type = 'cart'
                        {time_condition}
                    GROUP BY 
                        d.product_id, d.brand, d.category_l1, d.category_l2
                    ORDER BY 
                        metric_value DESC
                    LIMIT :limit
                    """),
                    {"limit": limit}
                ).all()
            else:
                # 默认查询销售额
                results = db.execute(
                    text(f"""
                    SELECT 
                        d.product_id,
                        d.brand,
                        d.category_l1 || '.' || d.category_l2 as category,
                        SUM(f.revenue) as metric_value
                    FROM 
                        fact_user_behavior f
                    JOIN 
                        dim_products d ON f.product_id = d.product_id
                    WHERE 
                        f.event_type = 'purchase'
                        {time_condition}
                    GROUP BY 
                        d.product_id, d.brand, d.category_l1, d.category_l2
                    ORDER BY 
                        metric_value DESC
                    LIMIT :limit
                    """),
                    {"limit": limit}
                ).all()
            
            # 格式化结果
            products = []
            for result in results:
                products.append({
                    "product_id": result.product_id,
                    "name": f"{result.brand} Product",  # 实际项目中应该有商品名称字段
                    "category": result.category,
                    "metric_value": float(result.metric_value) if result.metric_value else 0
                })
            
            # 存储到缓存
            products_cache[cache_key] = products
            return products
        finally:
            db.close()
