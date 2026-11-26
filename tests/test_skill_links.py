"""Link-integrity checks for non-vendor-lock skills in agentic-resources."""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "file:")
SKIP_DIRS = frozenset({
    "domains/web/anatomy",
    "domains/devtools/freetoken-setup",
    "domains/ml-training/huggingface-community-evals",
    "domains/ml-training/huggingface-llm-trainer",
    "domains/ml-training/huggingface-local-models",
    "domains/ml-training/huggingface-paper-publisher",
    "domains/ml-training/huggingface-tool-builder",
})
RETIRED_LITERALS = (
    "../../lib/behaviors/escalation-protocol.md",
    "../skill-sources.json",
    ".agents/skills/references/ticket-stage-procedure.md",
)


def _owned_skill_dirs(repo: Path = REPO) -> list[Path]:
    registry = json.loads((repo / "registry.json").read_text(encoding="utf-8"))["skills"]
    vendor_lock = json.loads((repo / "vendor-lock.json").read_text(encoding="utf-8"))["skills"]
    dirs = []
    for name, spec in sorted(registry.items()):
        if name in vendor_lock or spec.get("source") == "external":
            continue
        rel = spec["path"]
        if rel in SKIP_DIRS:
            continue
        sdir = repo / rel
        if sdir.is_dir():
            dirs.append(sdir)
    return dirs


def check_skill_links(repo: Path = REPO) -> list[str]:
    errors = []
    for sdir in _owned_skill_dirs(repo):
        for md in sorted(sdir.rglob("*.md")):
            if md.is_symlink():
                continue
            rel_md = md.relative_to(repo)
            text = md.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), 1):
                for lit in RETIRED_LITERALS:
                    if lit in line:
                        errors.append(f"{rel_md}:{lineno}: retired path literal {lit!r}")
                for match in MD_LINK_RE.finditer(line):
                    raw = match.group(2)
                    if raw.startswith(SKIP_PREFIXES):
                        continue
                    target = raw.split("#", 1)[0]
                    if not target or target == "URL":
                        continue
                    if not (md.parent / target).exists():
                        errors.append(f"{rel_md}:{lineno}: broken link ({raw})")
    return errors


def test_owned_skill_links_resolve():
    assert check_skill_links() == []


def test_fixture_broken_link_is_red(tmp_path):
    (tmp_path / "registry.json").write_text(
        json.dumps({"skills": {"demo": {"path": "core/demo", "source": "home"}}}),
        encoding="utf-8",
    )
    (tmp_path / "vendor-lock.json").write_text(
        json.dumps({"skills": {}}),
        encoding="utf-8",
    )
    demo = tmp_path / "core" / "demo"
    demo.mkdir(parents=True)
    (demo / "SKILL.md").write_text("See [missing](../../nowhere.md).\n", encoding="utf-8")
    errors = check_skill_links(repo=tmp_path)
    assert len(errors) == 1
    assert "broken link (../../nowhere.md)" in errors[0]
