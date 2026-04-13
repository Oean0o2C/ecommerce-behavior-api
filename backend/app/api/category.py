from fastapi import APIRouter, Query
from datetime import date
from ..services.category_service import CategoryService

router = APIRouter()
category_service = CategoryService()

@router.get("/performance")
def category_performance(
    category_level: str = Query(..., description="类目层级: l1, l2, l3"),
    limit: int = Query(10, description="返回数量限制"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期")
):
    """品类表现接口"""
    return category_service.get_category_performance(category_level, limit, start_date, end_date)
