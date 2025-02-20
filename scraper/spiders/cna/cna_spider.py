from scraper.spiders.base_spider import BaseNewsSpider
import re
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import logging
from typing import Dict, Optional, Generator
from .cna_menu_scraper import CnaMenuScraper

class CnaSpider(BaseNewsSpider):
    # 靜態配置
    name = "cna"
    base_url = "https://www.cna.com.tw"

    def __init__(self, category='ait', **kwargs):
        super().__init__()
        
        # 從配置文件讀取可用類別
        menu_scraper = CnaMenuScraper()
        self.available_categories = menu_scraper.get_menu_mapping()
        
        if not self.available_categories:
            self.logger.error("無法獲取類別配置，使用預設類別")
            self.available_categories = {'ait': '科技', 'aall': '即時'}
        
        # 驗證分類是否有效
        if category not in self.available_categories:
            raise ValueError(f"Invalid category. Must be one of {list(self.available_categories.keys())}")
        
        # 動態配置
        self.category = category
        self.start_url = f"{self.base_url}/list/{category}.aspx"
        self.logger = logging.getLogger(self.__class__.__name__)

    def change_category(self, new_category: str) -> None:
        """允許動態更改分類"""
        if new_category not in self.available_categories:
            raise ValueError(f"Invalid category. Must be one of {list(self.available_categories.keys())}")
        self.category = new_category
        self.start_url = f"{self.base_url}/list/{new_category}.aspx"

    def fetch_news_list(self) -> Generator[Dict, None, None]:
        """獲取新聞列表"""
        try:
            response = self.session.get(self.start_url, headers=self.headers)
            response.raise_for_status()
            return self.parse_list(response)
        except requests.RequestException as e:
            self.logger.error(f"獲取新聞列表失敗: {str(e)}")
            return None

    def parse_list(self, response) -> Generator[Dict, None, None]:
        """解析新聞列表頁面"""
        soup = BeautifulSoup(response.text, 'lxml')
        for li in soup.select('ul.mainList li:not(.sponsored)'):
            try:
                article_data = {
                    'title': li.select_one('h2 span').text.strip(),
                    'url': li.select_one('a')['href'],
                    'publish_time': self._parse_cna_time(li.select_one('div.date')['title']),
                    'source': '中央社'
                }
                article_content = self.fetch_article(article_data)
                if article_content:
                    yield article_content
            except Exception as e:
                self.logger.error(f"解析列表項目失敗: {str(e)}")

    def fetch_article(self, article_data: Dict) -> Optional[Dict]:
        """獲取文章內容"""
        try:
            response = self.session.get(article_data['url'], headers=self.headers)
            response.raise_for_status()
            return self.parse_article(response, article_data)
        except requests.RequestException as e:
            self.logger.error(f"獲取文章失敗 {article_data['url']}: {str(e)}")
            return None

    def parse_article(self, response, article_data: Dict) -> Dict:
        """解析文章內容"""
        try:
            soup = BeautifulSoup(response.text, 'lxml')
            content_element = soup.select_one('div.paragraph')
            content = self._clean_content(content_element)
            
            return {
                'title': article_data['title'],
                'content': content,
                'url': article_data['url'],
                'publish_date': article_data['publish_time'],
                'source': article_data['source']
            }
        except Exception as e:
            self.logger.error(f"解析文章內容失敗 {article_data['url']}: {str(e)}")
            return None

    def _parse_cna_time(self, timestamp: str) -> datetime:
        """解析中央社的時間戳"""
        try:
            return datetime.strptime(timestamp, '%Y%m%d%H%M%S')
        except ValueError as e:
            self.logger.error(f"解析時間戳失敗 {timestamp}: {str(e)}")
            return datetime.now()

    def _clean_content(self, content_element) -> str:
        """清理文章內容"""
        if not content_element:
            return ""
        try:
            # 移除不需要的元素
            for selector in ['.shareBar', '.modalbox', 'script']:
                [x.extract() for x in content_element.select(selector)]
            
            # 獲取純文本並清理
            text = content_element.get_text(strip=True)
            # 移除多餘的空白
            text = re.sub(r'\s+', ' ', text)
            return text
        except Exception as e:
            self.logger.error(f"清理內容失敗: {str(e)}")
            return "" 