from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging
from typing import Generator

from app.config.settings import config
from app.models.news import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """資料庫連接管理器"""
    
    def __init__(self):
        self.engine = create_engine(
            config['DATABASE_URL'],
            echo=config['ENV'] == 'development'
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """創建所有表"""
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """獲取資料庫會話的上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"資料庫操作錯誤: {str(e)}")
            raise
        finally:
            session.close()

# 創建全局資料庫管理器實例
db_manager = DatabaseManager() 