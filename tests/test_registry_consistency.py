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
