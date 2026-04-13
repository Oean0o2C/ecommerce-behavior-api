from datetime import date
from sqlalchemy import func
from ..database import SessionLocal
from ..models.models import FactUserBehavior, DimTime

class UserRepository:
    def get_user_funnel(self, start_date: date, end_date: date):
        """获取用户行为漏斗数据"""
        db = SessionLocal()
        try:
            # 构建时间范围的time_key
            start_time_key = int(start_date.strftime('%Y%m%d'))
            end_time_key = int(end_date.strftime('%Y%m%d'))
            
            # 查询浏览量
            view_count = db.query(
                func.count(FactUserBehavior.event_id)
            ).filter(
                FactUserBehavior.event_type == 'view',
                FactUserBehavior.time_key >= start_time_key,
                FactUserBehavior.time_key <= end_time_key
            ).scalar() or 0
            
            # 查询加购量
            cart_count = db.query(
                func.count(FactUserBehavior.event_id)
            ).filter(
                FactUserBehavior.event_type == 'cart',
                FactUserBehavior.time_key >= start_time_key,
                FactUserBehavior.time_key <= end_time_key
            ).scalar() or 0
            
            # 查询购买量
            purchase_count = db.query(
                func.count(FactUserBehavior.event_id)
            ).filter(
                FactUserBehavior.event_type == 'purchase',
                FactUserBehavior.time_key >= start_time_key,
                FactUserBehavior.time_key <= end_time_key
            ).scalar() or 0
            
            # 计算各阶段百分比
            view_percentage = 100
            cart_percentage = 0
            purchase_percentage = 0
            
            if view_count > 0:
                cart_percentage = (cart_count / view_count) * 100
            if cart_count > 0:
                purchase_percentage = (purchase_count / cart_count) * 100
            
            # 构建漏斗数据
            funnel = [
                {"stage": "view", "count": view_count, "percentage": round(view_percentage, 1)},
                {"stage": "cart", "count": cart_count, "percentage": round(cart_percentage, 1)},
                {"stage": "purchase", "count": purchase_count, "percentage": round(purchase_percentage, 1)}
            ]
            
            return funnel
        finally:
            db.close()
    
    def get_user_rfm(self, segment: str):
        """获取用户RFM分层数据"""
        db = SessionLocal()
        try:
            # 查询用户RFM数据
            results = db.query(
                FactUserBehavior.user_id,
                func.max(DimTime.date_actual).label('last_purchase_date'),
                func.count(FactUserBehavior.event_id).filter(FactUserBehavior.event_type == 'purchase').label('frequency'),
                func.sum(FactUserBehavior.revenue).filter(FactUserBehavior.event_type == 'purchase').label('monetary')
            ).join(
                DimTime, FactUserBehavior.time_key == DimTime.time_key
            ).filter(
                FactUserBehavior.event_type == 'purchase'
            ).group_by(
                FactUserBehavior.user_id
            ).all()
            
            # 计算RFM评分和用户分层
            users = []
            for result in results:
                # 计算最近购买天数
                recency = (date.today() - result.last_purchase_date).days
                
                # 计算RFM评分
                # 这里使用简单的评分逻辑，实际项目中可能需要更复杂的评分算法
                r_score = 5 if recency <= 7 else 4 if recency <= 14 else 3 if recency <= 30 else 2 if recency <= 90 else 1
                f_score = 5 if result.frequency >= 10 else 4 if result.frequency >= 5 else 3 if result.frequency >= 3 else 2 if result.frequency >= 2 else 1
                m_score = 5 if result.monetary >= 1000 else 4 if result.monetary >= 500 else 3 if result.monetary >= 200 else 2 if result.monetary >= 100 else 1
                
                # 计算用户分层
                if r_score >= 4 and f_score >= 4 and m_score >= 4:
                    user_segment = 'high_value'
                elif r_score >= 3 and f_score >= 3 and m_score >= 3:
                    user_segment = 'medium_value'
                else:
                    user_segment = 'low_value'
                
                # 如果指定了segment，只返回该segment的用户
                if segment and user_segment != segment:
                    continue
                
                users.append({
                    "user_id": result.user_id,
                    "recency": recency,
                    "frequency": result.frequency,
                    "monetary": float(result.monetary) if result.monetary else 0,
                    "segment": user_segment
                })
            
            # 按monetary降序排序
            users.sort(key=lambda x: x['monetary'], reverse=True)
            
            return users
        finally:
            db.close()
