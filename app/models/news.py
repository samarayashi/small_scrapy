from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ARRAY, Float, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base  # 從統一的 Base 匯入

class NewsCategory(Base):
    """新聞分類模型，主鍵為 category_key"""
    __tablename__ = 'news_categories'

    category_key = Column(String(50), primary_key=True)
    category_name = Column(String(100), nullable=False)

    articles = relationship('NewsArticle', back_populates='news_category', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<NewsCategory(key='{self.category_key}', name='{self.category_name}')>"

class NewsArticle(Base):
    """新聞文章模型"""
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    publish_time = Column(TIMESTAMP, nullable=False)
    source = Column(String(100), nullable=False)
    news_category_key = Column(String(50), ForeignKey('news_categories.category_key'), nullable=False)
    content = Column(Text)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # LLM 相關欄位
    keywords = Column(ARRAY(String))
    summary = Column(Text)
    sentiment = Column(Float)

    # 添加唯一約束
    __table_args__ = (
        UniqueConstraint('title', 'url', name='uk_news_title_url'),
    )

    news_category = relationship('NewsCategory', back_populates='articles')

    def __repr__(self):
        category_name = self.news_category.category_name if self.news_category else 'Unknown'
        return f"<NewsArticle(title='{self.title}', category='{category_name}')>"

    @classmethod
    def from_spider_data(cls, data: dict) -> "NewsArticle":
        """從爬蟲數據創建新聞文章實例
        假設 data 包含 news_category_key 或已由外部轉換成 news_category_key
        """
        return cls(
            title=data['title'],
            url=data['url'],
            publish_time=data['publish_time'],
            source=data['source'],
            news_category_key=data['category'],
            content=data.get('content')
        ) 