"""Link-Matrix: links.yaml stimmt mit allen drei Sync-Mechanismen überein (P3)."""
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
LINKS = REPO / "runtimes/links.yaml"
MAP = REPO / "docs/maps/skill-sync-map.md"


def _quoted_list(text, var):
    matches = re.findall(var + r"=\(([^)]*)\)", text)
    bodies = [b for b in matches if b.strip()]
    assert bodies, f"{var} nicht gefunden"
    quoted = re.findall(r'"([^"]+)"', bodies[-1])
    if quoted:
        return quoted
    return bodies[-1].split()


def _py_tuple(text, var):
    m = re.search(var + r"\s*=\s*\((.*?)\)", text, re.S)
    assert m, f"{var} nicht gefunden"
    return re.findall(r"'([^']+)'", m.group(1))


def load_links(path=LINKS):
    return yaml.safe_load(path.read_text())


def check_links(data=None):
    errors = []
    data = data or load_links()
    mechs = {m["name"]: m for m in data.get("mechanisms", [])}
    for name in ("init.sh", "share-agent-resources.sh", "agent-resources.py"):
        if name not in mechs:
            errors.append(f"Mechanismus fehlt in links.yaml: {name}")
    if errors:
        return errors
    init = (REPO / "runtimes/init.sh").read_text()
    share = (REPO / "runtimes/scripts/share-agent-resources.sh").read_text()
    inv = (REPO / "runtimes/scripts/agent-resources.py").read_text()
    home = [p.replace("$HOME/", "~/") for p in _quoted_list(init, "HARNESS_DIRS")]
    proj = [p.replace("$REPO/", "") for p in _quoted_list(init, "PROJECT_DIRS")]
    if mechs["init.sh"].get("harness_dirs") != home:
        errors.append(f"init.sh harness_dirs drift: {home}")
    if mechs["init.sh"].get("project_dirs") != proj:
        errors.append(f"init.sh project_dirs drift: {proj}")
    if mechs["share-agent-resources.sh"].get("skill_dirs") != _quoted_list(share, "SKILL_DIRS"):
        errors.append("share-agent-resources.sh skill_dirs drift")
    if mechs["share-agent-resources.sh"].get("context_files") != _quoted_list(share, "CONTEXT_FILES"):
        errors.append("share-agent-resources.sh context_files drift")
    if mechs["agent-resources.py"].get("skill_roots") != list(_py_tuple(inv, "SKILL_ROOTS")):
        errors.append("agent-resources.py skill_roots drift")
    return errors


def test_link_matrix_matches_sources():
    assert check_links() == []


def test_map_covers_all_mechanisms():
    assert MAP.is_file(), f"Map fehlt: {MAP}"
    text = MAP.read_text()
    for name in ("init.sh", "share-agent-resources.sh", "agent-resources.py"):
        assert name in text, f"Map nennt {name} nicht"


def test_fixture_drift_is_red(tmp_path):
    data = load_links()
    data["mechanisms"][0]["harness_dirs"] = ["~/.erfunden/skills"]
    assert any("drift" in e for e in check_links(data=data))
