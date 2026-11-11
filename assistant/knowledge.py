"""Carrega a base de conhecimento (falhas comuns de Airflow + GCP)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base" / "airflow_gcp_errors.yaml"


@dataclass(frozen=True)
class Entry:
    """Uma falha conhecida, com causa, correção e referências."""

    id: str
    title: str
    category: str
    patterns: tuple[str, ...]
    symptoms: str
    cause: str
    fix: tuple[str, ...]
    docs: tuple[str, ...] = field(default_factory=tuple)

    @property
    def compiled_patterns(self) -> tuple[re.Pattern[str], ...]:
        return tuple(re.compile(p, re.IGNORECASE) for p in self.patterns)

    def search_text(self) -> str:
        """Texto usado para indexar a entrada na busca."""
        return " ".join([self.title, " ".join(self.patterns), self.symptoms, self.cause])

    def as_context(self) -> str:
        """Texto enviado para a LLM como contexto recuperado."""
        fix = "\n".join(f"  - {step}" for step in self.fix)
        docs = ", ".join(self.docs)
        return (
            f"[id: {self.id}] {self.title}\n"
            f"Sintomas: {self.symptoms.strip()}\n"
            f"Causa: {self.cause.strip()}\n"
            f"Correção:\n{fix}\n"
            f"Documentação: {docs}"
        )


def load_knowledge_base(path: str | Path = DEFAULT_KB_PATH) -> list[Entry]:
    """Lê o YAML e valida os campos de cada entrada."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    entries: list[Entry] = []
    seen: set[str] = set()
    for item in raw:
        entry = Entry(
            id=item["id"],
            title=item["title"],
            category=item["category"],
            patterns=tuple(item["patterns"]),
            symptoms=item["symptoms"].strip(),
            cause=item["cause"].strip(),
            fix=tuple(item["fix"]),
            docs=tuple(item.get("docs", [])),
        )
        if entry.id in seen:
            raise ValueError(f"id duplicado na base de conhecimento: {entry.id}")
        seen.add(entry.id)
        entry.compiled_patterns  # falha cedo se algum regex for inválido
        entries.append(entry)
    return entries
