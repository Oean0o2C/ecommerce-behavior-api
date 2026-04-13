from datetime import date, datetime
from ..repositories.sales_repository import SalesRepository

class SalesService:
    def __init__(self):
        self.sales_repo = SalesRepository()
    
    def get_sales_overview(self, start_date: date, end_date: date):
        """获取销售概览"""
        # 调用销售仓库的方法获取数据
        data = self.sales_repo.get_sales_overview(start_date, end_date)
        
        # 计算转化率
        conversion_rate = 0
        if data['uv'] > 0:
            conversion_rate = data['order_count'] / data['uv']
        
        return {
            "code": 200,
            "data": {
                "gmv": data['gmv'],
                "order_count": data['order_count'],
                "uv": data['uv'],
                "conversion_rate": round(conversion_rate, 4)
            },
            "message": "success",
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    
    def get_sales_trend(self, granularity: str, start_date: date, end_date: date):
        """获取销售趋势"""
        # 调用销售仓库的方法获取数据
        trend_data = self.sales_repo.get_sales_trend(granularity, start_date, end_date)
        
        return {
            "code": 200,
            "data": {
                "granularity": granularity,
                "trend": trend_data
            },
            "message": "success",
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
