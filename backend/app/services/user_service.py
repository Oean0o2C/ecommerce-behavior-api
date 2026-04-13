from datetime import date, datetime
from ..repositories.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
    
    def get_user_funnel(self, start_date: date, end_date: date):
        """获取用户行为漏斗"""
        # 调用用户仓库的方法获取数据
        funnel = self.user_repo.get_user_funnel(start_date, end_date)
        
        return {
            "code": 200,
            "data": {
                "funnel": funnel
            },
            "message": "success",
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    
    def get_user_rfm(self, segment: str):
        """获取用户RFM分层"""
        # 调用用户仓库的方法获取数据
        users = self.user_repo.get_user_rfm(segment)
        
        return {
            "code": 200,
            "data": {
                "segment": segment,
                "users": users
            },
            "message": "success",
            "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
