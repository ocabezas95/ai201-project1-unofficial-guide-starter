from pathlib import Path
import json
import chromadb
from sentence_transformers import SentenceTransformer


CHUNKS_FILE = Path("data/processed/chunks.json")
CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "uno_cs_reviews"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 4


def load_chunks():
    with CHUNKS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_vector_store():
    chunks = load_chunks()

    model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete old collection if it exists so we don't duplicate chunks
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(name=COLLECTION_NAME)

    texts = [chunk["text"] for chunk in chunks]
    ids = [chunk["id"] for chunk in chunks]
    metadatas = [
        {
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"]
        }
        for chunk in chunks
    ]

    embeddings = model.encode(texts).tolist()

    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )

    print(f"Stored {len(chunks)} chunks in ChromaDB.")


def retrieve(query: str, top_k: int = TOP_K):
    model = SentenceTransformer(EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)

    query_embedding = model.encode([query]).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    retrieved = []

    for i in range(len(results["documents"][0])):
        retrieved.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
            "distance": results["distances"][0][i]
        })

    return retrieved


if __name__ == "__main__":
    build_vector_store()

    test_queries = [
        "What do students say about Vassil Rousser's cybersecurity class?",
        "What do students say about UNO's cybersecurity and internship opportunities?",
        "Why might someone choose UNO over Loyola for computer science?"
    ]

    for query in test_queries:
        print("\n" + "=" * 100)
        print(f"QUERY: {query}")
        print("=" * 100)

        results = retrieve(query)

        for i, result in enumerate(results, start=1):
            print(f"\nResult {i}")
            print(f"Source: {result['source']}")
            print(f"Chunk: {result['chunk_index']}")
            print(f"Distance: {result['distance']:.4f}")
            print(result["text"][:700])