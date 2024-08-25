import pandas as pd
import pymongo
from sentence_transformers import SentenceTransformer
import os

# MongoDB connection
client = pymongo.MongoClient(
    'mongodb+srv://phuc:pBWtKzGm3jHnMxsr@cluster0.llq9qnt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["sample_mflix"]
collection = db['vnexpress_articles']

# Load the embedding model
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")


def get_embedding(text: str) -> list[float]:
    if not text.strip():
        print("Attempted to get embedding for empty text.")
        return []
    embedding = embedding_model.encode(text)
    return embedding.tolist()


# Read the Excel file
excel_file = 'vnexpress_articles.xlsx'  # Make sure this is the correct path to your file
if not os.path.exists(excel_file):
    print(f"Error: File {excel_file} not found.")
    exit(1)

df = pd.read_excel(excel_file)

# Process each row and insert into MongoDB
for index, row in df.iterrows():
    # Combine title and description for embedding
    text_for_embedding = f"{row['title']} {row['description']}"

    # Create the document to insert
    document = {
        "title": row['title'],
        "url": row['url'],
        "description": row['description'],
        "embedding": get_embedding(text_for_embedding)
    }

    # Insert the document
    result = collection.insert_one(document)
    print(f"Inserted document with ID: {result.inserted_id}")

print("Data ingestion into MongoDB completed")

# Print some statistics
print(f"Total documents in collection: {collection.count_documents({})}")
print("Sample document:")
print(collection.find_one())