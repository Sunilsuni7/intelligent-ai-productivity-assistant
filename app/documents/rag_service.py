from typing import Dict, Any
from app.documents.retriever import retrieve_chunks

def generate_rag_answer(query: str) -> Dict[str, Any]:
    chunks = retrieve_chunks(query, top_k=5)

    if not chunks:
        return {
            "answer": "I couldn't find enough information in the available documents to answer that question.",
            "sources": [],
            "retrieved_chunk_count": 0
        }

    # Build context
    context_parts = []
    sources = []

    for i, chunk in enumerate(chunks):
        page_info = f"page {chunk['page_number']}" if chunk.get('page_number') else f"chunk {i+1}"
        source_name = f"{chunk['filename']} — {page_info}"
        sources.append(source_name)

        context_parts.append(f"--- SOURCE {i+1}: {source_name} ---\n{chunk['text']}")

    context_text = "\n\n".join(context_parts)

    prompt = f"""
You are an intelligent enterprise productivity assistant.

Answer the user's question using ONLY the provided context from the documents.

Important rules:
1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not present in the context, say exactly: "I couldn't find enough information in the available documents to answer that question."
4. Keep the answer short and professional.

User question:
{query}

Context:
{context_text}
"""

    from app.ai.assistant import generate_gemini_response
    ai_response, err = generate_gemini_response(prompt)
    if err:
        return {
            "answer": "Gemini is unavailable. I cannot generate a synthesized answer right now.",
            "error": err,
            "sources": sources,
            "retrieved_chunk_count": len(chunks)
        }

    return {
        "answer": ai_response,
        "sources": list(set(sources)), # deduplicate if necessary, but preserving order is better, let's keep list
        "retrieved_chunk_count": len(chunks)
    }
