import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPI:
    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_sales_overview(self):
        """测试销售概览接口"""
        response = client.get("/api/v1/sales/overview", params={
            "start_date": "2026-04-01",
            "end_date": "2026-04-13"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "data" in data
        assert "gmv" in data["data"]
        assert "order_count" in data["data"]
        assert "uv" in data["data"]
        assert "conversion_rate" in data["data"]
    
    def test_sales_trend(self):
        """测试销售趋势接口"""
        response = client.get("/api/v1/sales/trend", params={
            "granularity": "day",
            "start_date": "2026-04-01",
            "end_date": "2026-04-13"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "data" in data
        assert "granularity" in data["data"]
        assert "trend" in data["data"]
    
    def test_category_performance(self):
        """测试品类表现接口"""
        response = client.get("/api/v1/category/performance", params={
            "category_level": "l1",
            "limit": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "data" in data
        assert "category_level" in data["data"]
        assert "categories" in data["data"]
    
    def test_user_funnel(self):
        """测试用户行为漏斗接口"""
        response = client.get("/api/v1/user/funnel", params={
            "start_date": "2026-04-01",
            "end_date": "2026-04-13"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "data" in data
        assert "funnel" in data["data"]
    
    def test_user_rfm(self):
        """测试用户RFM分层接口"""
        response = client.get("/api/v1/user/rfm")
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "data" in data
        assert "users" in data["data"]
    
    def test_products_top(self):
        """测试热销商品接口"""
        response = client.get("/api/v1/products/top", params={
            "metric": "sales",
            "limit": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 200
        assert "data" in data
        assert "metric" in data["data"]
        assert "products" in data["data"]
