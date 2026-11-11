"""Interface web (Gradio). Também é o ponto de entrada no Hugging Face Spaces.

Rodar localmente:
    python app.py
"""

from __future__ import annotations

import yaml
import gradio as gr

from assistant.diagnose import Diagnoser
from assistant.knowledge import DEFAULT_KB_PATH

SAMPLES_PATH = DEFAULT_KB_PATH.parent.parent / "sample_logs" / "sample_logs.yaml"
SAMPLES = {s["name"]: s["log"] for s in yaml.safe_load(SAMPLES_PATH.read_text(encoding="utf-8"))}

diagnoser = Diagnoser()
MODE_NOTE = (
    f"LLM ativa: **{diagnoser.llm.model}**"
    if diagnoser.llm
    else "Rodando **sem LLM** (só a busca). Defina `GEMINI_API_KEY` para explicações geradas pela IA."
)


def analyze(log_text: str):
    result = diagnoser.diagnose(log_text)
    table = [
        [m.entry.title, f"{m.score:.2f}", f"{m.pattern_score:.2f}", f"{m.text_score:.2f}", ", ".join(m.matched_patterns) or "-"]
        for m in result.matches
    ]
    return result.to_markdown(), table


def load_sample(name: str) -> str:
    return SAMPLES.get(name, "")


with gr.Blocks(title="Airflow Log Assistant") as demo:
    gr.Markdown(
        "# Airflow Log Assistant\n"
        "Cole o log de uma tarefa do Apache Airflow que falhou. O assistente busca a causa "
        "numa base de falhas comuns de Airflow e Google Cloud e explica como corrigir.\n\n"
        f"{MODE_NOTE}\n\n"
        "> Não cole logs com dados sensíveis, senhas ou informações de clientes."
    )
    with gr.Row():
        with gr.Column(scale=1):
            sample = gr.Dropdown(choices=list(SAMPLES), label="Ou escolha um log de exemplo", value=None)
            log_input = gr.Textbox(label="Log da tarefa", lines=16, placeholder="[2026-10-14, 03:19:41 UTC] {...} ERROR - ...")
            run_btn = gr.Button("Diagnosticar", variant="primary")
        with gr.Column(scale=1):
            output = gr.Markdown()
            with gr.Accordion("Como a busca pontuou cada falha", open=False):
                scores = gr.Dataframe(
                    headers=["Falha", "Pontuação", "Padrões", "Texto", "Padrões encontrados"],
                    interactive=False,
                )

    sample.change(load_sample, inputs=sample, outputs=log_input)
    run_btn.click(analyze, inputs=log_input, outputs=[output, scores])
    log_input.submit(analyze, inputs=log_input, outputs=[output, scores])


if __name__ == "__main__":
    demo.launch()
