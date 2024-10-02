import streamlit as st
from sentence_transformers import SentenceTransformer
import pymongo
from tqdm import tqdm
from underthesea import sent_tokenize, word_tokenize

@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("keepitreal/vietnamese-sbert")

def get_embedding(text: str) -> list[float]:
    if not text.strip():
        print("Attempted to get embedding for empty text.")
        return []
    model = load_embedding_model()
    embedding = model.encode(text)
    return embedding.tolist()
#
# def preprocess_text(text: str) -> str:
#     # Tokenize and join to create a preprocessed string
#     return " ".join(word_tokenize(text.lower()))
#
#
# def update_mongodb_embeddings_batched(connection_string, db_name, collection_name, batch_size=100):
#     client = pymongo.MongoClient(connection_string)
#     db = client[db_name]
#     collection = db[collection_name]
#
#     total_documents = collection.count_documents({})
#
#     for i in tqdm(range(0, total_documents, batch_size), desc="Updating embeddings"):
#         batch = list(collection.find().skip(i).limit(batch_size))
#
#         for document in batch:
#             text_for_embedding = f"{document['title']} {document['date']} {document['chunk_content']}"
#             preprocessed_text = preprocess_text(text_for_embedding)
#             new_embedding = get_embedding(preprocessed_text)
#
#             collection.update_one(
#                 {"_id": document["_id"]},
#                 {"$set": {"embedding": new_embedding}}
#             )
#
#     print("All documents updated with new embeddings.")
#
#
# def update_mongodb_index(connection_string, db_name, collection_name):
#     client = pymongo.MongoClient(connection_string)
#     db = client[db_name]
#     collection = db[collection_name]
#
#     # Lấy danh sách các chỉ mục hiện có
#     existing_indexes = collection.index_information()
#
#     # Tìm và xóa chỉ mục vector cũ nếu tồn tại
#     vector_index_name = None
#     for index_name, index_info in existing_indexes.items():
#         if 'embedding' in index_info['key'][0]:
#             vector_index_name = index_name
#             break
#
#     if vector_index_name:
#         print(f"Dropping existing vector index: {vector_index_name}")
#         collection.drop_index(vector_index_name)
#     else:
#         print("No existing vector index found.")
#
#     # Tạo chỉ mục mới
#     print("Creating new vector index...")
#     collection.create_index([("embedding", pymongo.ASCENDING)], name="vector_index_new", dimension=768)
#
#     print("Vector index updated successfully.")
#
# connection_string = "mongodb+srv://phuc:pBWtKzGm3jHnMxsr@cluster0.llq9qnt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# db_name = "sample_mflix"
# collection_name = "minh_articles"
# update_mongodb_embeddings_batched(connection_string, db_name, collection_name)
# update_mongodb_index(connection_string, db_name, collection_name)