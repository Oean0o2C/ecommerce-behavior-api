from sqlalchemy import func, text
from ..database import SessionLocal
from ..models.models import FactUserBehavior, DimProducts

# 添加内存缓存
category_cache = {}

class CategoryRepository:
    def get_category_performance(self, category_level: str, limit: int, start_date, end_date):
        """获取品类表现数据"""
        # 转换日期为time_key格式 (YYYYMMDD)
        start_time_key = int(start_date.strftime('%Y%m%d')) if start_date else None
        end_time_key = int(end_date.strftime('%Y%m%d')) if end_date else None
        
        # 检查缓存
        cache_key = f"category_{category_level}_{limit}_{start_time_key}_{end_time_key}"
        if cache_key in category_cache:
            return category_cache[cache_key]
        
        db = SessionLocal()
        try:
            # 构建查询条件
            query = db.query(
                func.sum(FactUserBehavior.revenue)
            ).filter(
                FactUserBehavior.event_type == 'purchase'
            )
            
            # 添加时间范围过滤
            if start_time_key and end_time_key:
                query = query.filter(
                    FactUserBehavior.time_key >= start_time_key,
                    FactUserBehavior.time_key <= end_time_key
                )
            
            # 获取总GMV
            total_gmv = query.scalar()
            total_gmv = float(total_gmv) if total_gmv else 0
            
            # 根据类目层级执行不同的查询
            if category_level == 'l1':
                # L1 层级查询
                query = db.query(
                    DimProducts.category_l1.label('name'),
                    func.sum(FactUserBehavior.revenue).label('gmv')
                ).join(
                    DimProducts, FactUserBehavior.product_id == DimProducts.product_id
                ).filter(
                    FactUserBehavior.event_type == 'purchase'
                )
                
                # 添加时间范围过滤
                if start_time_key and end_time_key:
                    query = query.filter(
                        FactUserBehavior.time_key >= start_time_key,
                        FactUserBehavior.time_key <= end_time_key
                    )
                
                results = query.group_by(
                    DimProducts.category_l1
                ).order_by(
                    func.sum(FactUserBehavior.revenue).desc()
                ).limit(
                    limit
                ).all()
            elif category_level == 'l2':
                # L2 层级查询
                query = db.query(
                    func.concat(DimProducts.category_l1, '.', DimProducts.category_l2).label('name'),
                    func.sum(FactUserBehavior.revenue).label('gmv')
                ).join(
                    DimProducts, FactUserBehavior.product_id == DimProducts.product_id
                ).filter(
                    FactUserBehavior.event_type == 'purchase'
                )
                
                # 添加时间范围过滤
                if start_time_key and end_time_key:
                    query = query.filter(
                        FactUserBehavior.time_key >= start_time_key,
                        FactUserBehavior.time_key <= end_time_key
                    )
                
                results = query.group_by(
                    DimProducts.category_l1, DimProducts.category_l2
                ).order_by(
                    func.sum(FactUserBehavior.revenue).desc()
                ).limit(
                    limit
                ).all()
            elif category_level == 'l3':
                # L3 层级查询
                query = db.query(
                    func.concat(DimProducts.category_l1, '.', DimProducts.category_l2, '.', DimProducts.category_l3).label('name'),
                    func.sum(FactUserBehavior.revenue).label('gmv')
                ).join(
                    DimProducts, FactUserBehavior.product_id == DimProducts.product_id
                ).filter(
                    FactUserBehavior.event_type == 'purchase'
                )
                
                # 添加时间范围过滤
                if start_time_key and end_time_key:
                    query = query.filter(
                        FactUserBehavior.time_key >= start_time_key,
                        FactUserBehavior.time_key <= end_time_key
                    )
                
                results = query.group_by(
                    DimProducts.category_l1, DimProducts.category_l2, DimProducts.category_l3
                ).order_by(
                    func.coalesce(func.sum(FactUserBehavior.revenue), 0).desc()
                ).limit(
                    limit
                ).all()
            else:
                # 默认 L1 层级
                query = db.query(
                    DimProducts.category_l1.label('name'),
                    func.sum(FactUserBehavior.revenue).label('gmv')
                ).join(
                    DimProducts, FactUserBehavior.product_id == DimProducts.product_id
                ).filter(
                    FactUserBehavior.event_type == 'purchase'
                )
                
                # 添加时间范围过滤
                if start_time_key and end_time_key:
                    query = query.filter(
                        FactUserBehavior.time_key >= start_time_key,
                        FactUserBehavior.time_key <= end_time_key
                    )
                
                results = query.group_by(
                    DimProducts.category_l1
                ).order_by(
                    func.sum(FactUserBehavior.revenue).desc()
                ).limit(
                    limit
                ).all()
            
            # 格式化结果
            categories = []
            for result in results:
                if result and result.name:
                    percentage = 0
                    gmv = float(result.gmv) if result.gmv else 0
                    if total_gmv > 0:
                        percentage = (gmv / total_gmv) * 100
                    categories.append({
                        "name": result.name,
                        "gmv": gmv,
                        "percentage": round(percentage, 1)
                    })
            # 存储到缓存
            category_cache[cache_key] = categories
            return categories
        finally:
            db.close()
