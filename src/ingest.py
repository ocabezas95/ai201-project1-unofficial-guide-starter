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


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    chunks = []

    # Try to split by review boundaries first
    review_blocks = re.split(r"\n\s*review\s+\d+\s*:", text, flags=re.IGNORECASE)

    # Keep the professor metadata with each review when possible
    metadata_match = re.search(
        r"Professor:.*?Reviews:",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )
    metadata = metadata_match.group(0).strip() if metadata_match else ""

    for i, block in enumerate(review_blocks):
        block = block.strip()

        if not block:
            continue

        # Skip the metadata-only block if it does not contain review text
        if i == 0 and "Course:" not in block:
            continue

        review_text = f"{metadata}\n\nReview:\n{block}".strip()

        # If the review block is short enough, keep it as one chunk
        if len(review_text) <= chunk_size:
            chunks.append(review_text)
        else:
            # If a review is too long, fall back to overlapping character chunks
            start = 0
            while start < len(review_text):
                end = start + chunk_size
                chunk = review_text[start:end].strip()

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
                "text": chunk
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