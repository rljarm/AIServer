# project_root/model_integration/embeddings.py
# If needed to customize embeddings
from langchain.embeddings import HuggingFaceEmbeddings

def get_embeddings():
    return HuggingFaceEmbeddings()