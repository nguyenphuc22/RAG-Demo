import pymongo
import streamlit as st

@st.cache_resource
def init_mongodb_connection(connection_string):
    if not connection_string:
        st.error("Please provide a MongoDB connection string.")
        return None
    try:
        client = pymongo.MongoClient(connection_string)
        client.admin.command('ping')
        st.sidebar.success("Successfully connected to MongoDB!")
        return client
    except Exception as e:
        st.sidebar.error(f"Failed to connect to MongoDB: {e}")
        return None

def get_collection(client, db_name, collection_name):
    if client:
        db = client[db_name]
        collection = db[collection_name]
        print(f"Number of documents in collection: {collection.count_documents({})}")
        print("Indexes:", collection.index_information())
        return collection
    return None