"""Assistente que diagnostica falhas em logs do Airflow com busca (RAG) e LLM."""

from assistant.diagnose import Diagnoser, Diagnosis

__all__ = ["Diagnoser", "Diagnosis"]
