import requests
from bs4 import BeautifulSoup
import logging

class BaseNewsSpider:
    name = 'base_spider'
    allowed_domains = []
    start_urls = []
    
    def __init__(self):
        self.logger = logging.getLogger(self.name)
        self.session = requests.Session()
        self.session.headers.update(self._default_headers())
        
    def _default_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
    
    def start_requests(self):
        for url in self.start_urls:
            yield self._request_with_retry(url)
            
    def _request_with_retry(self, url, retries=3):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            if retries > 0:
                self.logger.warning(f"Retrying {url}, remaining retries: {retries-1}")
                return self._request_with_retry(url, retries-1)
            else:
                self.logger.error(f"Failed to fetch {url}: {str(e)}")
                raise 