"""Integração com a LLM (Google Gemini).

A LLM recebe o trecho do log e as falhas recuperadas pela busca, escolhe a
causa mais provável e escreve a explicação. Ela só pode responder com base no
contexto enviado, o que reduz respostas inventadas.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from assistant.preprocess import ParsedLog
from assistant.retriever import Match

DEFAULT_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """Você é um engenheiro de dados que diagnostica falhas em pipelines Apache Airflow no Google Cloud.
Regras:
1. Use somente o log e as falhas conhecidas enviadas no contexto.
2. Escolha o id da falha conhecida que melhor explica o log. Se nenhuma explicar, use "desconhecido".
3. Cite o trecho exato do log que comprova o diagnóstico.
4. Escreva em português, de forma direta, para alguém que precisa corrigir o problema agora.
5. Responda apenas com JSON válido no formato:
{"entry_id": str, "causa": str, "evidencia": str, "correcao": [str], "confianca": "alta" | "media" | "baixa"}"""


@dataclass(frozen=True)
class LLMAnswer:
    entry_id: str
    cause: str
    evidence: str
    fix: tuple[str, ...]
    confidence: str
    model: str


def build_prompt(log: ParsedLog, matches: list[Match]) -> str:
    context = "\n\n".join(m.entry.as_context() for m in matches)
    return (
        f"FALHAS CONHECIDAS (recuperadas pela busca):\n{context}\n\n"
        f"TRECHO DO LOG COM ERRO:\n{log.focus}\n\n"
        f"ÚLTIMA EXCEÇÃO:\n{log.final_error or '(nenhuma)'}"
    )


def parse_answer(text: str, model: str, allowed_ids: set[str]) -> LLMAnswer:
    """Valida o JSON da LLM. Levanta ValueError se vier fora do formato."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    data = json.loads(text)
    entry_id = str(data.get("entry_id", "desconhecido"))
    if entry_id not in allowed_ids | {"desconhecido"}:
        raise ValueError(f"a LLM escolheu um id fora do contexto: {entry_id}")
    fix = data.get("correcao") or []
    if isinstance(fix, str):
        fix = [fix]
    confidence = str(data.get("confianca", "media")).lower()
    return LLMAnswer(
        entry_id=entry_id,
        cause=str(data.get("causa", "")).strip(),
        evidence=str(data.get("evidencia", "")).strip(),
        fix=tuple(str(step) for step in fix),
        confidence=confidence if confidence in {"alta", "media", "baixa"} else "media",
        model=model,
    )


class GeminiClient:
    """Cliente simples. Só é criado se existir a variável GEMINI_API_KEY."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        from google import genai  # importado aqui para o projeto rodar sem a lib

        self._genai = genai
        self.client = genai.Client(api_key=api_key)
        self.model = model

    @classmethod
    def from_env(cls) -> "GeminiClient | None":
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            return None
        return cls(api_key=key, model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL))

    def diagnose(self, log: ParsedLog, matches: list[Match]) -> LLMAnswer:
        types = self._genai.types
        response = self.client.models.generate_content(
            model=self.model,
            contents=build_prompt(log, matches),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        return parse_answer(response.text or "", self.model, {m.entry.id for m in matches})
