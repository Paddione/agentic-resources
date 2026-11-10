"""Prompts-Konsistenz: jede .md in runtimes/prompts braucht einen Manifest-Eintrag (P1)."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO / "runtimes" / "prompts"
MANIFEST = PROMPTS_DIR / "manifest.yaml"
MAP = REPO / "docs" / "maps" / "prompts-map.md"
REQUIRED_FIELDS = ("id", "role", "harness", "version")


def load_manifest(path=MANIFEST):
    return yaml.safe_load(path.read_text())


def check_manifest(prompts_dir=PROMPTS_DIR, manifest_path=MANIFEST):
    errors = []
    try:
        data = yaml.safe_load(manifest_path.read_text())
    except FileNotFoundError:
        return [f"Manifest fehlt: {manifest_path}"]
    entries = (data or {}).get("prompts", [])
    by_file = {}
    seen_ids = set()
    for entry in entries:
        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"Eintrag ohne {field}: {entry}")
        if entry.get("id") in seen_ids:
            errors.append(f"doppelte id: {entry.get('id')}")
        seen_ids.add(entry.get("id"))
        if entry.get("file"):
            by_file[entry["file"]] = entry["id"]
    md_files = sorted(p.name for p in prompts_dir.glob("*.md"))
    for name in md_files:
        if name not in by_file:
            errors.append(f"Prompt ohne Manifest-Eintrag: {name}")
    for fname in by_file:
        if not (prompts_dir / fname).is_file():
            errors.append(f"Manifest-Eintrag ohne Datei: {fname}")
    return errors


def check_map(map_path=MAP, manifest_path=MANIFEST):
    try:
        data = yaml.safe_load(manifest_path.read_text())
    except FileNotFoundError:
        return [f"Manifest fehlt: {manifest_path}"]
    if not map_path.is_file():
        return [f"Map fehlt: {map_path}"]
    text = map_path.read_text()
    return [f"Map nennt {e['id']} nicht" for e in (data or {}).get("prompts", [])
            if e.get("id") and e["id"] not in text]


def test_manifest_covers_all_prompts():
    assert check_manifest() == []


def test_map_covers_all_prompts():
    assert check_map() == []


def test_fixture_missing_entry_is_red(tmp_path):
    d = tmp_path / "prompts"
    d.mkdir()
    (d / "a.md").write_text("# a\n")
    (d / "b.md").write_text("# b\n")
    m = tmp_path / "manifest.yaml"
    m.write_text(yaml.safe_dump({"prompts": [
        {"id": "a", "file": "a.md", "role": "x", "harness": "y", "version": 1}]}))
    errors = check_manifest(prompts_dir=d, manifest_path=m)
    assert any("b.md" in e for e in errors)


def test_fixture_dangling_entry_is_red(tmp_path):
    d = tmp_path / "prompts"
    d.mkdir()
    (d / "a.md").write_text("# a\n")
    m = tmp_path / "manifest.yaml"
    m.write_text(yaml.safe_dump({"prompts": [
        {"id": "a", "file": "a.md", "role": "x", "harness": "y", "version": 1},
        {"id": "ghost", "file": "ghost.md", "role": "x", "harness": "y", "version": 1}]}))
    assert any("ghost.md" in e for e in check_manifest(prompts_dir=d, manifest_path=m))
