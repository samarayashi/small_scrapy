from scraper.spiders.base_spider import BaseNewsSpider
import re
from datetime import datetime, timedelta
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
    api_url = "https://www.cna.com.tw/cna2018api/api/WNewsList"
    DEFAULT_PAGE_SIZE = 40     # 預設每頁新聞數量

    def __init__(self, category="acul"):
        """
        初始化爬蟲
        Args:
            category (str): 新聞類別代碼
        """
        super().__init__()
        # 設置logger，控制台只顯示INFO及以上級別
        self.logger = setup_logger(
            self.__class__.__name__,
            console_level=logging.INFO,
            file_level=logging.DEBUG
        )
        
        # 設置API專用的headers
        self.session.headers.update({
            'Referer': 'https://www.cna.com.tw/',
            'Origin': 'https://www.cna.com.tw',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        })
        
        # 載入類別配置
        menu_scraper = CnaMenuScraper()
        self.categories_map = menu_scraper.get_menu_mapping()
        
        # 設定初始類別
        self.set_category(category)
        self.cutoff_time = datetime.now() - timedelta(hours=24)

    def set_category(self, category_code: str) -> None:
        """
        設定爬取的新聞類別
        Args:
            category_code (str): 類別代碼
        """
        # 檢查類別代碼是否在可用類別值中
        if category_code not in self.categories_map.keys():
            available_categories = "\n".join([
                f"- {code}: {name}" 
                for code, name in self.categories_map.items()
            ])
            raise ValueError(
                f"無效的類別代碼: {category_code}\n"
                f"可用類別:\n{available_categories}"
            )
        
        self.category = category_code

    def get_news_list(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> list:
        """
        從API獲取新聞列表
        Args:
            page (int): 頁碼
            page_size (int): 每頁新聞數量，預設40篇
        Returns:
            list: 新聞列表
        """
        try:
            payload = {
                "action": "0",
                "category": self.category,
                "pagesize": str(page_size),
                "pageidx": page
            }
            
            # 使用父類的session發送請求
            response = self.session.post(self.api_url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if data["Result"] != "Y":
                self.logger.error(f"API返回錯誤: {data}")
                return []
            
            # 篩選24小時內的新聞
            news_items = []
            for item in data["ResultData"]["Items"]:
                news_time = datetime.strptime(
                    item['CreateTime'], 
                    '%Y/%m/%d %H:%M'
                )
                if news_time >= self.cutoff_time:
                    news_items.append(item)
                    
            return news_items
            
        except Exception as e:
            self.logger.error(f"獲取新聞列表失敗: {str(e)}", exc_info=True)
            return []

    def crawl(self) -> Generator[Dict, None, None]:
        """
        爬取新聞
        Args:
            max_pages (int): 最大爬取頁數，預設2頁以確保獲取足夠的24小時內新聞
        Yields:
            Dict: 新聞資料
        """
        total_fetched = 0
        page = 1    
        need_fetching = True
        page_size = self.DEFAULT_PAGE_SIZE
        
        while need_fetching:
            news_list = self.get_news_list(page=page, page_size=page_size)
            # 如果當前頁面的新聞數量小於預設值,表示已經沒有更多新聞,不需要繼續爬取下一頁
            if len(news_list) < self.DEFAULT_PAGE_SIZE:
                self.logger.info(f"下輪新聞內容數量({len(news_list)})小於預設值({self.DEFAULT_PAGE_SIZE}),將會停止爬取")
                need_fetching = False
            else:
                page += 1
                
            for news in news_list:
                try:
                    # 從API回應中提取資料
                    article_data = {
                        'title': news['HeadLine'],
                        'url': news['PageUrl'],
                        'publish_time': datetime.strptime(
                            news['CreateTime'], 
                            '%Y/%m/%d %H:%M'
                        ),
                        'source': '中央社',
                        'category': self.categories_map[self.category]
                    }
                    
                    # 獲取並解析文章內容
                    article_content = self.get_article_content(article_data['url'])
                    if article_content:
                        article_data.update(article_content)
                        total_fetched += 1
                        yield article_data
                        
                except Exception as e:
                    self.logger.error(
                        f"處理新聞失敗 {news.get('PageUrl', '')}: {str(e)}", 
                        exc_info=True
                    )
                    continue
            
            self.logger.info(f"已爬取 {total_fetched} 篇24小時內的新聞")

    def get_article_content(self, url: str) -> Optional[Dict]:
        """
        獲取文章內容
        Args:
            url (str): 文章URL
        Returns:
            Optional[Dict]: 文章內容
        """
        try:
            # 使用父類的_request_with_retry方法
            response = self._request_with_retry(url)
            
            soup = BeautifulSoup(response.text, 'lxml')
            content_element = soup.select_one('div.paragraph')
            
            if not content_element:
                self.logger.warning(f"找不到文章內容: {url}")
                return None
                
            content = self._clean_content(content_element)
            if not content:
                return None
                
            return {
                'content': content
            }
            
        except Exception as e:
            self.logger.error(f"獲取文章內容失敗 {url}: {str(e)}", exc_info=True)
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