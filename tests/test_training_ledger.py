"""training-memory ledger: Validierung des Loesch-Historienformats (artifact/deleted)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "core/training-memory/scripts/ledger.py"
SHA = "a" * 64


def deleted_event(**overrides):
    details = {"path": "/mnt/f/models/x/x-Q4_K_M.gguf", "sha256": SHA, "bytes": 123,
               "quantization": "Q4_K_M", "source": "hf:org/x@abc", "role": "D1",
               "metrics": None, "reason": "ohne-rolle"}
    details.update(overrides)
    return {"kind": "artifact", "status": "deleted", "subject": "x-Q4_K_M.gguf",
            "details": details, "evidence": ["inventory-2026-10-27.json"]}


def run(memory, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--memory-dir", str(memory), *args],
                          capture_output=True, text=True)


def append(tmp_path, event):
    memory = tmp_path / "memory"
    memory.mkdir(exist_ok=True)
    (memory / "events.jsonl").touch()
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event))
    return run(memory, "append", "--file", str(path)), memory / "events.jsonl"


def test_deleted_artifact_with_full_history_is_appended(tmp_path):
    result, events = append(tmp_path, deleted_event())
    assert result.returncode == 0, result.stderr
    stored = json.loads(events.read_text())
    assert stored["status"] == "deleted" and stored["details"]["sha256"] == SHA


def test_deleted_artifact_allows_unknown_values_as_null(tmp_path):
    result, _ = append(tmp_path, deleted_event(quantization=None, source=None, role=None))
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("field", ["sha256", "path", "bytes", "reason",
                                   "quantization", "source", "role", "metrics"])
def test_deleted_artifact_requires_every_history_field(tmp_path, field):
    event = deleted_event()
    del event["details"][field]
    result, events = append(tmp_path, event)
    assert result.returncode != 0
    assert events.read_text() == ""


@pytest.mark.parametrize("override", [{"sha256": "abc"}, {"bytes": -1}, {"bytes": "12"},
                                      {"reason": " "}, {"path": ""}])
def test_deleted_artifact_rejects_invalid_values(tmp_path, override):
    result, _ = append(tmp_path, deleted_event(**override))
    assert result.returncode != 0


def test_deleted_artifact_requires_evidence(tmp_path):
    event = deleted_event()
    del event["evidence"]
    result, _ = append(tmp_path, event)
    assert result.returncode != 0


def test_deleted_status_is_only_valid_for_artifacts(tmp_path):
    event = deleted_event()
    event["kind"] = "training"
    result, _ = append(tmp_path, event)
    assert result.returncode != 0
