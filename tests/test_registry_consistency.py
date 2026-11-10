"""Registry-vs-disk consistency: registry.json indexes every skill (AGENTS.md)."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LAYERS = ("core", "lifecycle", "domains")


def _on_disk_skills():
    found = {}
    for layer in LAYERS:
        root = REPO / layer
        if not root.is_dir():
            continue
        for skill_file in root.rglob("SKILL.md"):
            if "staging" in skill_file.parts:
                continue
            rel = skill_file.parent.relative_to(REPO)
            found[rel.name] = str(rel)
    return found


def _registry():
    return json.loads((REPO / "registry.json").read_text())["skills"]


def test_every_on_disk_skill_is_registered():
    on_disk = _on_disk_skills()
    registered = {name for name, spec in _registry().items()}
    missing = sorted(set(on_disk) - registered)
    assert missing == [], f"SKILL.md on disk but missing in registry.json: {missing}"


def test_every_registered_path_exists_on_disk():
    missing = sorted(
        f"{name}: {spec.get('path')}"
        for name, spec in _registry().items()
        if not (REPO / spec.get("path", "")).is_dir()
    )
    assert missing == [], f"registry.json paths missing on disk: {missing}"


def _lock():
    return json.loads((REPO / "vendor-lock.json").read_text())["skills"]


def _upstream_errors(registry=None, lock=None):
    """Upstream-Pflicht bei source: external; Richtung: lock.ref gewinnt (P4)."""
    registry = registry if registry is not None else _registry()
    lock = lock if lock is not None else _lock()
    errors = []
    for name, spec in registry.items():
        if spec.get("source") != "external":
            continue
        up = spec.get("upstream") or {}
        for field in ("source", "revision", "vendor_id"):
            if not up.get(field):
                errors.append(f"{name}: upstream.{field} fehlt (Pflicht bei source: external)")
        if name in lock:
            if up.get("revision") != lock[name].get("ref"):
                errors.append(f"{name}: upstream.revision != vendor-lock ref")
            if up.get("vendor_id") != name:
                errors.append(f"{name}: upstream.vendor_id != vendor-lock-Schlüssel")
            if up.get("path") != lock[name].get("path"):
                errors.append(f"{name}: upstream.path != vendor-lock path")
    for name in lock:
        if name in registry and registry[name].get("source") != "external":
            if name not in NON_EXTERNAL_LOCK_TRACKED:
                errors.append(f"{name}: vendor-lock-geführt, aber registry.source != external "
                              f"(neu: als external mit upstream einordnen oder begründet aufnehmen)")
    return errors


# vendor-lock-geführte Skills, deren Registry-Quelle bewusst nicht external ist
# (via Bachelorprojekt ererbt; Klassifikation in P4 eingefroren, s. vendor-map.md).
# Neue Namen fallen hier rot heraus und erzwingen eine Einordnungsentscheidung.
NON_EXTERNAL_LOCK_TRACKED = frozenset({
    "gitops-cluster-debug", "gitops-knowledge", "gitops-repo-audit", "hf-mem",
    "huggingface-best", "huggingface-community-evals", "huggingface-datasets",
    "huggingface-llm-trainer", "huggingface-local-models", "huggingface-lora-space-builder",
    "huggingface-paper-publisher", "huggingface-papers", "huggingface-tool-builder",
    "huggingface-trackio", "huggingface-vision-trainer", "huggingface-zerogpu",
    "lavish", "llama-cpp", "playwright-best-practices", "python-testing-patterns",
    "skill-creator", "sota-testing", "train-sentence-transformers", "transformers-js",
    "trl-training", "vitest", "vitest-testing",
})


def test_external_skills_have_upstream_and_match_lock():
    assert _upstream_errors() == []


def test_fixture_external_without_upstream_is_red():
    reg = {"x": {"path": "domains/a/x", "source": "external"}}
    assert any("upstream.source" in e for e in _upstream_errors(registry=reg, lock={}))


def test_fixture_lock_ref_mismatch_is_red():
    reg = {"x": {"path": "d", "source": "external",
                 "upstream": {"source": "s", "revision": "neu", "vendor_id": "x", "path": "p"}}}
    lock = {"x": {"ref": "alt", "path": "p"}}
    assert any("!= vendor-lock ref" in e for e in _upstream_errors(registry=reg, lock=lock))


def test_fixture_lock_tracked_as_non_external_is_red():
    reg = {"x": {"path": "d", "source": "bachelorprojekt"}}
    lock = {"x": {"ref": "r", "path": "p"}}
    assert any("!= external" in e for e in _upstream_errors(registry=reg, lock=lock))
