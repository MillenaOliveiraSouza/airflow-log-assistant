"""Limpa o log e separa as linhas que mais importam para o diagnóstico."""

from __future__ import annotations

import re
from dataclasses import dataclass

# "[2026-10-14, 03:12:08 UTC] {taskinstance.py:1157} INFO - "
_PREFIX = re.compile(r"^\[[^\]]*\]\s*(\{[^}]*\}\s*)?(INFO|WARNING|ERROR|CRITICAL|DEBUG)?\s*-?\s*")

# Linhas com sinais fortes de erro.
_SIGNAL = re.compile(
    r"error|exception|traceback|failed|failure|denied|refused|timed? ?out|"
    r"not found|no such|does not|isn't defined|sigkill|oomkilled|zombie|"
    r"exit_code|return code|no open slots|upstream_failed|\b[45]\d\d\b",
    re.IGNORECASE,
)

MAX_CHARS = 6000


@dataclass(frozen=True)
class ParsedLog:
    original: str
    clean: str          # log inteiro sem prefixos de data e nível
    focus: str          # só as linhas com sinal de erro
    final_error: str    # última linha de exceção, normalmente a mais útil


def _strip_prefix(line: str) -> str:
    return _PREFIX.sub("", line).strip()


def parse_log(text: str) -> ParsedLog:
    """Extrai as partes do log usadas pela busca e pela LLM."""
    text = (text or "").strip()
    if len(text) > MAX_CHARS:
        # Em logs longos, o erro costuma estar no fim.
        text = text[-MAX_CHARS:]

    lines = [_strip_prefix(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    focus_lines = [line for line in lines if _SIGNAL.search(line)]

    exception_lines = [
        line for line in lines
        if re.match(r"^[\w.]+(Error|Exception|Timeout|Interrupt|Forbidden|NotFound|BadRequest)\b", line)
        or line.startswith(("KeyError", "TypeError", "ValueError"))
    ]
    final_error = exception_lines[-1] if exception_lines else (focus_lines[-1] if focus_lines else "")

    return ParsedLog(
        original=text,
        clean="\n".join(lines),
        focus="\n".join(focus_lines) or "\n".join(lines[-5:]),
        final_error=final_error,
    )
