import pandas as pd
from database.NewsCrawlerInterface import NewsCrawlerInterface


class UniversalExcelCrawler(NewsCrawlerInterface):
    def __init__(self, base_url='https://vnexpress.net/'):
        self.base_url = base_url
        self.articles = []

    def crawl(self, max_articles: int) -> None:
        # TODO: Implement this method
        pass
    def save_to_excel(self, filename: str) -> pd.DataFrame:
        # TODO: Implement this method
        pass

    def get_articles(self) -> list[dict]:
        # TODO: Implement this method
        pass
