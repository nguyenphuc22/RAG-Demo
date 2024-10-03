import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import math
from database.NewsCrawlerInterface import NewsCrawlerInterface

class ThanhNienExcelCrawler(NewsCrawlerInterface):
    def __init__(self, base_url='https://thanhnien.vn'):
        self.base_url = base_url
        self.max_articles = 0
        self.articles = []
        self.categories = []
        self.mapping_categories = [
            {"url": "/thoi-su.htm", "id": 1854},
            {"url": "/the-gioi.htm", "id": 18566},
            {"url": "/kinh-te.htm", "id": 18549},
            {"url": "/doi-song.htm", "id": 18517},
            {"url": "/suc-khoe.htm", "id": 18565},
            {"url": "/gioi-tre.htm", "id": 18569},
            {"url": "/giao-duc.htm", "id": 18526},
            {"url": "/du-lich.htm", "id": 185234},
            {"url": "/van-hoa.htm", "id": 18593},
            {"url": "/giai-tri.htm", "id": 185285},
            {"url": "/the-thao.htm", "id": 185318},
            {"url": "/cong-nghe.htm", "id": 185315},
            {"url": "/xe.htm", "id": 185317},
            # {"url": "/video.htm", "id": 63},
            {"url": "/tieu-dung-thong-minh.htm", "id": 185132},
            # {"url": "/thoi-trang-tre.htm", "id": 63},
        ]

    def get_page_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.HTTPError as e:
                print(f"Error fetching {url}: {e}")
                return None
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_categories(self):
        html_content = self.get_page_content(self.base_url)

        if not html_content:
            return
        soup = BeautifulSoup(html_content, "html.parser")

        # Get categories
        content_element = soup.find("ul", class_="menu-nav")
        href_list = content_element.findAll("a", class_="nav-link")
        # Remove first categories (Trang chủ, Video và thời trang trẻ)
        for a in href_list:
            if self.find_category_id(a['href']) is not None:
                self.categories.append({'url' : a['href'], 'max' : math.ceil(self.max_articles / (len(href_list)- 3))})
        if len(self.categories) == 0:
            print("Không tìm thấy categories")

    # Get html of categories
    def get_articles_categories(self, category):
        html_content = self.get_page_content(self.base_url + category["url"])
        soup = BeautifulSoup(html_content, "html.parser")
        count_articles_category = 0
        page = 1
        if not html_content:
            return
        count_articles_category = self.parse_articles(soup, category, page, count_articles_category)
        print(category["url"] + ' count: ' + str(count_articles_category))

        # Handle next page
        while (count_articles_category < category["max"] and len(self.articles) <= self.max_articles):
            page += 1
            count_articles_category = self.parse_articles(None, category, page, count_articles_category)
            print(category["url"] + ' count: ' + str(count_articles_category))

    def parse_articles(self, soup, category, page, count_articles_category):
        category_id = self.find_category_id(category["url"])
        if category_id is None:
            return
        if page == 1:
            results = []
            box_main = soup.find('div', class_='box-category-item-main')
            # Main articles
            item_first = box_main.find('div', class_='item-first')
            if item_first:
                results.append(item_first)

            # Related articles
            item_related = box_main.find('div', class_='item-related')
            if item_related:
                item_related_list = item_related.find_all('div', class_='box-category-item')
                if item_related_list :
                    results.extend(item_related_list)

            # Sub articles
            box_sub = soup.find('div', class_='box-category-sub')
            if box_sub:
                sub_item_list = box_sub.find_all('div', class_='box-category-item')
                if sub_item_list:
                    results.extend(sub_item_list)

            for item in results:
                if count_articles_category >= category['max'] or len(self.articles) > self.max_articles:
                    break
                url_element = item.find('a', class_='box-category-link-title')
                url, title = self.get_url_and_title(url_element)
                description, content, date = self.get_article_details(url)
                count_articles_category += 1
                self.articles.append({
                    'title': title,
                    'url': url,
                    'description': description,
                    'content': content,
                    'date': date
                })
        

        # List articles
        if page > 1 :
            category_id = self.find_category_id(category["url"])
            # Biến đổi URL thành dạng có số trang
            page_url = self.base_url + '/timelinelist/' + str(category_id) + f'/{page}.htm'
            print(f"Page {page_url}")
            html_content = self.get_page_content(page_url)
            soup = BeautifulSoup(html_content, "html.parser")
            article_list = soup.find_all("div", class_="box-category-item")
            if not soup:
                print("Category không thể truy cập")
                return False
        else :
            stream_main = soup.find("div", class_="list__stream-main")
            article_list = stream_main.find_all("div", class_="box-category-item")
            print("stream_main")

        for article in article_list:
            if (count_articles_category >= category["max"] or len(self.articles) > self.max_articles):
                break
            url_element = article.find("a", class_="box-category-link-title")
            url, title = self.get_url_and_title(url_element)
            description, content, date = self.get_article_details(url)
            count_articles_category += 1
            self.articles.append(
                {
                    "title": title,
                    "url": url,
                    "description": description,
                    "content": content,
                    "date": date,
                }
            )
        return count_articles_category
    
     # Find category_id in maaping
    def find_category_id(self, url_to_find):
        for category in self.mapping_categories:
            if category["url"] == url_to_find:
                return category["id"]
        return None 
    
    def get_url_and_title(self, url_element):
        url = ""
        title = ""
        if url_element is not None:
            url = self.base_url + url_element["href"]
            print(url)
            title = url_element["title"]
        return url, title
    def get_article_details(self, url):
        html_content = self.get_page_content(url)
        if not html_content:
            return "",

        soup = BeautifulSoup(html_content, "html.parser")
        description_element = soup.find("h2", class_="detail-sapo")
        description = description_element.text.strip() if description_element else ""
        # Extract content
        content_element = soup.find("div", class_="detail-content")
        content = content_element.text.strip() if content_element else ""

        # Extract date
        detail_time = soup.find("div", class_="detail-time")

        if detail_time:
            date_element = detail_time.div
            if date_element: 
                date_text = date_element.text.strip()
                date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
                match = re.search(date_pattern, date_text)
                if match:
                    date_str = match.group(1)
                    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                    print(f"Ngày đăng bài: {date_obj.strftime('%d/%m/%Y')}")
                else:
                    print("Không tìm thấy ngày đăng bài")
                    date_obj = ""
            else:
                    print("Không tìm thấy ngày đăng bài")
                    date_obj = ""
        else:
            print("Không tìm thấy ngày đăng bài")
            date_obj = ""

        return (
            description,
            content,
            date_obj.strftime("%d/%m/%Y") if isinstance(date_obj, datetime) else "",
        )
    
    def crawl(self, max_articles: int) -> None:
        self.max_articles = max_articles
        self.get_categories()
        
        print(self.categories)

        for category in self.categories:
            print(category["url"])
            self.get_articles_categories(category)

        self.articles = self.articles[:max_articles]

    def save_to_excel(self, filename: str = 'thanhnien_articles.xlsx') -> pd.DataFrame:
        df = pd.DataFrame(self.articles)
        df.to_excel(filename, index=False)
        print(f"Saved {len(self.articles)} articles to {filename}")
        return df

    def get_articles(self) -> list[dict]:
        return self.articles