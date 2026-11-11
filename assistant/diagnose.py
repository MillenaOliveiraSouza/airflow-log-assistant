"""Orquestra o fluxo: limpar log -> buscar falhas -> explicar com a LLM."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from assistant.knowledge import Entry, load_knowledge_base
from assistant.llm import GeminiClient
from assistant.preprocess import ParsedLog, parse_log
from assistant.retriever import HybridRetriever, Match

logger = logging.getLogger(__name__)

# Regras para admitir "não sei", calibradas só no conjunto de desenvolvimento:
# falhas conhecidas tiveram pontuação mínima 0,44 e as desconhecidas, máxima 0,38.
MIN_SCORE = 0.40


@dataclass
class Diagnosis:
    entry: Entry | None
    cause: str
    evidence: str
    fix: list[str]
    confidence: str
    mode: str                       # "llm" ou "busca"
    matches: list[Match] = field(default_factory=list)
    warning: str = ""

    def to_markdown(self) -> str:
        if self.entry is None:
            title = "Não reconheci essa falha"
        else:
            title = self.entry.title
        parts = [f"### {title}", f"**Confiança:** {self.confidence} · **Modo:** {self.mode}"]
        if self.warning:
            parts.append(f"> {self.warning}")
        parts.append(f"**Causa provável**\n\n{self.cause}")
        if self.evidence:
            parts.append(f"**Evidência no log**\n\n```\n{self.evidence}\n```")
        if self.fix:
            parts.append("**Como corrigir**\n\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(self.fix, 1)))
        if self.entry and self.entry.docs:
            parts.append("**Documentação**\n\n" + "\n".join(f"- {d}" for d in self.entry.docs))
        return "\n\n".join(parts)


def _evidence(log: ParsedLog, best: Match, max_lines: int = 3) -> str:
    """Linhas do log onde os padrões da falha escolhida aparecem."""
    if best.matched_patterns:
        patterns = [p for raw, p in zip(best.entry.patterns, best.entry.compiled_patterns) if raw in best.matched_patterns]
        lines = [line for line in log.clean.splitlines() if any(p.search(line) for p in patterns)]
        if lines:
            return "\n".join(lines[-max_lines:])
    return log.final_error or log.focus


class Diagnoser:
    def __init__(self, entries: list[Entry] | None = None, llm: GeminiClient | None = None, use_llm: bool = True):
        self.entries = entries or load_knowledge_base()
        self.by_id = {e.id: e for e in self.entries}
        self.retriever = HybridRetriever(self.entries)
        self.llm = llm if llm is not None else (GeminiClient.from_env() if use_llm else None)

    def diagnose(self, log_text: str, k: int = 3) -> Diagnosis:
        log = parse_log(log_text)
        if not log.clean:
            return Diagnosis(None, "Cole um log para analisar.", "", [], "baixa", "busca")

        matches = self.retriever.search(log, k=k)
        best = matches[0]

        if self.llm is not None:
            try:
                answer = self.llm.diagnose(log, matches)
                entry = self.by_id.get(answer.entry_id)
                return Diagnosis(
                    entry=entry,
                    cause=answer.cause,
                    evidence=answer.evidence,
                    fix=list(answer.fix) or (list(entry.fix) if entry else []),
                    confidence=answer.confidence,
                    mode=f"llm ({answer.model})",
                    matches=matches,
                )
            except Exception as exc:  # rede, quota, JSON inválido...
                logger.warning("LLM falhou, usando só a busca: %s", exc)
                warning = "A LLM não respondeu; mostrando o resultado da busca."
        else:
            warning = ""

        return self._from_retrieval(_evidence(log, best), best, matches, warning)

    def _from_retrieval(self, evidence: str, best: Match, matches: list[Match], warning: str) -> Diagnosis:
        # Sem nenhum padrão conhecido no log, a semelhança de texto sozinha não basta.
        if best.score < MIN_SCORE or not best.matched_patterns:
            return Diagnosis(
                entry=None,
                cause="Nenhuma falha conhecida corresponde a este log com segurança. Veja as opções mais próximas abaixo.",
                evidence=evidence,
                fix=[],
                confidence="baixa",
                mode="busca",
                matches=matches,
                warning=warning,
            )
        gap = best.score - (matches[1].score if len(matches) > 1 else 0)
        confidence = "alta" if best.score >= 0.7 and gap >= 0.15 else "media" if best.score >= 0.5 else "baixa"
        return Diagnosis(
            entry=best.entry,
            cause=best.entry.cause,
            evidence=evidence,
            fix=list(best.entry.fix),
            confidence=confidence,
            mode="busca",
            matches=matches,
            warning=warning,
        )
