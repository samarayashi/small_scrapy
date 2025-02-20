from typing import Generator, Dict
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.database.connection import db_manager
from app.models.news import NewsArticle
from scraper.spiders.cna.cna_spider import CnaSpider

logger = logging.getLogger(__name__)

class NewsETLPipeline:
    """新聞ETL管道"""
    
    def __init__(self):
        self.spider = CnaSpider()
        
    def extract(self) -> Generator[Dict, None, None]:
        """從爬蟲獲取數據"""
        yield from self.spider.crawl()
        
    def transform(self, data: Dict) -> NewsArticle:
        """轉換數據為NewsArticle模型"""
        return NewsArticle.from_spider_data(data)
        
    def load(self, article: NewsArticle) -> bool:
        """將數據載入資料庫"""
        try:
            with db_manager.get_session() as session:
                session.add(article)
                return True
                
        except IntegrityError:
            logger.warning(f"文章已存在（標題+URL重複）: {article.title}")
            return False
        except Exception as e:
            logger.error(f"保存文章時發生錯誤: {str(e)}")
            raise
            
    def run(self):
        """執行ETL流程"""
        total_processed = 0
        total_saved = 0
        
        try:
            for data in self.extract():
                total_processed += 1
                article = self.transform(data)
                if self.load(article):
                    total_saved += 1
                    
            logger.info(f"ETL完成: 處理 {total_processed} 篇文章，成功保存 {total_saved} 篇")
            
        except Exception as e:
            logger.error(f"ETL過程發生錯誤: {str(e)}")
            raise 