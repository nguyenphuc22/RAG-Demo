import streamlit as st
import google.generativeai as genai
from data.mongodb_client import init_mongodb_connection, get_collection
from database.NewsCrawlerInterface import NewsCrawlerInterface
from database.baophapluat import BaoPhapLuatExcelCrawler
from database.dantri import DanTriExcelCrawler
from database.thanhnien_crawler import ThanhNienExcelCrawler
from database.thuvienphapluat import ThuVienPhapLuatExcelCrawler
from database.tuoitre_crawler import TuoiTreExcelCrawler
from database.vnexpress_crawler import VnExpressExcelCrawler
from embedding.embedding_model import load_embedding_model
from search.vector_search import get_search_result, create_vector_and_update_mongodb

# Streamlit interface for API keys and connection string
st.sidebar.title("Configuration")
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")
mongo_connection_string = st.sidebar.text_input("MongoDB Connection String", type="password")
max_articles = st.sidebar.number_input("Maximum number of articles to crawl", min_value=1, max_value=100, value=20)
client = init_mongodb_connection(mongo_connection_string)

crawler_options = {
    "VnExpress": VnExpressExcelCrawler,
    "Tuổi Trẻ": TuoiTreExcelCrawler,
    "Thanh Niên": ThanhNienExcelCrawler,
    "Dân Trí": DanTriExcelCrawler,
    "Báo Pháp Luật": BaoPhapLuatExcelCrawler,
    "Thư Viện Pháp Luật": ThuVienPhapLuatExcelCrawler
}
selected_crawler = st.sidebar.selectbox("Select Crawler", list(crawler_options.keys()))

def crawl_and_update(crawler: NewsCrawlerInterface, max_articles: int):
    with st.spinner(f'Crawling up to {max_articles} new articles...'):
        crawler.crawl(max_articles=max_articles)
        df = crawler.save_to_excel("articles.xlsx")
    st.sidebar.success("Crawling completed!")

    with st.spinner('Creating vector embeddings and updating MongoDB...'):
        collection.delete_many({})
        print("All documents deleted from the collection.")
        create_vector_and_update_mongodb(df,collection)

if client:
    collection = get_collection(client, "sample_mflix", "vnexpress_articles")
    print(f"Number of documents in collection: {collection.count_documents({})}")
    print("Indexes:", collection.index_information())
    embedding_model = load_embedding_model()

    # Gemini setup
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
    else:
        st.error("Please provide a Gemini API key.")
        st.stop()

    if st.sidebar.button("Crawl New Articles"):
        crawler_class = crawler_options[selected_crawler]
        crawler = crawler_class()
        crawl_and_update(crawler, max_articles)

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