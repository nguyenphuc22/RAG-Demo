import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import math
from database.NewsCrawlerInterface import NewsCrawlerInterface

class DanTriExcelCrawler(NewsCrawlerInterface):
    def __init__(self, base_url='https://dantri.com.vn'):
        self.base_url = base_url
        self.max_articles = 0
        self.articles = []
        self.categories = []

    def get_page_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    # Get html of categories
    def get_articles_categories (self, category) :
        html_content = self.get_page_content(self.base_url + category['url'])
        soup = BeautifulSoup(html_content, 'html.parser')
        count_articles = 0

        if not html_content:
            return
        count_articles += self.parse_articles(soup, category)

        # Handle next page
        while count_articles < category['max'] and len(self.articles) <= self.max_articles:
            next_page = soup.find('a', class_='page-item next')
            if not next_page:
                return
            html_content = self.get_page_content(self.base_url + next_page['href'])
            print(f"next page {next_page['href']}")
            soup = BeautifulSoup(html_content, 'html.parser')
            if not html_content:
                return
            count_articles += self.parse_articles(soup, category)

    def parse_articles(self, soup, category):
        article_list = soup.find('div', class_='article list')
        count_articles = 0
        if not article_list:
            print('Category không thể truy cập')
            return False
        for idx, article in enumerate(article_list.find_all('article', class_='article-item')):
            if idx >= category['max'] or len(self.articles) > self.max_articles:
                break
            count_articles += 1
            title_element = article.find('h3', class_='article-title')
            description_element = article.find('h3', class_='article-excerpt')

            if title_element and title_element.a:
                title = title_element.a.text.strip()
                url = 'https://dantri.com.vn' + title_element.a['href']
                description = ""
                if description_element and description_element.a:
                    description = description_element.a.text.strip()

                # Fetch full content and date
                content, date = self.get_article_details(url)

                self.articles.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'content': content,
                    'date': date
                })
        return count_articles

    def get_article_details(self, url):
        html_content = self.get_page_content(url)
        if not html_content:
            return "", ""

        soup = BeautifulSoup(html_content, 'html.parser')
        # Extract content
        content_element = soup.find('article', class_='singular-container')
        is_magazine = False
        if not content_element:
            is_magazine = True
            content_element = soup.find('article', class_='e-magazine')
            
        content = content_element.text.strip() if content_element else ""

        # Extract date
        date_span = soup.find('time', class_='author-time')
        if not date_span and is_magazine: 
            date_span = soup.find('time', class_='e-magazine__meta-item')
        if not date_span:
            date_span = soup.find('time')

        if date_span:
            date_text = date_span.text.strip()
            date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
            match = re.search(date_pattern, date_text)
            if match:
                date_str = match.group(1)
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                print(f"Ngày đăng bài: {date_obj.strftime('%d/%m/%Y')}")
            else:
                print("Không tìm thấy ngày đăng bài")
                date_obj = ""
        else:
            print("Không tìm thấy ngày đăng bài")
            date_obj = ""

        return content, date_obj.strftime('%d/%m/%Y') if isinstance(date_obj, datetime) else ""

    def get_categories(self, max_articles) :
        html_content = self.get_page_content(self.base_url)

        if not html_content:
            return
        soup = BeautifulSoup(html_content, 'html.parser')

        # Get categories
        content_element = soup.find('ol', class_="nf-menu")
        href_list = content_element.findAll('a', class_="dt-text-MineShaft")
        for a in href_list:
            self.categories.append({'url' : a['href'], 'max' : math.ceil(max_articles/ len(href_list))})
        if len(self.categories) == 0:
            print('Không tìm thấy categories')

    def crawl(self, max_articles: 1,delay_range=(1, 3)) -> None:
        self.max_articles = max_articles   
        self.get_categories(max_articles)
        print(self.get_categories)
        for category in self.categories :
            print(category['url'])
            self.get_articles_categories(category)

        self.articles = self.articles[:max_articles]

    def save_to_excel(self, filename: str = 'dantri_articles.xlsx') -> pd.DataFrame:
        valid_articles = []
        
        # Check error articles
        for article in self.articles:
            try:
                df_test = pd.DataFrame([article])
                df_test.to_excel("test.xlsx", index=False)
                
                valid_articles.append(article)
            except Exception as e:
                print(f"Bỏ qua bài viết gặp lỗi: {e}")

        # Save to excel
        try:
            df = pd.DataFrame(valid_articles)
            df.to_excel(filename, index=False)
            print(f"Đã lưu {len(valid_articles)} bài viết hợp lệ vào {filename}")
        except Exception as e:
            print(f"Lỗi trong quá trình lưu file Excel: {e}")

        return df

    def get_articles(self) -> list[dict]:
        return self.articles