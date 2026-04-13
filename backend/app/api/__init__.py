from fastapi import APIRouter
from .sales import router as sales_router
from .category import router as category_router
from .user import router as user_router
from .products import router as products_router

router = APIRouter()

# 注册各个路由模块
router.include_router(sales_router, prefix="/sales", tags=["sales"])
router.include_router(category_router, prefix="/category", tags=["category"])
router.include_router(user_router, prefix="/user", tags=["user"])
router.include_router(products_router, prefix="/products", tags=["products"])
