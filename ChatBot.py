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
from database.vtv_crawler import VTVExcelCrawler
from embedding.embedding_model import load_embedding_model
from prompts.history import update_prompt_with_history
from prompts.prompt import CHATBOT_PROMPT
from search.vector_search import get_search_result, create_vector_and_update_mongodb, preprocess_text

# Streamlit interface for API keys and connection string
st.sidebar.title("Configuration")
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")
mongo_connection_string = st.sidebar.text_input("MongoDB Connection String", type="password")
max_articles = st.sidebar.number_input("Maximum number of articles to crawl", min_value=1, max_value=100, value=20)
client = init_mongodb_connection(mongo_connection_string)
db_name = "sample_mflix"
collection_name = "minh_articles"
# collection_name = "minh_articles"

crawler_options = {
    "VnExpress": VnExpressExcelCrawler,
    "Tuổi Trẻ": TuoiTreExcelCrawler,
    "Thanh Niên": ThanhNienExcelCrawler,
    "Dân Trí": DanTriExcelCrawler,
    "Báo Pháp Luật": BaoPhapLuatExcelCrawler,
    "Thư Viện Pháp Luật": ThuVienPhapLuatExcelCrawler,
    "VTV": VTVExcelCrawler
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
        create_vector_and_update_mongodb(df, collection)

if client:
    collection = get_collection(client, db_name, collection_name)
    print(f"Number of documents in collection: {collection.count_documents({})}")
    print("Indexes:", collection.index_information())
    embedding_model = load_embedding_model()

    # Gemini setup
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
    else:
        st.error("Please provide a valid Gemini API key.")
        st.stop()

    if st.sidebar.button("Crawl New Articles"):
        print("Crawling new articles...")
        crawler_class = crawler_options[selected_crawler]
        crawler = crawler_class()
        crawl_and_update(crawler, max_articles)

    st.title("💬 Improved Hybrid Search RAG Chatbot")
    st.caption("🚀 A Streamlit chatbot powered by Gemini and MongoDB, using Enhanced Hybrid Search with Semantic Reranking")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "Xin chào! Tôi có thể giúp gì cho bạn về các tin tức từ các nguồn tin tức Việt Nam?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        preprocessed_prompt = preprocess_text(prompt)
        source_information = get_search_result(preprocessed_prompt, collection)
        combined_prompt = update_prompt_with_history(CHATBOT_PROMPT, prompt, source_information)
        print(combined_prompt)

        try:
            response = model.generate_content(combined_prompt)
            msg = response.text
        except Exception as e:
            msg = f"Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn: {str(e)}"

        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

    st.sidebar.title("Giới thiệu")
    st.sidebar.info("Chatbot này sử dụng Hybrid Search cải tiến với Semantic Reranking, MongoDB và Gemini để cung cấp thông tin từ các bài báo từ nhiều nguồn tin tức Việt Nam.")

else:
    st.error("Please configure MongoDB connection to continue.")