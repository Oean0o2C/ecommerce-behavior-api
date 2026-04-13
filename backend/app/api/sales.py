from fastapi import APIRouter, Query
from datetime import date
from ..services.sales_service import SalesService

router = APIRouter()
sales_service = SalesService()

@router.get("/overview")
def sales_overview(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期")
):
    """销售概览接口"""
    return sales_service.get_sales_overview(start_date, end_date)

@router.get("/trend")
def sales_trend(
    granularity: str = Query(..., description="时间粒度: day, week, month"),
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期")
):
    """销售趋势接口"""
    return sales_service.get_sales_trend(granularity, start_date, end_date)
