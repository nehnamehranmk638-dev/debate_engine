import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

load_dotenv()

def get_embeddings():
    return OpenAIEmbeddings(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model="openai/text-embedding-ada-002"
    )

def build_store(docs_path: str, save_path: str):
    loader = DirectoryLoader(
        docs_path,
        glob="*.txt",
        loader_cls=TextLoader
    )
    docs = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(docs)
    
    embeddings = get_embeddings()
    store = FAISS.from_documents(chunks, embeddings)
    store.save_local(save_path)
    print(f"Built store at {save_path} with {len(chunks)} chunks")
    return store

def load_store(save_path: str):
    embeddings = get_embeddings()
    return FAISS.load_local(
        save_path,
        embeddings,
        allow_dangerous_deserialization=True
    )