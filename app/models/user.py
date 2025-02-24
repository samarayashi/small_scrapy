from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base  # 統一使用同一個 Base
from app.models.news import NewsCategory  # 添加 NewsCategory 的導入
from datetime import datetime

class User(Base):
    """使用者模型，存放使用者基本資料"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(100), nullable=False)
    line_user_id = Column(String(100), nullable=False, unique=True)
    is_registered = Column(Boolean, default=False)
    registration_date = Column(DateTime)
    last_active = Column(DateTime)

    # 建立與訂閱表的一對多關係
    sub_weathers = relationship('SubWeather', back_populates='user', cascade='all, delete-orphan')
    sub_news = relationship('SubNews', back_populates='user', cascade='all, delete-orphan')

    def __init__(self, line_user_id, user_name='新用戶'):
        self.line_user_id = line_user_id
        self.user_name = user_name
        self.is_registered = True
        self.registration_date = datetime.now()
        self.last_active = datetime.now()

    def __repr__(self):
        return f"<User(name='{self.user_name}', line_user_id='{self.line_user_id}')>"


class SubWeather(Base):
    """天氣訂閱模型，存放使用者天氣訂閱相關資訊"""
    __tablename__ = 'sub_weather'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    longitude = Column(Float)
    latitude = Column(Float)
    location_name = Column(String(100))

    user = relationship('User', back_populates='sub_weathers')

    def __repr__(self):
        return f"<SubWeather(user_id={self.user_id}, location='{self.location_name}', longitude={self.longitude}, latitude={self.latitude})>"


class SubNews(Base):
    """新聞訂閱模型，存放使用者新聞訂閱的分類資訊"""
    __tablename__ = 'sub_news'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    news_category_key = Column(String(50), ForeignKey('news_categories.category_key', ondelete='CASCADE'), nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'news_category_key', name='uq_user_news_category'),)

    user = relationship('User', back_populates='sub_news')
    news_category = relationship(NewsCategory, lazy='joined')  # 直接使用已導入的 NewsCategory 類別

    def __repr__(self):
        return f"<SubNews(user_id={self.user_id}, news_category_key={self.news_category_key})>" 