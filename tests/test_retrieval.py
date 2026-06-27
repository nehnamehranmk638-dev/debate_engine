import pytest
from retrieval.vector_store import (
    get_embeddings,
    clean_content,
    is_useful_chunk,
    build_dynamic_store
)

def test_clean_content_removes_footnotes():
    dirty = "Some text [^1](https://example.com) more text"
    clean = clean_content(dirty)
    assert "http" not in clean
    assert "Some text" in clean

def test_clean_content_removes_urls():
    dirty = "Visit https://example.com for more info"
    clean = clean_content(dirty)
    assert "https" not in clean

def test_is_useful_chunk_rejects_short():
    assert is_useful_chunk("too short") == False

def test_is_useful_chunk_rejects_symbols():
    assert is_useful_chunk("!@#$%^&*()_+[]{}|;':,./<>?" * 5) == False

def test_is_useful_chunk_accepts_good_text():
    good = "Artificial intelligence regulation is essential for ensuring safety and fairness in automated decision making systems."
    assert is_useful_chunk(good) == True

def test_embeddings_connection():
    embeddings = get_embeddings()
    result = embeddings.embed_query("test query about AI regulation")
    assert isinstance(result, list)
    assert len(result) == 1536
    assert all(isinstance(x, float) for x in result)