from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ARRAY, Float
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
    category_code = Column(String(50), nullable=False)
    category_name = Column(String(100), nullable=False)
    content = Column(Text)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(datetime.UTC))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(datetime.UTC), onupdate=lambda: datetime.now(datetime.UTC))
    
    # LLM 相關欄位
    keywords = Column(ARRAY(String))
    summary = Column(Text)
    sentiment = Column(Float)

    def __repr__(self):
        return f"<NewsArticle(title='{self.title}', category='{self.category_code}')>"

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