import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random


class VnExpressExcelCrawler:
    def __init__(self, base_url='https://vnexpress.net/'):
        self.base_url = base_url
        self.articles = []

    def get_page_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_articles(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        for article in soup.find_all('article', class_='item-news'):
            title_element = article.find('h3', class_='title-news')
            if title_element and title_element.a:
                title = title_element.a.text.strip()
                url = title_element.a['href']
                description = article.find('p', class_='description')
                description = description.text.strip() if description else ""
                self.articles.append({
                    'title': title,
                    'url': url,
                    'description': description
                })

    def crawl(self, max_articles=50, delay_range=(1, 3)):
        html_content = self.get_page_content(self.base_url)
        if not html_content:
            return

        self.parse_articles(html_content)

        while len(self.articles) < max_articles:
            time.sleep(random.uniform(*delay_range))
            next_page = self.find_next_page(html_content)
            if not next_page:
                break
            html_content = self.get_page_content(next_page)
            if not html_content:
                break
            self.parse_articles(html_content)

        self.articles = self.articles[:max_articles]

    def find_next_page(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        next_page_link = soup.find('a', class_='next-page')
        return next_page_link['href'] if next_page_link else None

    def save_to_excel(self, filename='vnexpress_articles.xlsx'):
        df = pd.DataFrame(self.articles)
        df.to_excel(filename, index=False)
        print(f"Saved {len(self.articles)} articles to {filename}")


if __name__ == "__main__":
    crawler = VnExpressExcelCrawler()
    crawler.crawl(max_articles=50)
    crawler.save_to_excel()