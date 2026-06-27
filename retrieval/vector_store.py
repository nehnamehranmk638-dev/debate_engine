import os
import re
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

def get_embeddings():
    return OpenAIEmbeddings(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model="openai/text-embedding-ada-002"
    )

def clean_content(text: str) -> str:
    # remove markdown footnote links like [^](url)
    text = re.sub(r'\[\^?\d*\]\(https?://[^\)]+\)', '', text)
    # remove bare URLs
    text = re.sub(r'https?://\S+', '', text)
    # remove patterns like _Id._ or _See_
    text = re.sub(r'_[^_]+_', '', text)
    # collapse multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_useful_chunk(text: str) -> bool:
    # skip chunks that are too short
    if len(text) < 100:
        return False
    # skip chunks that are mostly punctuation/symbols
    alpha_ratio = sum(c.isalpha() for c in text) / len(text)
    if alpha_ratio < 0.5:
        return False
    return True

def search_web(query: str, num_results: int = 5) -> list[Document]:
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    results = client.search(
        query=query,
        max_results=num_results
    )
    docs = []
    for r in results["results"]:
        content = clean_content(r.get("content", ""))
        if content:
            docs.append(Document(
                page_content=content,
                metadata={
                    "source": r.get("url", "unknown"),
                    "title": r.get("title", "unknown")
                }
            ))
    return docs

def build_dynamic_store(topic: str, stance: str) -> FAISS:
    if stance == "PRO":
        query = f"why we need {topic} safety benefits accountability"
    else:
        query = f"against {topic} why it is bad harmful innovation freedom"

    print(f"Searching web for {stance} arguments on: {topic}")
    docs = search_web(query, num_results=7)  # increased to 7

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    all_chunks = splitter.split_documents(docs)

    clean_chunks = [
        c for c in all_chunks
        if is_useful_chunk(c.page_content)
    ]
    print(f"Created {len(clean_chunks)} clean chunks for {stance} store")

    embeddings = get_embeddings()
    store = FAISS.from_documents(clean_chunks, embeddings)
    return store