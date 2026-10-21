"""Consumer targets are always linked; --harness adds Home targets (full matrix)."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_DIRS = [".agents/skills", ".claude/skills", ".codex/skills",
                ".opencode/skills", ".zcode/skills"]
HOME_DIRS = [".agents/skills", ".claude/skills", ".codex/skills",
             ".config/opencode/skills", ".zcode/skills",
             ".gemini/config/skills", ".pi/agent/skills",
             ".qwen/skills", ".openclaw/skills"]
# Kein Projekt-Gegenstueck mit <root>/skills-Layout (Home-only per init.sh).
HOME_ONLY_DIRS = [".gemini/config/skills", ".pi/agent/skills",
                  ".qwen/skills", ".openclaw/skills",
                  ".config/opencode/skills"]


def run_init(tmp_path, with_harness):
    resources = tmp_path / "resources"
    (resources / "runtimes").mkdir(parents=True)
    (resources / "core/example").mkdir(parents=True)
    (resources / "core/example/SKILL.md").write_text("---\nname: example\ndescription: fixture\n---\n")
    script = resources / "runtimes/init.sh"
    shutil.copyfile(Path(__file__).resolve().parents[1] / "runtimes/init.sh", script)
    consumer, home = tmp_path / "consumer", tmp_path / "home"
    consumer.mkdir()
    for directory in HOME_DIRS:
        (home / directory).mkdir(parents=True)
    command = ["bash", str(script), "--repo", str(consumer), "--layers", "core", "--dry-run"]
    if with_harness:
        command.append("--harness")
    result = subprocess.run(command, env={**os.environ, "HOME": str(home)},
                            capture_output=True, text=True, check=True)
    return consumer, home, result


@pytest.mark.parametrize("with_harness", [True, False])
def test_project_destinations_always_linked(tmp_path, with_harness):
    consumer, _home, result = run_init(tmp_path, with_harness)
    for directory in PROJECT_DIRS:
        assert str(consumer / directory / "example") in result.stdout


@pytest.mark.parametrize("with_harness", [True, False])
@pytest.mark.parametrize("directory", HOME_DIRS)
def test_harness_flag_controls_home_destinations(tmp_path, directory, with_harness):
    _consumer, home, result = run_init(tmp_path, with_harness)
    assert (str(home / directory / "example") in result.stdout) is with_harness


def test_home_only_dirs_have_no_project_counterpart(tmp_path):
    consumer, _home, result = run_init(tmp_path, False)
    for directory in HOME_ONLY_DIRS:
        assert str(consumer / directory / "example") not in result.stdout


def _fixture_resources(tmp_path):
    resources = tmp_path / "resources"
    (resources / "runtimes").mkdir(parents=True)
    (resources / "core/example").mkdir(parents=True)
    (resources / "core/example/SKILL.md").write_text("---\nname: example\ndescription: fixture\n---\n")
    script = resources / "runtimes/init.sh"
    shutil.copyfile(Path(__file__).resolve().parents[1] / "runtimes/init.sh", script)
    return script


def test_dangling_link_is_repaired(tmp_path):
    script = _fixture_resources(tmp_path)
    consumer = tmp_path / "consumer"
    destdir = consumer / ".agents/skills"
    destdir.mkdir(parents=True)
    (destdir / "example").symlink_to("/nonexistent-dead-target")
    assert not (destdir / "example").exists()
    result = subprocess.run(
        ["bash", str(script), "--repo", str(consumer), "--layers", "core"],
        capture_output=True, text=True, check=True,
    )
    assert "fixed" in result.stdout
    assert (destdir / "example").is_symlink()
    assert (destdir / "example").exists()


def test_real_file_never_overwritten(tmp_path):
    script = _fixture_resources(tmp_path)
    consumer = tmp_path / "consumer"
    destdir = consumer / ".agents/skills"
    destdir.mkdir(parents=True)
    (destdir / "example").write_text("user content")
    result = subprocess.run(
        ["bash", str(script), "--repo", str(consumer), "--layers", "core"],
        capture_output=True, text=True, check=True,
    )
    assert result.returncode == 0
    assert not (destdir / "example").is_symlink()
    assert (destdir / "example").read_text() == "user content"
