"""Busca híbrida: padrões conhecidos (regex) + similaridade de texto (TF-IDF).

Por que híbrida?
- Regex acerta quando a mensagem de erro é clássica ("SIGKILL", "403").
- TF-IDF ajuda quando a mensagem é diferente, mas usa palavras parecidas
  com a descrição da falha.
A pontuação final combina as duas e fica entre 0 e 1.
"""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from assistant.knowledge import Entry
from assistant.preprocess import ParsedLog

PATTERN_WEIGHT = 0.6
TFIDF_WEIGHT = 0.4
FINAL_ERROR_BONUS = 1.0  # um padrão na linha final da exceção vale o dobro
# Similaridade de cosseno que já conta como "texto muito parecido".
# Usamos o valor absoluto (e não relativo ao melhor resultado) para que a
# pontuação caia quando nenhuma entrada for parecida com o log.
TFIDF_SCALE = 0.5


@dataclass(frozen=True)
class Match:
    entry: Entry
    score: float
    pattern_score: float
    text_score: float
    matched_patterns: tuple[str, ...]


class HybridRetriever:
    def __init__(self, entries: list[Entry]):
        if not entries:
            raise ValueError("a base de conhecimento está vazia")
        self.entries = entries
        # Caracteres (3 a 5) lidam bem com nomes como AirflowTaskTimeout,
        # que viram uma única palavra numa busca por palavras.
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True, sublinear_tf=True)
        self.doc_matrix = self.vectorizer.fit_transform([e.search_text() for e in entries])

    def _pattern_score(self, entry: Entry, log: ParsedLog) -> tuple[float, tuple[str, ...]]:
        weight = 0.0
        matched: list[str] = []
        for raw, pattern in zip(entry.patterns, entry.compiled_patterns):
            if pattern.search(log.clean):
                matched.append(raw)
                weight += 1.0
                if log.final_error and pattern.search(log.final_error):
                    weight += FINAL_ERROR_BONUS
        # Satura: 1 padrão = 0,5; 3 ou mais = perto de 1.
        return weight / (weight + 1.0), tuple(matched)

    def search(self, log: ParsedLog, k: int = 3) -> list[Match]:
        query = log.focus + "\n" + log.final_error
        text_scores = cosine_similarity(self.vectorizer.transform([query]), self.doc_matrix)[0]

        results: list[Match] = []
        for entry, raw_text in zip(self.entries, text_scores):
            p_score, matched = self._pattern_score(entry, log)
            t_score = float(min(1.0, raw_text / TFIDF_SCALE))
            score = PATTERN_WEIGHT * p_score + TFIDF_WEIGHT * t_score
            results.append(Match(entry, round(score, 4), round(p_score, 4), round(t_score, 4), matched))

        results.sort(key=lambda m: m.score, reverse=True)
        return results[:k]
