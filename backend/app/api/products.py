from fastapi import APIRouter, Query
from datetime import date
from ..services.products_service import ProductsService

router = APIRouter()
products_service = ProductsService()

@router.get("/top")
def top_products(
    metric: str = Query(..., description="排序指标: sales, views, carts"),
    limit: int = Query(10, description="返回数量限制"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期")
):
    """热销商品接口"""
    return products_service.get_top_products(metric, limit, start_date, end_date)
