"""--harness must add Home destinations without changing consumer behavior."""
import os
import shutil
import subprocess
from pathlib import Path


def test_harness_flag_adds_home_destinations(tmp_path):
    resources = tmp_path / "resources"
    (resources / "runtimes").mkdir(parents=True)
    (resources / "core/example").mkdir(parents=True)
    (resources / "core/example/SKILL.md").write_text("---\nname: example\ndescription: fixture\n---\n")
    script = resources / "runtimes/init.sh"
    shutil.copyfile(Path(__file__).resolve().parents[1] / "runtimes/init.sh", script)
    consumer, home = tmp_path / "consumer", tmp_path / "home"
    consumer.mkdir()
    for directory in [".agents/skills", ".claude/skills", ".config/opencode/skills", ".zcode/skills"]:
        (home / directory).mkdir(parents=True)
    result = subprocess.run(["bash", str(script), "--repo", str(consumer), "--layers", "core", "--harness", "--dry-run"], env={**os.environ, "HOME": str(home)}, capture_output=True, text=True, check=True)
    assert str(consumer / ".agents/skills/example") in result.stdout
    assert str(home / ".agents/skills/example") in result.stdout
    assert str(home / ".config/opencode/skills/example") in result.stdout
