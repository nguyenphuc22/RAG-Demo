import streamlit as st
from typing import List
from underthesea import sent_tokenize
from embedding.embedding_model import get_embedding
from rank_bm25 import BM25Okapi
import numpy as np


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
    # Perform a text search using MongoDB's text index
    results = collection.find(
        {"$text": {"$search": user_query}},
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

    # Create a dictionary to store the best rank for each document
    best_ranks = {}

    for i, result in enumerate(vector_results):
        doc_id = result['url']  # Using URL as a unique identifier
        best_ranks[doc_id] = min(best_ranks.get(doc_id, float('inf')), i + 1)

    for i, result in enumerate(keyword_results):
        doc_id = result['url']
        best_ranks[doc_id] = min(best_ranks.get(doc_id, float('inf')), i + 1)

    # Calculate RRF score for each document
    rrf_scores = {doc_id: 1 / (k + rank) for doc_id, rank in best_ranks.items()}

    # Sort results by RRF score
    sorted_results = sorted(all_results, key=lambda x: rrf_scores[x['url']], reverse=True)

    # Remove duplicates while preserving order
    seen = set()
    deduplicated_results = []
    for result in sorted_results:
        if result['url'] not in seen:
            seen.add(result['url'])
            deduplicated_results.append(result)

    return deduplicated_results[:10]  # Return top 10 results


def hybrid_search(user_query, collection, limit=30):
    vector_results = vector_search(user_query, collection, limit)
    keyword_results = keyword_search(user_query, collection, limit)
    combined_results = reciprocal_rank_fusion(vector_results, keyword_results)
    return combined_results


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

            print(f"Adding chunk {i + 1}/{len(chunks)} for article: {title} \n URL: {url} \n Chunk: {chunk}")

            document = {
                "title": title,
                "url": url,
                "description": description if i == 0 else "",  # Only include description for the first chunk
                "chunk_content": chunk,
                "chunk_index": i,
                "date": date,
                "embedding": get_embedding(text_for_embedding)
            }
            collection.insert_one(document)

    # Create text index for keyword search
    collection.create_index([("title", "text"), ("chunk_content", "text")])

    st.success(f"Successfully added {len(df)} articles (split into chunks) to MongoDB with vector embeddings and text index.")


def get_search_result(query, collection):
    search_results = hybrid_search(query, collection, 5)
    print("Hybrid search results:")
    print(search_results)
    search_result = "Thông tin từ các bài báo liên quan:\n\n"
    for i, result in enumerate(search_results, 1):
        search_result += f"{i}. Tiêu đề: {result.get('title', 'N/A')}\n"
        search_result += f"   URL: {result.get('url', 'N/A')}\n"
        search_result += f"   Trích đoạn: {result.get('chunk_content', 'N/A')} \n"
        search_result += f"   Điểm liên quan: {result.get('normalized_score', 'N/A')}\n\n"
    return search_result