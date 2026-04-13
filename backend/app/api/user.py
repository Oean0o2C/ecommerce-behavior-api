from fastapi import APIRouter, Query
from datetime import date
from ..services.user_service import UserService

router = APIRouter()
user_service = UserService()

@router.get("/funnel")
def user_funnel(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期")
):
    """用户行为漏斗接口"""
    return user_service.get_user_funnel(start_date, end_date)

@router.get("/rfm")
def user_rfm(
    segment: str = Query(None, description="用户分层")
):
    """用户RFM分层接口"""
    return user_service.get_user_rfm(segment)
