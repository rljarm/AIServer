# project_root/model_integration/rag_chain.py

import asyncio
from typing import List
from model_integration.vectorstore import search_vectorstore, add_document_to_store

async def rag_search_and_store(query: str):
    # Perform vector store search
    results = search_vectorstore(query, k=3)
    # Combine results
    combined = "\n".join([doc.page_content for doc in results])
    return combined

async def add_resources_to_store(resources: List[str]):
    for res in resources:
        add_document_to_store(res)