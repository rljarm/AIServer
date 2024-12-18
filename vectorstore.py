# project_root/model_integration/vectorstore.py

import os
import pickle
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

# This sets up a vector store for RAG. On first run, create it if not exists.
# On subsequent runs, load the existing store.

VECTOR_STORE_PATH = "project_root/model_integration/faiss_store.pkl"

def get_vectorstore():
    if os.path.exists(VECTOR_STORE_PATH):
        with open(VECTOR_STORE_PATH, "rb") as f:
            vs = pickle.load(f)
        return vs
    else:
        embeddings = HuggingFaceEmbeddings()
        vs = FAISS.from_texts(["initial text"], embeddings)
        with open(VECTOR_STORE_PATH, "wb") as f:
            pickle.dump(vs, f)
        return vs

def add_document_to_store(text: str):
    vs = get_vectorstore()
    embeddings = HuggingFaceEmbeddings()
    new_vs = vs.add_texts([text], embeddings)
    with open(VECTOR_STORE_PATH, "wb") as f:
        pickle.dump(new_vs, f)

def search_vectorstore(query: str, k=3):
    vs = get_vectorstore()
    return vs.similarity_search(query, k=k)