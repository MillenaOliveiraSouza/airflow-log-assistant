"""Mede quantas vezes o assistente acerta a causa dos logs de exemplo.

Dois conjuntos:
- desenvolvimento (sample_logs.yaml): usado para escrever e ajustar a base.
- holdout (holdout_logs.yaml): escrito depois e nunca usado para ajustes.
  É o número que vale para estimar o desempenho real.

Uso:
    python -m eval.evaluate                 # só a busca (não precisa de chave)
    python -m eval.evaluate --llm           # busca + Gemini (precisa de GEMINI_API_KEY)
    python -m eval.evaluate --save          # grava eval/results.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from assistant.diagnose import Diagnoser
from assistant.llm import GeminiClient

ROOT = Path(__file__).resolve().parent.parent
SETS = {
    "Desenvolvimento": ROOT / "data" / "sample_logs" / "sample_logs.yaml",
    "Holdout (nunca usado para ajustes)": ROOT / "data" / "sample_logs" / "holdout_logs.yaml",
}
RESULTS_PATH = ROOT / "eval" / "results.md"
UNKNOWN = "desconhecido"


def evaluate_set(diagnoser: Diagnoser, path: Path) -> list[dict]:
    rows = []
    for sample in yaml.safe_load(path.read_text(encoding="utf-8")):
        result = diagnoser.diagnose(sample["log"])
        predicted = result.entry.id if result.entry else UNKNOWN
        expected = sample["expected"]
        top3 = [m.entry.id for m in result.matches]
        rows.append({
            "name": sample["name"],
            "difficulty": sample["difficulty"],
            "expected": expected,
            "predicted": predicted,
            "top1": predicted == expected,
            # Para falhas desconhecidas, "top-3" não se aplica: conta o top-1.
            "top3": (expected in top3) if expected != UNKNOWN else predicted == UNKNOWN,
            "score": result.matches[0].score,
            "confidence": result.confidence,
        })
    return rows


def _pct(hits: int, total: int) -> str:
    return f"{hits}/{total} ({hits / total:.0%})" if total else "-"


def run(use_llm: bool) -> str:
    llm = GeminiClient.from_env() if use_llm else None
    if use_llm and llm is None:
        raise SystemExit("Defina GEMINI_API_KEY para avaliar com a LLM.")
    diagnoser = Diagnoser(llm=llm, use_llm=use_llm)
    mode = f"busca + LLM ({llm.model})" if llm else "somente busca (sem LLM)"

    results = {label: evaluate_set(diagnoser, path) for label, path in SETS.items()}

    lines = ["# Resultados da avaliação", "", f"Modo: **{mode}**", "",
             "| Conjunto | Logs | Acerto top-1 | Causa certa entre as 3 primeiras |",
             "| --- | --- | --- | --- |"]
    for label, rows in results.items():
        n = len(rows)
        lines.append(f"| {label} | {n} | {_pct(sum(r['top1'] for r in rows), n)} | {_pct(sum(r['top3'] for r in rows), n)} |")

    for label, rows in results.items():
        lines += ["", f"## {label}", "",
                  "| Log | Dificuldade | Esperado | Previsto | Top-1 | Top-3 | Pontuação | Confiança |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for r in rows:
            lines.append(
                f"| {r['name']} | {r['difficulty']} | {r['expected']} | {r['predicted']} | "
                f"{'✓' if r['top1'] else '✗'} | {'✓' if r['top3'] else '✗'} | {r['score']:.2f} | {r['confidence']} |"
            )

    lines += [
        "",
        "## Como ler",
        "",
        "- **Top-1:** a primeira resposta é a causa certa.",
        "- **Top-3:** a causa certa está entre as 3 opções mostradas na tela.",
        "- **desconhecido:** falhas que a base não cobre. O certo é o assistente admitir que não reconhece.",
        "",
        "## Limitações",
        "",
        "- Todos os logs são sintéticos, escritos para o projeto, e o conjunto é pequeno.",
        "- O conjunto de desenvolvimento foi usado para ajustar os padrões, então o resultado dele é otimista.",
        "- Logs com duas falhas ao mesmo tempo não estão nos conjuntos.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="usar a LLM além da busca")
    parser.add_argument("--save", action="store_true", help="salvar em eval/results.md")
    args = parser.parse_args()
    report = run(args.llm)
    print(report)
    if args.save:
        RESULTS_PATH.write_text(report, encoding="utf-8")
        print(f"Salvo em {RESULTS_PATH}")


if __name__ == "__main__":
    main()
