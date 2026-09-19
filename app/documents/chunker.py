from typing import List, Dict, Any
import re

def semantic_chunking(parsed_data: List[Dict[str, Any]], max_chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Takes the output of parser and splits it into smaller overlapping chunks.
    Preserves page_number and metadata.
    """
    final_chunks = []

    for item in parsed_data:
        text = item["text"]
        page = item["page_number"]
        section = item["section"]

        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)

        current_chunk_text = ""
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            if len(current_chunk_text) + len(p) < max_chunk_size:
                current_chunk_text += p + "\n\n"
            else:
                # If current chunk is not empty, save it
                if current_chunk_text:
                    final_chunks.append({
                        "text": current_chunk_text.strip(),
                        "page_number": page,
                        "section": section
                    })
                    # Overlap: keep the last part of the current chunk
                    # Here we just keep the last paragraph if it fits in overlap, or just empty it
                    if len(p) < max_chunk_size:
                        current_chunk_text = p + "\n\n"
                    else:
                        # Very long paragraph, just split it by sentences or blindly
                        current_chunk_text = p[:overlap] + "\n\n"
                else:
                    # Paragraph itself is larger than max_chunk_size
                    final_chunks.append({
                        "text": p[:max_chunk_size],
                        "page_number": page,
                        "section": section
                    })
                    current_chunk_text = p[max_chunk_size-overlap:] + "\n\n"

        if current_chunk_text.strip():
            final_chunks.append({
                "text": current_chunk_text.strip(),
                "page_number": page,
                "section": section
            })

    return final_chunks
