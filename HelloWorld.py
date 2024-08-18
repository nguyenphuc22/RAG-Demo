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
collection = db['embedding_for_vector_search']

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
            "name": 1,
            "description": 1,
            "price": 1,
            "rating": 1,
            "score": {
                "$meta": "vectorSearchScore"
            }
        }
    }

    pipeline = [vector_search_stage, unset_stage, project_stage]
    results = collection.aggregate(pipeline)
    return list(results)


def get_search_result(query, collection):
    get_knowledge = vector_search(query, collection, 10)
    print("get_knowledge")
    print(get_knowledge)
    search_result = ""
    for i, result in enumerate(get_knowledge, 1):
        search_result += f"\n {i}) Name: {result.get('name', 'N/A')}"
        search_result += f", Price: {result.get('price', 'N/A')}"
        search_result += f", Rating: {result.get('rating', 'N/A')}"
    return search_result


st.title("💬 RAG Chatbot")
st.caption("🚀 A Streamlit chatbot powered by Gemini and MongoDB")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you with product information?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    source_information = get_search_result(prompt.lower(), collection)
    combined_prompt = f"Become a sales consultant for a phone store. Customer's question: {prompt}\nAnswer the question based on the following product information: {source_information}."
    print(combined_prompt)

    response = model.generate_content(combined_prompt)
    msg = response.text
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

st.sidebar.title("About")
st.sidebar.info("This chatbot uses RAG with MongoDB and Gemini to provide product information.")