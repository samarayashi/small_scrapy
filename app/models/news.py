from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ARRAY, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class NewsArticle(Base):
    """新聞文章模型"""
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    publish_time = Column(TIMESTAMP, nullable=False)
    source = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
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

    def __repr__(self):
        return f"<NewsArticle(title='{self.title}', category='{self.category}')>"

    @classmethod
    def from_spider_data(cls, data: dict) -> "NewsArticle":
        """從爬蟲數據創建新聞文章實例"""
        return cls(
            title=data['title'],
            url=data['url'],
            publish_time=data['publish_time'],
            source=data['source'],
            category=data['category'],
            content=data.get('content'),
        ) 