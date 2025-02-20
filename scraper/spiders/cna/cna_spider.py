from scraper.spiders.base_spider import BaseNewsSpider
import re
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import logging
import os
from typing import Dict, Optional, Generator
from .cna_menu_scraper import CnaMenuScraper
from scraper.utils.logger import setup_logger

class CnaSpider(BaseNewsSpider):
    """中央社新聞爬蟲"""
    
    name = "cna"
    base_url = "https://www.cna.com.tw"
    DEFAULT_CATEGORY = 'aall'  # 預設使用即時新聞類別

    def __init__(self, category=DEFAULT_CATEGORY):
        """
        初始化爬蟲
        Args:
            category (str): 新聞類別代碼，預設為'aall'（即時新聞）
        """
        super().__init__()
        # 設置logger，控制台只顯示INFO及以上級別
        self.logger = setup_logger(
            self.__class__.__name__,
            console_level=logging.INFO,
            file_level=logging.DEBUG
        )
        
        # 載入類別配置
        menu_scraper = CnaMenuScraper()
        self.categories = menu_scraper.get_menu_mapping()
        
        # 設定初始類別
        self.set_category(category)

    def set_category(self, category_code: str) -> None:
        """
        設定爬取的新聞類別
        Args:
            category_code (str): 類別代碼
        """
        # 檢查類別代碼是否在可用類別值中
        if category_code not in self.categories.values():
            available_categories = "\n".join([
                f"- {name}: {code}" 
                for name, code in self.categories.items()
            ])
            raise ValueError(
                f"無效的類別代碼: {category_code}\n"
                f"可用類別:\n{available_categories}"
            )
        
        self.category = category_code
        self.start_url = f"{self.base_url}/list/{category_code}.aspx"

    def get_category_name(self) -> str:
        """獲取當前類別的中文名稱"""
        for name, code in self.categories.items():
            if code == self.category:
                return name
        return "未知類別"

    def fetch_news_list(self) -> Generator[Dict, None, None]:
        """獲取新聞列表"""
        try:
            response = self._request_with_retry(self.start_url)
            if response:
                # 傳遞 response.text 而不是 response 物件
                yield from self.parse_list(response.text)
        except Exception as e:
            self.logger.error(f"獲取新聞列表失敗: {str(e)}")

    def parse_list(self, html_content: str) -> Generator[Dict, None, None]:
        """解析新聞列表頁面"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            items = soup.select('#jsMainList > li')
            
            for item in items:
                try:
                    # 獲取連結
                    link = item.select_one('a')
                    if not link:
                        continue
                        
                    url = link.get('href', '')
                    if not url:
                        continue
                        
                    # 確保是完整URL
                    if not url.startswith('http'):
                        url = self.base_url + url
                    
                    # 獲取標題
                    title_element = item.select_one('h2 span')
                    if not title_element:
                        continue
                    title = title_element.get_text(strip=True)
                    
                    # 獲取日期 - 修正這裡
                    date_element = item.select_one('.date')
                    if not date_element:
                        continue
                        
                    # 直接獲取日期文字
                    date_text = date_element.get_text(strip=True)
                    # 轉換日期格式
                    publish_time = datetime.strptime(date_text, '%Y/%m/%d %H:%M')
                    
                    yield {
                        'url': url,
                        'title': title,
                        'publish_time': publish_time
                    }
                    
                except Exception as e:
                    self.logger.error(f"解析列表項目失敗: {str(e)}\n項目內容: {item}")
                    continue
                
        except Exception as e:
            self.logger.error(f"解析列表頁面失敗: {str(e)}")

    def fetch_article(self, article_data: Dict) -> Optional[Dict]:
        """獲取文章內容"""
        try:
            response = self._request_with_retry(article_data['url'])
            if response:
                # 傳遞 response.text
                return self.parse_article(response.text, article_data)
        except Exception as e:
            self.logger.error(f"獲取文章失敗 {article_data['url']}: {str(e)}")
        return None

    def parse_article(self, html_content: str, article_data: Dict) -> Optional[Dict]:
        """解析文章內容"""
        try:
            # 使用 html_content 而不是 response.text
            soup = BeautifulSoup(html_content, 'lxml')
            content_element = soup.select_one('div.paragraph')
            
            if not content_element:
                self.logger.warning(f"找不到文章內容: {article_data['url']}")
                return None
                
            content = self._clean_content(content_element)
            if not content:
                return None
                
            return {
                'title': article_data['title'],
                'content': content,
                'url': article_data['url'],
                'publish_date': article_data['publish_time'],
                'source': '中央社',  # 添加固定的來源
                'category': self.get_category_name()  # 使用當前類別
            }
        except Exception as e:
            # 使用 exc_info=True 來記錄完整的堆疊跟蹤
            self.logger.error(
                f"解析文章內容失敗 {article_data['url']}: {str(e)}", 
                exc_info=True
            )
            return None

    def _clean_content(self, content_element) -> Optional[str]:
        """清理文章內容"""
        if not content_element:
            return None
            
        try:
            # 一次性選擇所有不需要的元素
            unwanted_selectors = ', '.join([
                '.shareBar', 
                '.modalbox', 
                'script',
                '.SubscriptionInner',      # 移除訂閱區塊
                '.articlekeywordGroup',    # 移除關鍵字區塊
                '.paragraph.moreArticle',  # 移除相關文章區塊
                '.paragraph.bottomArticleBanner',  # 移除底部廣告
                '.paragraph.BtnShareGroup',  # 移除分享按鈕
                '.advertiseGroup',         # 移除廣告區塊
                '.advertiseMobile'         # 移除手機版廣告
            ])
            
            # 一次性移除所有不需要的元素
            for element in content_element.select(unwanted_selectors):
                element.extract()
            
            # 獲取純文本並清理
            text = content_element.get_text(strip=True)
            
            # 移除多餘的空白
            text = re.sub(r'\s+', ' ', text)
            
            # 移除版權聲明
            text = re.sub(r'本網站之文字、圖片及影音，非經授權，不得轉載、公開播送或公開傳輸及利用。', '', text)
            
            # 移除編輯資訊
            text = re.sub(r'（編輯：[^）]*）\d+', '', text)
            
            return text.strip() or None
            
        except Exception as e:
            self.logger.error(f"清理內容失敗: {str(e)}", exc_info=True)
            return None 