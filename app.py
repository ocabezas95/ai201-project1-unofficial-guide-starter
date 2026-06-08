import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

import gradio as gr
from query import ask


def handle_query(question):
    if not question.strip():
        return "Please enter a question.", ""

    try:
        result = ask(question)
    except Exception as e:
        return f"Something went wrong: {e}", ""

    answer = result["answer"]

    sources = "\n".join(f"- {source}" for source in result["sources"])

    return answer, sources


with gr.Blocks() as demo:
    gr.Markdown("# UNO CS Unofficial Guide")
    gr.Markdown("Ask questions about UNO Computer Science professors, courses, and student experiences.")

    question = gr.Textbox(label="Your question", placeholder="Example: What do students say about Vassil Rousser?")
    ask_button = gr.Button("Ask")

    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved Sources", lines=4)

    ask_button.click(handle_query, inputs=question, outputs=[answer, sources])
    question.submit(handle_query, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()