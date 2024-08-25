import streamlit as st
import pymongo
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Streamlit interface for API keys and connection string
st.sidebar.title("Configuration")
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")
mongo_connection_string = st.sidebar.text_input("MongoDB Connection String", type="password")

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


# MongoDB connection
@st.cache_resource
def init_mongodb_connection(connection_string):
    if not connection_string:
        st.error("Please provide a MongoDB connection string.")
        return None
    try:
        client = pymongo.MongoClient(connection_string)
        client.admin.command('ping')
        st.sidebar.success("Successfully connected to MongoDB!")
        return client
    except Exception as e:
        st.sidebar.error(f"Failed to connect to MongoDB: {e}")
        return None

client = init_mongodb_connection(mongo_connection_string)

if client:
    db = client["sample_mflix"]
    collection = db['vnexpress_articles']

    print(f"Number of documents in collection: {collection.count_documents({})}")
    print("Indexes:", collection.index_information())

    # Load the embedding model
    @st.cache_resource
    def load_embedding_model():
        return SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")

    embedding_model = load_embedding_model()

    # Gemini setup
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
    else:
        st.error("Please provide a Gemini API key.")
        st.stop()

    def get_embedding(text: str) -> list[float]:
        if not text.strip():
            print("Attempted to get embedding for empty text.")
            return []
        embedding = embedding_model.encode(text)
        return embedding.tolist()

    def vector_search(user_query, collection, limit=4):
        query_embedding = get_embedding(user_query)
        if not query_embedding:
            return "Invalid query or embedding generation failed."

        vector_search_stage = {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": 400,
                "limit": limit,
            }
        }

        unset_stage = {"$unset": "embedding"}

        project_stage = {
            "$project": {
                "_id": 0,
                "title": 1,
                "url": 1,
                "description": 1,
                "score": {
                    "$meta": "vectorSearchScore"
                }
            }
        }

        pipeline = [vector_search_stage, unset_stage, project_stage]
        results = collection.aggregate(pipeline)
        return list(results)


    if st.sidebar.button("Crawl New Articles"):
        crawler = VnExpressExcelCrawler()
        with st.spinner('Crawling new articles...'):
            crawler.crawl(max_articles=20)  # Crawl 20 bài viết mới
            crawler.save_to_excel()
        st.sidebar.success("Crawling completed!")

    def get_search_result(query, collection):
        get_knowledge = vector_search(query, collection, 5)
        print("get_knowledge")
        print(get_knowledge)
        search_result = ""
        for i, result in enumerate(get_knowledge, 1):
            search_result += f"\n{i}) Title: {result.get('title', 'N/A')}"
            search_result += f"\nURL: {result.get('url', 'N/A')}"
            search_result += f"\nDescription: {result.get('description', 'N/A')[:200]}..."
            search_result += "\n\n"
        return search_result

    st.title("💬 VnExpress RAG Chatbot")
    st.caption("🚀 A Streamlit chatbot powered by Gemini and MongoDB, using VnExpress articles")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "Xin chào! Tôi có thể giúp gì cho bạn về các tin tức từ VnExpress?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        source_information = get_search_result(prompt.lower(), collection)
        combined_prompt = f"""Bạn là một trợ lý AI được đào tạo để trả lời các câu hỏi dựa trên các bài báo từ VnExpress. 
        Câu hỏi của người dùng: {prompt}
        Hãy trả lời câu hỏi dựa trên thông tin sau từ các bài báo liên quan: 
        {source_information}
        Nếu thông tin không đủ để trả lời câu hỏi, hãy nói rằng bạn không có đủ thông tin và đề nghị người dùng đặt câu hỏi khác hoặc cung cấp thêm ngữ cảnh.
        Luôn trả lời bằng tiếng Việt và giữ giọng điệu thân thiện, chuyên nghiệp."""
        print(combined_prompt)

        response = model.generate_content(combined_prompt)
        msg = response.text
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

    st.sidebar.title("Giới thiệu")
    st.sidebar.info("Chatbot này sử dụng RAG với MongoDB và Gemini để cung cấp thông tin từ các bài báo VnExpress.")
else:
    st.error("Please configure MongoDB connection to continue.")