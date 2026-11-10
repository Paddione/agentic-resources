"""repo.yaml: Profile ⊆ Schema, jeder Schlüssel von Skills referenziert (P5)."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SCHEMA = REPO / "runtimes/repo.yaml.schema"
PROFILES = REPO / "runtimes/profiles"
MAP = REPO / "docs/maps/repo-yaml-map.md"
LAYERS = ("core", "lifecycle", "domains")

# Begriffliche (nicht wortgleiche) Referenzen — explizit begründet, fail-closed
# für neue Schlüssel: ein neuer Schema-Schlüssel ohne exakte und ohne hier
# eingetragene begründete Referenz fällt rot heraus.
ALIASES = {
    # Schlüssel: (Datei, [alle diese Teilstrings müssen in der Datei stehen])
    "agent_ignore_files": (
        "core/references/agent-optimized-repo.md",
        [".aiderignore", ".claudeignore"],
    ),
    "toolset_registry_path": (
        "domains/devtools/toolset-curate/SKILL.md",
        ["repo.yaml", "capabilities.yaml"],
    ),
}


def _repo_keys(path):
    data = yaml.safe_load(path.read_text())
    assert str(data.get("schema_version")) == "1", f"{path}: schema_version != 1"
    return set((data.get("repo") or {}).keys())


def _skill_text():
    texts = {}
    for layer in LAYERS:
        root = REPO / layer
        for md in root.rglob("*.md"):
            if "staging" in md.parts:
                continue
            texts[str(md.relative_to(REPO))] = md.read_text()
    return texts


def check_repo_yaml(schema_path=SCHEMA, profiles_dir=PROFILES):
    errors = []
    try:
        schema_keys = _repo_keys(schema_path)
    except FileNotFoundError:
        return ["Schema fehlt"]
    for profile in sorted(profiles_dir.glob("*.yaml")):
        extra = _repo_keys(profile) - schema_keys
        if extra:
            errors.append(f"{profile.name}: Schlüssel nicht im Schema: {sorted(extra)}")
    texts = _skill_text()
    blob = "\n".join(texts.values())
    for key in sorted(schema_keys):
        if key in blob:
            continue
        alias = ALIASES.get(key)
        if alias and alias[0] in texts and all(s in texts[alias[0]] for s in alias[1]):
            continue
        errors.append(f"toter Schlüssel (keine Skill-Referenz): {key}")
    return errors


def test_profiles_match_schema_and_keys_are_referenced():
    assert check_repo_yaml() == []


def test_map_covers_all_keys():
    assert MAP.is_file(), f"Map fehlt: {MAP}"
    text = MAP.read_text()
    missing = [k for k in _repo_keys(SCHEMA) if k not in text]
    assert missing == [], f"Map nennt nicht: {missing}"


def test_fixture_dead_key_is_red(tmp_path):
    schema = tmp_path / "schema.yaml"
    schema.write_text("schema_version: 1\nrepo:\n  lebendig: true\n  tot_xyz: true\n")
    profdir = tmp_path / "profiles"
    profdir.mkdir()
    (profdir / "a.yaml").write_text("schema_version: 1\nrepo:\n  lebendig: true\n  extra_xyz: true\n")
    errors = check_repo_yaml(schema_path=schema, profiles_dir=profdir)
    assert any("extra_xyz" in e for e in errors)
    assert any("tot_xyz" in e for e in errors)
