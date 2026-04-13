from datetime import datetime
from ..repositories.category_repository import CategoryRepository

class CategoryService:
    def __init__(self):
        self.category_repo = CategoryRepository()
    
    def get_category_performance(self, category_level: str, limit: int, start_date, end_date):
        """获取品类表现"""
        # 调用品类仓库的方法获取数据
        categories = self.category_repo.get_category_performance(category_level, limit, start_date, end_date)
        
        return {
            "code": 200,
            "data": {
                "category_level": category_level,
                "categories": categories
            },
            "message": "success",
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
