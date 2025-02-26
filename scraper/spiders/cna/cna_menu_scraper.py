from scraper.spiders.base_spider import BaseNewsSpider
import json
import os
from typing import Dict
from bs4 import BeautifulSoup
from scraper.utils.logger import setup_logger

# 使用自定義的logger設置
logger = setup_logger(__name__)

class CnaMenuScraper(BaseNewsSpider):
    """爬取中央社主選單類別的爬蟲"""
    
    name = "cna_menu"
    
    def __init__(self):
        super().__init__()
        self.url = "https://www.cna.com.tw/list/aspt.aspx"
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 設定配置文件路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.join(current_dir, 'configs')
        self.config_path = os.path.join(self.config_dir, 'categories.json')
        
        # 確保配置目錄存在
        os.makedirs(self.config_dir, exist_ok=True)

    def get_menu_mapping(self, force_update=False) -> Dict[str, str]:
        """
        獲取類別映射，優先從配置文件讀取，
        如果配置文件不存在或強制更新則重新爬取
        
        Args:
            force_update (bool): 是否強制更新配置
            
        Returns:
            Dict[str, str]: 格式為 {'aall': '即時', 'aipl': '政治', ...}
        """
        if not force_update and os.path.exists(self.config_path):
            return self._load_config()
            
        menu_mapping = self._scrape_menu_mapping()
        if menu_mapping:
            self._save_config(menu_mapping)
        return menu_mapping

    def _load_config(self) -> Dict[str, str]:
        """從配置文件讀取類別映射"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"讀取配置文件失敗: {str(e)}")
            return {}

    def _save_config(self, menu_mapping: Dict[str, str]) -> None:
        """保存類別映射到配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(menu_mapping, f, ensure_ascii=False, indent=2)
            self.logger.info("配置文件已更新")
        except Exception as e:
            self.logger.error(f"保存配置文件失敗: {str(e)}")

    def _scrape_menu_mapping(self) -> Dict[str, str]:
        """爬取主選單類別映射"""
        try:
            response = self._request_with_retry(self.url)
            soup = BeautifulSoup(response.text, 'lxml')
            menu = soup.select_one('.main-menu')
            
            menu_mapping = {}
            for link in menu.select('a.first-level'):
                category_code = link['href'].split('/')[-1].replace('.aspx', '')
                category_name = link.text.strip()
                menu_mapping[category_code] = category_name
                
            self.logger.info(f"成功爬取{len(menu_mapping)}個類別映射")
            return menu_mapping
            
        except Exception as e:
            self.logger.error(f"爬取類別映射失敗: {str(e)}")
            return {}

def main():
    """更新類別配置文件"""
    scraper = CnaMenuScraper()
    menu_mapping = scraper.get_menu_mapping(force_update=True)
    print("類別對應表:")
    for code, name in menu_mapping.items():
        print(f"{code}: {name}")

if __name__ == "__main__":
    main() 