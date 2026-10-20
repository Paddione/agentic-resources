"""--harness must add Home destinations without changing consumer behavior."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("with_harness", [True, False])
def test_harness_flag_controls_home_destinations(tmp_path, with_harness):
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
    command = ["bash", str(script), "--repo", str(consumer), "--layers", "core", "--dry-run"]
    if with_harness:
        command.append("--harness")
    result = subprocess.run(command, env={**os.environ, "HOME": str(home)}, capture_output=True, text=True, check=True)
    assert str(consumer / ".agents/skills/example") in result.stdout
    assert (str(home / ".agents/skills/example") in result.stdout) is with_harness
    assert (str(home / ".config/opencode/skills/example") in result.stdout) is with_harness
