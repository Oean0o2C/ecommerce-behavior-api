from sqlalchemy import Column, Integer, String, Boolean, Date, DECIMAL, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DimTime(Base):
    __tablename__ = "dim_time"
    
    time_key = Column(Integer, primary_key=True, index=True)
    date_actual = Column(Date, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, nullable=False)
    is_holiday = Column(Boolean, default=False)

class DimUsers(Base):
    __tablename__ = "dim_users"
    
    user_key = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    first_seen_date = Column(Date, nullable=False)
    last_seen_date = Column(Date, nullable=False)
    user_segment = Column(String(20), default='new')
    region = Column(String(50), default='unknown')
    device_type = Column(String(20), default='desktop')

class DimProducts(Base):
    __tablename__ = "dim_products"
    
    product_key = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, unique=True, nullable=False, index=True)
    category_id = Column(BigInteger, nullable=False)
    category_l1 = Column(String(50), nullable=False)
    category_l2 = Column(String(50), nullable=False)
    category_l3 = Column(String(50), default='other')
    brand = Column(String(50), default='Unknown')
    price_range = Column(String(20))

class FactUserBehavior(Base):
    __tablename__ = "fact_user_behavior"
    
    event_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    time_key = Column(Integer, ForeignKey("dim_time.time_key"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("dim_users.user_id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("dim_products.product_id"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, default=1)
    revenue = Column(DECIMAL(12, 2))
    user_session = Column(String(50), nullable=False)
