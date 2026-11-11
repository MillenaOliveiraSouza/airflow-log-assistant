import json
from pathlib import Path

import pytest
import yaml

from assistant.diagnose import Diagnoser
from assistant.knowledge import load_knowledge_base
from assistant.llm import LLMAnswer, parse_answer
from assistant.preprocess import parse_log

ROOT = Path(__file__).resolve().parent.parent
DEV_LOGS = yaml.safe_load((ROOT / "data" / "sample_logs" / "sample_logs.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def diagnoser():
    return Diagnoser(use_llm=False)


def test_knowledge_base_is_valid():
    entries = load_knowledge_base()
    assert len(entries) >= 15
    assert len({e.id for e in entries}) == len(entries)
    assert all(e.fix and e.docs for e in entries)


def test_expected_ids_exist_in_knowledge_base():
    ids = {e.id for e in load_knowledge_base()} | {"desconhecido"}
    for path in (ROOT / "data" / "sample_logs").glob("*.yaml"):
        for sample in yaml.safe_load(path.read_text(encoding="utf-8")):
            assert sample["expected"] in ids, sample["name"]


def test_parse_log_strips_airflow_prefix():
    log = parse_log("[2026-10-14, 03:19:41 UTC] {local_task_job_runner.py:234} INFO - Task exited with return code Negsignal.SIGKILL")
    assert log.clean == "Task exited with return code Negsignal.SIGKILL"
    assert "SIGKILL" in log.focus


def test_parse_log_keeps_end_of_long_logs():
    text = "linha sem nada\n" * 2000 + "KeyError: 'customer_id'"
    assert parse_log(text).final_error == "KeyError: 'customer_id'"


@pytest.mark.parametrize("sample", DEV_LOGS, ids=lambda s: s["name"])
def test_development_logs(diagnoser, sample):
    result = diagnoser.diagnose(sample["log"])
    predicted = result.entry.id if result.entry else "desconhecido"
    assert predicted == sample["expected"]


def test_evidence_points_to_the_matching_line(diagnoser):
    sample = next(s for s in DEV_LOGS if s["name"] == "01_oom_carga_vendas")
    assert "SIGKILL" in diagnoser.diagnose(sample["log"]).evidence


def test_empty_log(diagnoser):
    result = diagnoser.diagnose("   ")
    assert result.entry is None and result.matches == []


def test_parse_answer_accepts_valid_json():
    raw = json.dumps({"entry_id": "oom_sigkill", "causa": "memória", "evidencia": "SIGKILL",
                      "correcao": ["use chunks"], "confianca": "alta"})
    answer = parse_answer(raw, "modelo", {"oom_sigkill"})
    assert answer.entry_id == "oom_sigkill" and answer.fix == ("use chunks",)


def test_parse_answer_rejects_id_outside_context():
    raw = json.dumps({"entry_id": "inventado", "causa": "x"})
    with pytest.raises(ValueError):
        parse_answer(raw, "modelo", {"oom_sigkill"})


class FakeLLM:
    model = "fake"

    def __init__(self, fail=False):
        self.fail = fail

    def diagnose(self, log, matches):
        if self.fail:
            raise RuntimeError("quota")
        return LLMAnswer(matches[0].entry.id, "explicação da LLM", "trecho", ("passo 1",), "alta", self.model)


def test_uses_llm_when_available():
    result = Diagnoser(llm=FakeLLM()).diagnose(DEV_LOGS[0]["log"])
    assert result.mode == "llm (fake)" and result.cause == "explicação da LLM"


def test_falls_back_to_search_when_llm_fails():
    result = Diagnoser(llm=FakeLLM(fail=True)).diagnose(DEV_LOGS[0]["log"])
    assert result.mode == "busca" and result.warning and result.entry.id == "oom_sigkill"
