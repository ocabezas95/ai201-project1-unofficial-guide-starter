from groq import Groq
from dotenv import load_dotenv
from retrieve import retrieve

load_dotenv()

MODEL_NAME = "llama-3.3-70b-versatile"

client = Groq()

NOT_ENOUGH_INFO = "I don't have enough information in the provided documents to answer that."

# Chunks with a cosine distance above this are too weakly related to the
# question to be useful, so we drop them before building the context.
MAX_DISTANCE = 0.85


def build_context(chunks):
    context_parts = []

    for i, chunk in enumerate(chunks, start=1):
        label = chunk["source"]
        if chunk.get("professor"):
            label = f"{chunk['professor']} ({chunk['source']})"

        context_parts.append(
            f"[Source {i}: {label}]\n"
            f"{chunk['text']}"
        )

    return "\n\n---\n\n".join(context_parts)


def ask(question: str):
    retrieved_chunks = retrieve(question)

    # Keep only chunks the retriever is reasonably confident about.
    retrieved_chunks = [
        chunk for chunk in retrieved_chunks
        if chunk["distance"] <= MAX_DISTANCE
    ]

    if not retrieved_chunks:
        return {
            "answer": NOT_ENOUGH_INFO,
            "sources": [],
            "retrieved_chunks": []
        }

    context = build_context(retrieved_chunks)

    prompt = f"""
You are a grounded RAG assistant for UNO Computer Science professor and course reviews.

Answer the user's question using ONLY the provided context.

Rules:
- Do not use outside knowledge.
- If the context contains student opinions, summarize the common themes.
- If none of the context is related to the question, say: "I don't have enough information in the provided documents to answer that."
- When you use information from the context, cite the source document name.
- Be concise and helpful.

Context:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You answer only from retrieved context and cite sources."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content

    sources = sorted(set(chunk["source"] for chunk in retrieved_chunks))

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": retrieved_chunks
    }


if __name__ == "__main__":
    question = input("Ask a question: ")
    result = ask(question)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print(f"- {source}")