import pytest
from pathlib import Path
from app.documents.parser import parse_document
from app.documents.chunker import semantic_chunking
from app.documents.embeddings import generate_embeddings
from app.documents.vector_store import VectorStore
from app.documents.retriever import retrieve_chunks
from app.documents.rag_service import generate_rag_answer
from unittest.mock import patch
import numpy as np

def test_parser_txt(tmp_path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Hello world", encoding="utf-8")
    parsed = parse_document(txt_file)
    assert len(parsed) == 1
    assert parsed[0]["text"] == "Hello world"

def test_chunking():
    data = [{"text": "Sentence one.\n\nSentence two.\n\nSentence three.", "page_number": 1, "section": None}]
    # Force small chunk size to test overlap/splitting
    chunks = semantic_chunking(data, max_chunk_size=20, overlap=5)
    assert len(chunks) > 1
    assert chunks[0]["page_number"] == 1

@patch("app.documents.embeddings.generate_embeddings")
def test_embeddings(mock_gen):
    mock_gen.return_value = np.array([[1.0, 0.0], [0.0, 1.0]])
    texts = ["hello", "world"]
    emb = mock_gen(texts)
    assert isinstance(emb, np.ndarray)
    assert emb.shape[0] == 2
    assert emb.shape[1] > 0

def test_vector_store():
    store = VectorStore()
    store.chunk_ids = []
    store.embeddings = None

    emb = np.array([[1.0, 0.0], [0.0, 1.0]])
    store.add_embeddings([1, 2], emb)
    assert len(store.chunk_ids) == 2

    # query [1,0] should match chunk 1
    query = np.array([1.0, 0.0])
    res = store.search(query, top_k=1)
    assert len(res) == 1
    assert res[0]["chunk_id"] == 1

    # test remove
    store.remove_embeddings_by_chunk_ids({1})
    assert len(store.chunk_ids) == 1
    assert store.chunk_ids[0] == 2

@patch("app.documents.retriever.get_connection")
@patch("app.documents.retriever.vector_store")
@patch("app.documents.retriever.generate_embedding")
def test_hybrid_retrieval(mock_gen_emb, mock_store, mock_db):
    mock_gen_emb.return_value = np.array([1.0, 0.0])
    mock_store.search.return_value = [{"chunk_id": 1, "score": 0.9}]

    class MockCursor:
        def execute(self, *args, **kwargs): pass
        def fetchall(self): return [{"id": 1, "text": "test document content", "page_number": 1, "filename": "test.txt"}]
    class MockConn:
        def cursor(self): return MockCursor()
        def close(self): pass

    mock_db.return_value = MockConn()

    results = retrieve_chunks("test document")
    assert len(results) == 1
    assert results[0]["chunk_id"] == 1
    # Check if keyword boost worked (0.9 + 0.1 for 2 words matching = 1.0)
    assert results[0]["score"] > 0.9

@patch("app.documents.rag_service.retrieve_chunks")
@patch("app.ai.assistant.generate_gemini_response")
def test_rag_service(mock_gemini, mock_retrieve):
    mock_retrieve.return_value = [
        {"text": "Remote work is allowed for 2 days.", "page_number": 1, "filename": "policy.pdf"}
    ]
    mock_gemini.return_value = ("Employees can work remotely for 2 days.", None)

    result = generate_rag_answer("How many remote days?")
    assert "2 days" in result["answer"]
    assert len(result["sources"]) == 1
    assert "policy.pdf" in result["sources"][0]

@patch("app.documents.rag_service.retrieve_chunks")
def test_rag_service_no_context(mock_retrieve):
    mock_retrieve.return_value = []

    result = generate_rag_answer("What is the meaning of life?")
    assert "couldn't find enough information" in result["answer"]
    assert result["retrieved_chunk_count"] == 0
