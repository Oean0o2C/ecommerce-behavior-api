from datetime import datetime
from ..repositories.products_repository import ProductsRepository

class ProductsService:
    def __init__(self):
        self.products_repo = ProductsRepository()
    
    def get_top_products(self, metric: str, limit: int, start_date, end_date):
        """获取热销商品"""
        # 调用商品仓库的方法获取数据
        products = self.products_repo.get_top_products(metric, limit, start_date, end_date)
        
        return {
            "code": 200,
            "data": {
                "metric": metric,
                "products": products
            },
            "message": "success",
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
