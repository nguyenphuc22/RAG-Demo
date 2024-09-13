import streamlit as st
from typing import List
from underthesea import sent_tokenize
from embedding.embedding_model import get_embedding


def split_text(text: str, max_length: int = 1000, overlap: int = 100) -> List[str]:
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence[-overlap:] + " " + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

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
            "chunk_content": 1,
            "score": {
                "$meta": "vectorSearchScore"
            }
        }
    }

    pipeline = [vector_search_stage, unset_stage, project_stage]
    results = collection.aggregate(pipeline)
    return list(results)


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

    st.success(f"Successfully added {len(df)} articles (split into chunks) to MongoDB with vector embeddings.")

def get_search_result(query, collection):
    get_knowledge = vector_search(query, collection, 5)
    print("get_knowledge")
    print(get_knowledge)
    search_result = ""
    for i, result in enumerate(get_knowledge, 1):
        search_result += f"\n{i}) Title: {result.get('title', 'N/A')}"
        search_result += f"\nURL: {result.get('url', 'N/A')}"
        search_result += f"\nContent Chunk: {result.get('chunk_content', 'N/A')[:200]}..."
        search_result += "\n\n"
    return search_result