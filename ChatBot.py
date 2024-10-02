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
from evalution.question import evaluation
from search.vector_search import get_search_result, create_vector_and_update_mongodb, preprocess_text
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Streamlit interface for API keys and connection string
st.sidebar.title("Configuration")
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")
mongo_connection_string = st.sidebar.text_input("MongoDB Connection String", type="password")
max_articles = st.sidebar.number_input("Maximum number of articles to crawl", min_value=1, max_value=100, value=20)
client = init_mongodb_connection(mongo_connection_string)
db_name = "sample_mflix"
collection_name = "minh_articles"

crawler_options = {
    # "VnExpress": VnExpressExcelCrawler,
    "Tuổi Trẻ": TuoiTreExcelCrawler,
    "Thanh Niên": ThanhNienExcelCrawler,
    "Dân Trí": DanTriExcelCrawler,
    # "Báo Pháp Luật": BaoPhapLuatExcelCrawler,
    # "Thư Viện Pháp Luật": ThuVienPhapLuatExcelCrawler,
    "VTV": VTVExcelCrawler
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

selected_crawler = st.sidebar.selectbox("Select Crawler", list(crawler_options.keys()))
if 'show_form' not in st.session_state:
    st.session_state.show_form = False


def get_context_aware_query(current_query):
    if len(st.session_state.messages) < 2:
        return current_query

    previous_query = st.session_state.messages[-2]["content"] if st.session_state.messages[-2]["role"] == "user" else ""
    previous_response = st.session_state.messages[-1]["content"] if st.session_state.messages[-1][
                                                                        "role"] == "assistant" else ""

    context_aware_query = f"""
    Dựa trên cuộc hội thoại sau:
    Câu hỏi trước: {previous_query}
    Câu trả lời trước: {previous_response}
    Câu hỏi hiện tại: {current_query}

    Hãy tạo ra một câu hỏi mới kết hợp ngữ cảnh từ câu hỏi trước và câu hỏi hiện tại để tìm kiếm thông tin liên quan.
    Chỉ đưa ra câu hỏi mới, không cần giải thích gì thêm.
    """

    try:
        response = model.generate_content(context_aware_query)
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi khi tạo câu hỏi có ngữ cảnh: {str(e)}")
        return current_query


def crawl_and_update(crawler: NewsCrawlerInterface, max_articles: int):
    with st.spinner(f'Crawling up to {max_articles} new articles...'):
        crawler.crawl(max_articles=max_articles)
        df = crawler.save_to_excel("articles.xlsx")
    st.sidebar.success("Crawling completed!")

    with st.spinner('Creating vector embeddings and updating MongoDB...'):
        collection.delete_many({})
        print("All documents deleted from the collection.")
        create_vector_and_update_mongodb(df, collection)


def get_latest_articles(collection, limit=3):
    """Lấy các bài viết mới nhất từ cơ sở dữ liệu."""
    latest_articles = list(collection.find().sort("date", -1).limit(limit))
    return latest_articles


def generate_question_suggestions(model, articles, conversation_history):
    """Tạo gợi ý câu hỏi dựa trên các bài viết mới nhất và lịch sử trò chuyện."""
    if conversation_history.strip():
        context = f"""
        Dựa trên lịch sử trò chuyện sau đây, hãy đề xuất 3 câu hỏi mà người dùng có thể quan tâm:

        Lịch sử trò chuyện:
        {conversation_history}

        Hãy đưa ra 3 câu hỏi gợi ý liên quan đến cuộc trò chuyện hiện tại. Chỉ liệt kê các câu hỏi, không cần thêm giải thích hay định dạng khác.
        """
    else:
        context = f"""
        Dựa trên các bài viết mới nhất sau đây, hãy đề xuất 3 câu hỏi mà người dùng có thể quan tâm:

        Các bài viết mới nhất:
        {', '.join([article['title'] for article in articles])}

        Hãy đưa ra 3 câu hỏi gợi ý liên quan đến các chủ đề trong các bài viết mới. Chỉ liệt kê các câu hỏi, không cần thêm giải thích hay định dạng khác.
        """

    try:
        response = model.generate_content(context, safety_settings=safety_settings)
        suggestions = response.text.strip().split('\n')
        return suggestions[:3]  # Đảm bảo chỉ trả về tối đa 3 gợi ý
    except Exception as e:
        print(f"Lỗi khi tạo gợi ý câu hỏi: {str(e)}")
        return []


def process_user_input(user_input, model, collection):
    print(f"Processing user input: {user_input}")  # Debug print
    st.session_state.messages.append({"role": "user", "content": user_input})

    context_aware_query = get_context_aware_query(user_input)
    preprocessed_prompt = preprocess_text(context_aware_query)

    source_information = get_search_result(preprocessed_prompt, collection)
    combined_prompt = update_prompt_with_history(CHATBOT_PROMPT, user_input, source_information)
    print(f"Context-aware query: {context_aware_query}")
    print(combined_prompt)

    try:
        response = model.generate_content(combined_prompt, safety_settings=safety_settings)
        msg = response.text
    except Exception as e:
        msg = f"Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": msg})

def handle_suggestion_click(suggestion):
    st.session_state.selected_question = suggestion
    st.rerun()

if client:
    collection = get_collection(client, db_name, collection_name)
    print(f"Number of documents in collection: {collection.count_documents({})}")
    print("Indexes:", collection.index_information())
    embedding_model = load_embedding_model()

    # Gemini setup
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.error("Please provide a valid Gemini API key.")
        st.stop()

    if st.sidebar.button("Crawl New Articles"):
        print("Crawling new articles...")
        crawler_class = crawler_options[selected_crawler]
        crawler = crawler_class()
        crawl_and_update(crawler, max_articles)
    
    if st.sidebar.button("Show/Hide Evaluate"):
        st.session_state.show_form = not st.session_state.show_form 

    evaluation(collection, model)
    st.title("💬 Improved Hybrid Search RAG Chatbot")
    st.caption(
        "🚀 A Streamlit chatbot powered by Gemini and MongoDB, using Enhanced Hybrid Search with Semantic Reranking")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant",
                                      "content": "Xin chào! Tôi có thể giúp gì cho bạn về các tin tức từ các nguồn tin tức Việt Nam?"}]

    if "selected_question" not in st.session_state:
        st.session_state.selected_question = None

    # Xử lý câu hỏi đã chọn từ lần chạy trước
    if st.session_state.selected_question:
        process_user_input(st.session_state.selected_question, model, collection)
        st.session_state.selected_question = None  # Reset sau khi xử lý

    # Hiển thị tất cả tin nhắn
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Thêm phần gợi ý câu hỏi
    latest_articles = get_latest_articles(collection)
    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-5:]])
    question_suggestions = generate_question_suggestions(model, latest_articles, conversation_history)

    if question_suggestions:
        st.sidebar.subheader("Gợi ý câu hỏi:")
        for i, suggestion in enumerate(question_suggestions):
            print(f"Suggestion {i + 1}: {suggestion}")
            st.sidebar.button(suggestion, key=f"suggestion_{i}", on_click=handle_suggestion_click, args=(suggestion,))


    if prompt := st.chat_input():
        process_user_input(prompt, model, collection)
        st.rerun()

    st.sidebar.title("Giới thiệu")
    st.sidebar.info(
        "Chatbot này sử dụng Hybrid Search cải tiến với Semantic Reranking, MongoDB và Gemini để cung cấp thông tin từ các bài báo từ nhiều nguồn tin tức Việt Nam.")

else:
    st.error("Please configure MongoDB connection to continue.")