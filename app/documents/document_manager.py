from pathlib import Path
from app.database.database import get_connection
from app.documents.parser import parse_document, get_file_hash
from app.documents.chunker import semantic_chunking
from app.documents.embeddings import generate_embeddings
from app.documents.vector_store import vector_store
from app.documents.rag_service import generate_rag_answer
import time

BASE_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = BASE_DIR / "documents"

def search_documents(query: str):
    """
    Called by Agent tool registry.
    Returns the RAG answer and sources.
    """
    try:
        rag_result = generate_rag_answer(query)
        return {
            "query": query,
            "answer": rag_result.get("answer"),
            "sources": rag_result.get("sources", []),
            "retrieved_chunk_count": rag_result.get("retrieved_chunk_count", 0)
        }
    except Exception as e:
        return {
            "query": query,
            "answer": f"Error during document search: {str(e)}",
            "sources": [],
            "error": str(e)
        }

def get_indexed_documents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.id, d.filename, d.file_type, d.status, d.indexed_at,
               (SELECT COUNT(*) FROM document_chunks c WHERE c.document_id = d.id) as chunk_count
        FROM documents d
    ''')
    docs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return docs

def index_all_documents():
    if not DOCUMENTS_DIR.exists():
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        return

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Check existing documents
    cursor.execute("SELECT id, filename, file_hash FROM documents")
    existing_docs = {row['filename']: dict(row) for row in cursor.fetchall()}

    current_files = []
    for file_path in DOCUMENTS_DIR.iterdir():
        if file_path.suffix.lower() not in [".pdf", ".docx", ".txt"]:
            continue

        filename = file_path.name
        current_files.append(filename)
        file_hash = get_file_hash(file_path)

        if filename in existing_docs:
            if existing_docs[filename]['file_hash'] == file_hash:
                # Unchanged
                continue
            else:
                # Modified -> re-index
                _delete_document_index(cursor, existing_docs[filename]['id'])
                _index_document(cursor, file_path, file_hash)
        else:
            # New document
            _index_document(cursor, file_path, file_hash)

    # 2. Check for deleted documents
    for filename, doc_info in existing_docs.items():
        if filename not in current_files:
            _delete_document_index(cursor, doc_info['id'])

    conn.commit()
    conn.close()

def _delete_document_index(cursor, document_id: int):
    # Get all chunk IDs
    cursor.execute("SELECT id FROM document_chunks WHERE document_id = ?", (document_id,))
    chunk_ids = {row['id'] for row in cursor.fetchall()}

    # Remove from vector store
    if chunk_ids:
        vector_store.remove_embeddings_by_chunk_ids(chunk_ids)

    # Remove from DB (cascade deletes chunks)
    cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))

def _index_document(cursor, file_path: Path, file_hash: str):
    filename = file_path.name
    file_type = file_path.suffix.lower()

    try:
        # Insert into documents table
        cursor.execute('''
            INSERT INTO documents (filename, file_type, file_hash, file_size, status)
            VALUES (?, ?, ?, ?, 'PROCESSING')
        ''', (filename, file_type, file_hash, file_path.stat().st_size))
        document_id = cursor.lastrowid

        # Parse and chunk
        parsed_data = parse_document(file_path)
        chunks = semantic_chunking(parsed_data)

        if not chunks:
            cursor.execute("UPDATE documents SET status = 'INDEXED' WHERE id = ?", (document_id,))
            return

        # Extract texts for embedding
        texts = [c["text"] for c in chunks]
        embeddings = generate_embeddings(texts)

        # Save chunks to DB
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            cursor.execute('''
                INSERT INTO document_chunks (document_id, chunk_index, text, page_number, section)
                VALUES (?, ?, ?, ?, ?)
            ''', (document_id, i, chunk["text"], chunk.get("page_number"), chunk.get("section")))
            chunk_ids.append(cursor.lastrowid)

        # Add to vector store
        vector_store.add_embeddings(chunk_ids, embeddings)

        cursor.execute("UPDATE documents SET status = 'INDEXED' WHERE id = ?", (document_id,))

    except Exception as e:
        print(f"Failed to index {filename}: {e}")
        # Mark as FAILED if we already inserted it
        cursor.execute("UPDATE documents SET status = 'FAILED' WHERE filename = ?", (filename,))
