import streamlit as st
import pymongo
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

# MongoDB connection
client = pymongo.MongoClient('mongodb+srv://phuc:pBWtKzGm3jHnMxsr@cluster0.llq9qnt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["sample_mflix"]
collection = db['vnexpress_articles']

print(f"Number of documents in collection: {collection.count_documents({})}")
print("Indexes:", collection.index_information())

# Load the embedding model
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")

# Gemini setup
genai.configure(api_key="AIzaSyDCsPcaLrlae0cRyxEJNm5mkzdCi6bAfkQ")
model = genai.GenerativeModel('gemini-1.5-pro')

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

def get_search_result(query, collection):
    get_knowledge = vector_search(query, collection, 5)
    print("get_knowledge")
    print(get_knowledge)
    search_result = ""
    for i, result in enumerate(get_knowledge, 1):
        search_result += f"\n{i}) Title: {result.get('title', 'N/A')}"
        search_result += f"\nURL: {result.get('url', 'N/A')}"
        search_result += f"\nDescription: {result.get('description', 'N/A')[:200]}..."  # Limit description length
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