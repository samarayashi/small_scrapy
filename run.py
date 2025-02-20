from scraper.spiders.cna.cna_menu_scraper import CnaMenuScraper
from scraper.spiders.cna.cna_spider import CnaSpider

def update_menu_config():
    """更新類別配置文件"""
    scraper = CnaMenuScraper()
    menu_mapping = scraper.get_menu_mapping(force_update=True)
    print("類別對應表:")
    for code, name in menu_mapping.items():
        print(f"{code}: {name}")

def test_news_scraper():
    """測試新聞爬蟲"""
    spider = CnaSpider(category='ait')
    articles = list(spider.fetch_news_list())
    print(f"成功爬取 {len(articles)} 篇文章")
    for article in articles:
        print(f"標題: {article['title']}")
    
    # 測試單一篇文章
    article = articles[0]
    print(f"測試單一篇文章: {article['title']}")
    print(f"發布時間: {article['publish_time']}")
    print(f"連結: {article['url']}")
    
    # 測試單一篇文章的內容
    content = spider.fetch_article(article)
    print(f"文章內容: {content}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("請指定要執行的功能：")
        print("python run.py menu  # 更新選單配置")
        print("python run.py news  # 測試新聞爬蟲")
        sys.exit(1)
    
    command = sys.argv[1]
    if command == "menu":
        update_menu_config()
    elif command == "news":
        test_news_scraper()
    else:
        print(f"未知的命令: {command}") 