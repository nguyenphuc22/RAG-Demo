import streamlit as st

from embedding.embedding_model import get_embedding


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

def create_vector_and_update_mongodb(df, collection):
    for _, row in df.iterrows():
        text_for_embedding = f"{row['title']} {row['date']} {row['content']}"

        document = {
            "title": row['title'],
            "url": row['url'],
            "description": row['description'],
            "content": row['content'],
            "date": row['date'],
            "embedding": get_embedding(text_for_embedding)
        }
        collection.insert_one(document)

    st.success(f"Successfully added {len(df)} new articles to MongoDB with vector embeddings.")

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