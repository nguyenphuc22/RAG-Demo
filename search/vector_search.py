import streamlit as st
from typing import List
from underthesea import sent_tokenize, word_tokenize
from embedding.embedding_model import get_embedding
from rank_bm25 import BM25Okapi
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import cosine


def preprocess_text(text: str) -> str:
    # Tokenize and join to create a preprocessed string
    return " ".join(word_tokenize(text.lower()))

def split_text(text: str, max_length: int = 512, overlap: int = 50) -> List[str]:
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " " + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def vector_search(user_query, collection, limit=20):
    query_embedding = get_embedding(preprocess_text(user_query))
    if not query_embedding:
        print("Query embedding is empty. Returning empty result.")
        return []

    vector_search_stage = {
        "$vectorSearch": {
            "index": "vector_index",
            "queryVector": query_embedding,
            "path": "embedding",
            "numCandidates": 1000,  # Increased from 400
            "limit": limit,
        }
    }

    unset_stage = {"$unset": "embedding"}

    project_stage = {
        "$project": {
            "_id": 0,
            "title": 1,
            "url": 1,
            "chunk_content": 1,
            "score": {
                "$meta": "vectorSearchScore"
            }
        }
    }

    pipeline = [vector_search_stage, unset_stage, project_stage]
    results = list(collection.aggregate(pipeline))

    # Normalize scores
    max_score = max(result['score'] for result in results) if results else 1
    for result in results:
        result['normalized_score'] = result['score'] / max_score

    return results


def keyword_search(user_query, collection, limit=10):
    # Preprocess the query
    preprocessed_query = preprocess_text(user_query)

    # Perform a text search using MongoDB's text index
    results = collection.find(
        {"$text": {"$search": preprocessed_query}},
        {"score": {"$meta": "textScore"}, "title": 1, "url": 1, "chunk_content": 1}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    results = list(results)

    # Normalize scores
    max_score = max(result['score'] for result in results) if results else 1
    for result in results:
        result['normalized_score'] = result['score'] / max_score

    return results


def reciprocal_rank_fusion(vector_results, keyword_results, k=60):
    # Combine results
    all_results = vector_results + keyword_results

    # Create a dictionary to store the best rank and scores for each document
    doc_info = {}

    for i, result in enumerate(vector_results):
        doc_id = result['url']  # Using URL as a unique identifier
        if doc_id not in doc_info or i + 1 < doc_info[doc_id]['rank']:
            doc_info[doc_id] = {
                'rank': i + 1,
                'vector_score': result['normalized_score'],
                'keyword_score': 0,
                'result': result
            }

    for i, result in enumerate(keyword_results):
        doc_id = result['url']
        if doc_id not in doc_info:
            doc_info[doc_id] = {
                'rank': i + 1,
                'vector_score': 0,
                'keyword_score': result['normalized_score'],
                'result': result
            }
        else:
            doc_info[doc_id]['keyword_score'] = result['normalized_score']
            if i + 1 < doc_info[doc_id]['rank']:
                doc_info[doc_id]['rank'] = i + 1

    # Calculate RRF score for each document
    for doc_id, info in doc_info.items():
        rrf_score = 1 / (k + info['rank'])
        combined_score = (info['vector_score'] + info['keyword_score']) / 2
        info['final_score'] = rrf_score * combined_score

    # Sort results by final score
    sorted_results = sorted(doc_info.values(), key=lambda x: x['final_score'], reverse=True)

    # Return the top results
    return [info['result'] for info in sorted_results[:10]]


def semantic_reranking(results, query, top_k=5):
    query_embedding = get_embedding(preprocess_text(query))
    if not query_embedding:
        print("Query embedding is empty. Skipping semantic reranking.")
        return results[:top_k]

    reranked_results = []
    for result in results:
        content_embedding = get_embedding(preprocess_text(result['chunk_content']))
        if not content_embedding:
            print(f"Content embedding is empty for result: {result['url']}. Skipping this result.")
            continue
        if len(query_embedding) != len(content_embedding):
            print(f"Embedding dimensions mismatch. Query: {len(query_embedding)}, Content: {len(content_embedding)}. Skipping this result.")
            continue
        result['semantic_score'] = 1 - cosine(query_embedding, content_embedding)
        reranked_results.append(result)

    return sorted(reranked_results, key=lambda x: x['semantic_score'], reverse=True)[:top_k]


def hybrid_search(user_query, collection, limit=30):
    vector_results = vector_search(user_query, collection, limit)
    print("Vector search results:")
    print(vector_results)
    # keyword_results = keyword_search(user_query, collection, limit)
    # print("Keyword search results:")
    # print(keyword_results)
    # combined_results = reciprocal_rank_fusion(vector_results, keyword_results)
    # print("Combined results:")
    # print(combined_results)
    return semantic_reranking(vector_results, user_query)


def create_vector_and_update_mongodb(df, collection):
    for _, row in df.iterrows():
        title = row['title']
        url = row['url']
        description = row['description']
        content = row['content']
        date = row['date']

        # Split the content into chunks
        chunks = split_text(content)

        for i, chunk in enumerate(chunks):
            text_for_embedding = f"{title} {date} {chunk}"
            preprocessed_text = preprocess_text(text_for_embedding)

            print(f"Adding chunk {i + 1}/{len(chunks)} for article: {title} \n URL: {url} \n Chunk: {chunk}")

            document = {
                "title": title,
                "url": url,
                "description": description if i == 0 else "",  # Only include description for the first chunk
                "chunk_content": chunk,
                "chunk_index": i,
                "date": date,
                "embedding": get_embedding(preprocessed_text)
            }
            collection.insert_one(document)

    # Create text index for keyword search
    collection.create_index([("title", "text"), ("chunk_content", "text")])

    st.success(f"Successfully added {len(df)} articles (split into chunks) to MongoDB with vector embeddings and text index.")


def get_search_result(query, collection):
    search_results = hybrid_search(query, collection, 30)
    print("Hybrid search results:")
    print(search_results)
    search_result = "Thông tin từ các bài báo liên quan:\n\n"
    for i, result in enumerate(search_results, 1):
        search_result += f"{i}. Tiêu đề: {result.get('title', 'N/A')}\n"
        search_result += f"   URL: {result.get('url', 'N/A')}\n"
        search_result += f"   Trích đoạn: {result.get('chunk_content', 'N/A')} \n"
        search_result += f"   Điểm liên quan: {result.get('semantic_score', 'N/A'):.4f}\n\n"
    return search_result