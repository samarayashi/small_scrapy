from typing import Generator, Dict, List
from scraper.utils.logger import setup_logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import db_manager
from app.models.news import NewsArticle
from scraper.spiders.cna.cna_spider import CnaSpider

# 使用自定義的logger設置
logger = setup_logger(__name__)

class NewsETLPipeline:
    """新聞ETL管道"""
    
    def __init__(self):
        self.spider = CnaSpider(category="acul")
        
    def extract(self) -> Generator[Dict, None, None]:
        """從爬蟲獲取數據"""
        yield from self.spider.crawl(max_pages=2)
        
    def transform(self, data: Dict) -> NewsArticle:
        """轉換數據為NewsArticle模型"""
        return NewsArticle.from_spider_data(data)
        
    def load(self, session: Session, article: NewsArticle) -> bool:
        """將數據載入資料庫
        
        Args:
            session: SQLAlchemy session
            article: 要保存的文章對象
            
        Returns:
            bool: 是否保存成功
        """
        try:
            session.add(article)
            session.flush()
            return True
                
        except IntegrityError:
            # 重複文章不是錯誤，只需要返回 False
            return False
            
        except Exception:
            # 不記錄錯誤，讓它往上傳遞給 _save_batch 處理
            raise
            
    def _save_batch(self, articles: List[NewsArticle]) -> int:
        """批次保存文章
        
        Args:
            articles: 要保存的文章列表
            
        Returns:
            int: 成功保存的文章數量
        """
        saved_count = 0
        with db_manager.get_session() as session:
            for article in articles:
                try:
                    if self.load(session, article):
                        saved_count += 1
                        logger.info(f"成功保存文章: {article.title}")
                    else:
                        logger.warning(f"文章已存在，跳過: {article.title}")
                except Exception as e:
                    # 在這裡統一處理並記錄數據庫操作錯誤
                    logger.error(f"文章 '{article.title}' 保存失敗: {str(e)}")
                    continue
        return saved_count

    def run(self):
        """執行ETL流程"""
        try:
            logger.info("開始ETL流程")
            total_processed = 0
            total_saved = 0
            batch_size = 10  # 可配置的批次大小
            
            articles_batch = []
            
            # 開始抓取和處理文章
            logger.info("開始抓取新聞數據...")
            for data in self.extract():
                total_processed += 1
                try:
                    # 轉換數據
                    article = self.transform(data)
                    articles_batch.append(article)
                    
                    # 當達到批次大小時進行保存
                    if len(articles_batch) >= batch_size:
                        saved = self._save_batch(articles_batch)
                        total_saved += saved
                        articles_batch = []
                        logger.info(f"已處理 {total_processed} 篇文章，成功保存 {total_saved} 篇")
                        
                except Exception as e:
                    # 只記錄數據轉換錯誤
                    logger.error(f"第 {total_processed} 篇文章轉換失敗: {str(e)}")
                    continue
            
            # 處理剩餘的文章
            if articles_batch:
                saved = self._save_batch(articles_batch)
                total_saved += saved
            
            # 輸出最終統計
            success_rate = (total_saved / total_processed * 100) if total_processed > 0 else 0
            logger.info(f"ETL完成: 總共處理 {total_processed} 篇文章，成功保存 {total_saved} 篇 (成功率: {success_rate:.2f}%)")
            return True
            
        except Exception as e:
            # 只記錄整體流程的嚴重錯誤
            logger.error(f"ETL流程發生嚴重錯誤: {str(e)}")
            return False 