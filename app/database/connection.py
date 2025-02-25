from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging
from typing import Generator

from app.config.settings import settings
from app.models.news import Base
from scraper.utils.logger import setup_logger

# 使用自定義的logger設置
logger = setup_logger(__name__)

class DatabaseManager:
    """資料庫連接管理器"""
    
    def __init__(self, database_url=None):
        self.engine = None
        self.session_factory = None
        
        # 直接使用 settings 中的 database_url 初始化
        database_url = database_url or settings.database_url
        if database_url:
            self.init_with_url(database_url)
        else:
            logger.warning("未提供資料庫URL，需要稍後手動初始化")
    
    def init_with_url(self, database_url):
        """使用URL初始化"""
        try:
            if not database_url:
                raise ValueError("database_url not found")
            
            echo = settings.sql_echo or False
            # 設置連接池參數
            
            self.engine = create_engine(
                database_url, 
                echo=echo,
                pool_size=3,  # 連接池大小
                max_overflow=10,  # 允許的最大臨時連接
                pool_timeout=30,  # 連接獲取超時
                pool_recycle=1800  # 連接回收時間(秒)
            )
            self.session_factory = scoped_session(sessionmaker(bind=self.engine))
            
            # 首先測試數據庫連接
            if not self.test_connection():
                raise ValueError("數據庫連接測試失敗")
            
            # 創建並驗證表格
            self.create_tables()
                
            logger.info("資料庫連接初始化成功")
            
        except Exception as e:
            logger.error(f"資料庫連接初始化失敗: {str(e)}")
            raise
            
    def init_app(self, app):
        """Flask應用初始化"""
        database_url = app.config.get('DATABASE_URL') or settings.database_url
        if not database_url:
            raise ValueError("DATABASE_URL 未設置")
        self.init_with_url(database_url)
        
        # 註冊關閉鉤子
        @app.teardown_appcontext
        def close_sessions(exception=None):
            if self.session_factory:
                self.session_factory.remove()

    def test_connection(self) -> bool:
        """測試數據庫連接並驗證配置"""
        try:
            # 測試不同級別的日誌
            logger.debug("=== 測試 DEBUG 級別消息 ===")
            logger.info("=== 測試 INFO 級別消息 ===")
            logger.warning("=== 測試 WARNING 級別消息 ===")
            logger.error("=== 測試 ERROR 級別消息 ===")
            
            # 使用 with 語句確保連接會被正確關閉
            with self.engine.connect() as conn:
                # 執行一系列測試查詢
                results = {}
                
                # 1. 測試數據庫連接
                results['database'] = conn.execute(text("SELECT current_database()")).scalar()
                
                # 2. 獲取當前schema
                results['schema'] = conn.execute(text("SELECT current_schema()")).scalar()
                
                # 3. 獲取當前用戶
                results['user'] = conn.execute(text("SELECT current_user")).scalar()
                
                # 4. 獲取用戶權限
                results['privileges'] = conn.execute(
                    text("SELECT has_database_privilege(current_user, current_database(), 'CREATE')")
                ).scalar()

                # 記錄連接信息
                logger.info(f"""
                    數據庫連接信息：
                    - 數據庫：{results['database']}
                    - Schema：{results['schema']}
                    - 用戶：{results['user']}
                    - 具有CREATE權限：{results['privileges']}
                """)

                # 5. 測試基本的寫入權限
                try:
                    conn.execute(text("CREATE TABLE IF NOT EXISTS connection_test (id serial primary key)"))
                    conn.execute(text("DROP TABLE connection_test"))
                    logger.info("成功測試表的創建和刪除權限")
                except Exception as e:
                    logger.error(f"表操作權限測試失敗: {str(e)}")
                    return False

                return True
                
        except Exception as e:
            logger.error(f"數據庫連接測試失敗: {str(e)}")
            return False

    def create_tables(self):
        """創建所有表"""
        try:
            # 使用 SQLAlchemy 創建所有定義的表
            Base.metadata.create_all(bind=self.engine)
            logger.info("完成資料表檢查")
        except Exception as e:
            logger.error(f"資料表創建失敗: {str(e)}")
            raise

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """獲取資料庫會話的上下文管理器"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
            logger.debug("資料庫操作提交成功")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"資料庫操作錯誤，執行回滾: {str(e)}")
            raise
        finally:
            session.close()

# 創建全局資料庫管理器實例
try:
    db_manager = DatabaseManager()
except Exception as e:
    logger.error(f"資料庫管理器初始化失敗: {str(e)}")
    raise 