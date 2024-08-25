from abc import ABC, abstractmethod
import pandas as pd

class NewsCrawlerInterface(ABC):
    @abstractmethod
    def crawl(self, max_articles: int) -> None:
        """Crawl articles from the news source."""
        pass

    @abstractmethod
    def save_to_excel(self, filename: str) -> pd.DataFrame:
        """Save crawled articles to an Excel file and return a DataFrame."""
        pass

    @abstractmethod
    def get_articles(self) -> list[dict]:
        """Return the list of crawled articles."""
        pass