from pathlib import Path
from pypdf import PdfReader
from docx import Document
from typing import List, Dict, Any
import hashlib

def get_file_hash(file_path: Path) -> str:
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def extract_text_from_pdf(file_path: Path) -> List[Dict[str, Any]]:
    reader = PdfReader(str(file_path))
    chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            chunks.append({
                "text": text.strip(),
                "page_number": i + 1,
                "section": None
            })
    return chunks

def extract_text_from_docx(file_path: Path) -> List[Dict[str, Any]]:
    document = Document(str(file_path))
    text = "\n".join([p.text for p in document.paragraphs if p.text.strip()])
    if not text:
        return []
    return [{
        "text": text,
        "page_number": 1,
        "section": None
    }]

def extract_text_from_txt(file_path: Path) -> List[Dict[str, Any]]:
    text = file_path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return [{
        "text": text,
        "page_number": 1,
        "section": None
    }]

def parse_document(file_path: Path) -> List[Dict[str, Any]]:
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
