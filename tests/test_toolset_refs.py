"""Toolset-Referenzen: tote Pfade in toolset-curate/SKILL.md fail-closed (P2).

P-Entscheid: KEIN lokales runtimes/toolset/capabilities.yaml. Die
Toolset-Kuration (capabilities.yaml, mcp.yaml, toolset.lock.yaml, Karten,
Skripte) lebt im Bachelorprojekt-Consumer (docs/agent-guide/registry/...);
AR hält nur den kuratierenden Skill. Eingetragen als EXTERNAL mit Begründung;
jeder neue Pfad in der SKILL.md muss entweder im Repo existieren oder hier
explizit als extern markiert werden. Konsum-Pfad je Consumer via
repo.yaml-Schlüssel toolset_registry_path (siehe runtimes/repo.yaml.schema).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "domains/devtools/toolset-curate/SKILL.md"

# Repo-relative Pfade, die bewusst auf den Bachelorprojekt-Consumer zeigen.
EXTERNAL = {
    "docs/agent-guide/registry/capabilities.yaml": "Kurations-SSOT im Bachelorprojekt",
    "docs/agent-guide/registry/mcp.yaml": "Server-Erreichbarkeit im Bachelorprojekt",
    "docs/agent-guide/registry/tools.yaml": "CLI/Agent-Erfassung im Bachelorprojekt",
    "docs/agent-guide/registry/toolset.lock.yaml": "gemessene Tool-Zahlen im Bachelorprojekt",
    "docs/agent-guide/maps/toolset-map.md": "generierte Karte im Bachelorprojekt",
    ".agents/skills/references/mcp-tool-guide.md": "Consumer-Ablage (AR: core/references/mcp-tool-guide.md)",
    ".agents/plans/toolset-tool-level/design.md": "Bachelorprojekt-Planpfad",
    ".claude/settings.json": "Harness-Config (Consumer)",
    "scripts/toolset-context.sh": "Bachelorprojekt-Skript",
    "scripts/toolset/collect.mjs": "Bachelorprojekt-Skript",
    "scripts/toolset/check.mjs": "Bachelorprojekt-Skript",
    "scripts/toolset/sync.mjs": "Bachelorprojekt-Skript",
    "scripts/toolset/emit-map.mjs": "Bachelorprojekt-Skript",
    "scripts/toolset/probe.mjs": "Bachelorprojekt-Skript",
    "scripts/toolset/lib/roles.mjs": "Rollen-Vokabular-SSOT im Bachelorprojekt",
    "scripts/plan-context.sh": "Bachelorprojekt-Skript (Negativreferenz)",
}

PATH_RE = re.compile(r"`((?:docs|scripts|runtimes|\.agents|\.claude)/[^`]*?)`")


def referenced_paths(text=SKILL.read_text()):
    found = set()
    for match in PATH_RE.findall(text):
        for part in match.split():
            part = part.strip("(),;")
            if "/" not in part or part.startswith("http"):
                continue
            part = re.sub(r"\{[^}]*\}", "*", part)
            if "*" in part:
                continue
            found.add(part)
    return found


def check_refs(skill_text=SKILL.read_text()):
    errors = []
    for path in sorted(referenced_paths(skill_text)):
        if (REPO / path).exists():
            continue
        if path in EXTERNAL:
            continue
        errors.append(f"tote Referenz ohne External-Markierung: {path}")
    return errors


def test_no_local_capabilities_shadow():
    assert not (REPO / "runtimes/toolset/capabilities.yaml").exists(), \
        "lokale capabilities.yaml würde den Bachelorprojekt-SSOT spiegeln (P2: external)"


def test_all_refs_resolve_or_are_external():
    assert check_refs() == []


def test_schema_names_toolset_registry_path():
    schema = (REPO / "runtimes/repo.yaml.schema").read_text()
    assert "toolset_registry_path" in schema


def test_fixture_unmarked_dead_path_is_red(tmp_path):
    text = "siehe `docs/agent-guide/registry/neu-erfunden.yaml` und `scripts/toolset/neu.mjs`"
    errors = check_refs(skill_text=text)
    assert len(errors) == 2
