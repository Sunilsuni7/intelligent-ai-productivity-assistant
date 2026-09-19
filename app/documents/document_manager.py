from pathlib import Path
from pypdf import PdfReader
from docx import Document


BASE_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = BASE_DIR / "documents"


def read_pdf(file_path):
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def read_docx(file_path):
    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def read_text(file_path):
    return Path(file_path).read_text(
        encoding="utf-8"
    )


def load_document(file_path):

    file_path = Path(file_path)

    if file_path.suffix.lower() == ".pdf":
        return read_pdf(file_path)

    if file_path.suffix.lower() == ".docx":
        return read_docx(file_path)

    if file_path.suffix.lower() == ".txt":
        return read_text(file_path)

    return ""


def search_documents(query):

    results = []

    query_words = set(
        query.lower().split()
    )

    if not DOCUMENTS_DIR.exists():
        return results

    for file_path in DOCUMENTS_DIR.iterdir():

        if file_path.suffix.lower() not in [
            ".pdf",
            ".docx",
            ".txt"
        ]:
            continue

        try:

            text = load_document(file_path)

            if not text.strip():
                continue

            text_lower = text.lower()

            matched_words = [
                word
                for word in query_words
                if word in text_lower
            ]

            if matched_words:

                score = len(matched_words)

                results.append({
                    "filename": file_path.name,
                    "score": score,
                    "content": text[:2000]
                })

        except Exception as error:

            print(
                f"Error reading {file_path.name}: {error}"
            )

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results