from datetime import date
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.models import FactUserBehavior, DimTime

class SalesRepository:
    def get_sales_overview(self, start_date: date, end_date: date):
        """获取销售概览数据"""
        db = SessionLocal()
        try:
            # 构建时间范围的time_key
            start_time_key = int(start_date.strftime('%Y%m%d'))
            end_time_key = int(end_date.strftime('%Y%m%d'))
            
            # 查询销售概览数据
            result = db.query(
                func.count(func.distinct(FactUserBehavior.user_id)).label('uv'),
                func.count(FactUserBehavior.event_id).label('pv'),
                func.count(FactUserBehavior.event_id).filter(FactUserBehavior.event_type == 'purchase').label('order_count'),
                func.sum(FactUserBehavior.revenue).filter(FactUserBehavior.event_type == 'purchase').label('gmv'),
                func.avg(FactUserBehavior.revenue).filter(FactUserBehavior.event_type == 'purchase').label('avg_order_value')
            ).filter(
                FactUserBehavior.time_key >= start_time_key,
                FactUserBehavior.time_key <= end_time_key
            ).first()
            
            if result:
                return {
                    "uv": result.uv or 0,
                    "pv": result.pv or 0,
                    "order_count": result.order_count or 0,
                    "gmv": float(result.gmv) if result.gmv else 0,
                    "avg_order_value": float(result.avg_order_value) if result.avg_order_value else 0
                }
            else:
                return {
                    "uv": 0,
                    "pv": 0,
                    "order_count": 0,
                    "gmv": 0,
                    "avg_order_value": 0
                }
        finally:
            db.close()
    
    def get_sales_trend(self, granularity: str, start_date: date, end_date: date):
        """获取销售趋势数据"""
        db = SessionLocal()
        try:
            # 构建时间范围的time_key
            start_time_key = int(start_date.strftime('%Y%m%d'))
            end_time_key = int(end_date.strftime('%Y%m%d'))
            
            # 查询销售趋势数据 - 不依赖DimTime表，直接从time_key计算日期
            if granularity == 'day':
                # 直接查询FactUserBehavior表，使用time_key计算日期
                results = db.query(
                    FactUserBehavior.time_key.label('time_key'),
                    func.sum(FactUserBehavior.revenue).filter(FactUserBehavior.event_type == 'purchase').label('gmv'),
                    func.count(FactUserBehavior.event_id).filter(FactUserBehavior.event_type == 'purchase').label('orders')
                ).filter(
                    FactUserBehavior.time_key >= start_time_key,
                    FactUserBehavior.time_key <= end_time_key
                ).group_by(
                    FactUserBehavior.time_key
                ).order_by(
                    FactUserBehavior.time_key
                ).all()
            else:
                # 对于week和month粒度，使用原始实现
                results = db.query(
                    DimTime.date_actual.label('date'),
                    func.sum(FactUserBehavior.revenue).filter(FactUserBehavior.event_type == 'purchase').label('gmv'),
                    func.count(FactUserBehavior.event_id).filter(FactUserBehavior.event_type == 'purchase').label('orders')
                ).join(
                    DimTime, FactUserBehavior.time_key == DimTime.time_key
                ).filter(
                    FactUserBehavior.time_key >= start_time_key,
                    FactUserBehavior.time_key <= end_time_key
                ).group_by(
                    DimTime.date_actual
                ).order_by(
                    DimTime.date_actual
                ).all()
            
            # 格式化结果
            trend_data = []
            for result in results:
                if hasattr(result, 'time_key') and result.time_key:
                    # 从time_key计算日期
                    time_key_str = str(result.time_key)
                    year = int(time_key_str[:4])
                    month = int(time_key_str[4:6])
                    day = int(time_key_str[6:8])
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    trend_data.append({
                        "date": date_str,
                        "gmv": float(result.gmv) if result.gmv else 0,
                        "orders": result.orders or 0
                    })
                elif hasattr(result, 'date') and result.date:
                    # 使用DimTime表的日期
                    trend_data.append({
                        "date": result.date.strftime('%Y-%m-%d'),
                        "gmv": float(result.gmv) if result.gmv else 0,
                        "orders": result.orders or 0
                    })
            
            return trend_data
        finally:
            db.close()
