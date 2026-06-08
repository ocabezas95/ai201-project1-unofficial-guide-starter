from pathlib import Path
import re
import json


RAW_DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "chunks.json"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def load_documents(raw_dir: Path):
    documents = []

    for file_path in raw_dir.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        documents.append({
            "source": file_path.name,
            "text": text
        })

    return documents


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()
    return text


def parse_header_fields(text: str):
    """Pull the professor name and URL out of a document's header block."""
    professor = ""
    url = ""

    professor_match = re.search(r"Professor:\s*(.+)", text)
    if professor_match:
        professor = professor_match.group(1).strip()

    url_match = re.search(r"URL:\s*(\S+)", text)
    if url_match:
        url = url_match.group(1).strip()

    return professor, url


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split a document into chunks.

    Returns a list of dicts: {"text", "professor", "url"}. We embed only the
    professor name plus the review body and keep the rest of the header
    (department, university, course list, URL) out of the embedded text, since
    that boilerplate is identical across every chunk and only dilutes the
    semantic signal. The structured fields travel as metadata instead.
    """
    professor, url = parse_header_fields(text)
    chunks = []

    is_review_file = re.search(r"\n\s*review\s+\d+\s*:", text, flags=re.IGNORECASE)

    if is_review_file:
        review_blocks = re.split(r"\n\s*review\s+\d+\s*:", text, flags=re.IGNORECASE)
        header = f"Professor: {professor}\n\n" if professor else ""

        for i, block in enumerate(review_blocks):
            block = block.strip()

            if not block:
                continue

            if i == 0 and "Course:" not in block:
                continue

            review_text = f"{header}Review:\n{block}".strip()

            if len(review_text) <= chunk_size:
                pieces = [review_text]
            else:
                pieces = character_chunk(review_text, chunk_size, overlap)

            for piece in pieces:
                chunks.append({"text": piece, "professor": professor, "url": url})

    else:
        for piece in character_chunk(text, chunk_size, overlap):
            chunks.append({"text": piece, "professor": professor, "url": url})

    return chunks


def character_chunk(text: str, chunk_size: int, overlap: int):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def process_documents():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    documents = load_documents(RAW_DATA_DIR)
    all_chunks = []

    for doc in documents:
        cleaned_text = clean_text(doc["text"])
        chunks = chunk_text(cleaned_text)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{doc['source']}_chunk_{i}",
                "source": doc["source"],
                "chunk_index": i,
                "professor": chunk["professor"],
                "url": chunk["url"],
                "text": chunk["text"]
            })

    OUTPUT_FILE.write_text(
        json.dumps(all_chunks, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Loaded documents: {len(documents)}")
    print(f"Total chunks created: {len(all_chunks)}")
    print(f"Saved chunks to: {OUTPUT_FILE}")

    print("\nSample chunks:\n")
    for chunk in all_chunks[:5]:
        print("=" * 80)
        print(f"Source: {chunk['source']}")
        print(f"Chunk: {chunk['chunk_index']}")
        print(chunk["text"])


if __name__ == "__main__":
    process_documents()