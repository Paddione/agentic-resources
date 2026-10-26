"""vendor-sync: 3-Wege-Merge, Lock-Disziplin und Check gegen ein lokales Upstream-Fixture."""
import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "runtimes/scripts/vendor-sync.py"
SKILL_V1 = "---\nname: zq-demo\ndescription: demo\n---\n\nzeile-a\nzeile-b\nzeile-c\nzeile-d\nzeile-e\n"
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
           "GIT_CONFIG_GLOBAL": "/dev/null"}


class Fixture:
    def __init__(self, tmp_path):
        self.t = tmp_path
        self.up = tmp_path / "up"
        self.root = tmp_path / "root"
        self.env = {**os.environ, **GIT_ENV, "VENDOR_SYNC_CACHE": str(tmp_path / "cache")}
        self.skill = self.up / "skills/zq-demo/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.skill.write_text(SKILL_V1)
        self.git("add", "-A")
        self.git("commit", "-qm", "v1")
        self.git("tag", "v1.0.0")
        self.base = self.git("rev-parse", "HEAD")
        dest = self.root / "domains/demo/zq-demo"
        dest.mkdir(parents=True)
        (dest / "SKILL.md").write_text(SKILL_V1.replace("zeile-e\n", "zeile-e LOKALER-PATCH\n"))
        (self.root / "vendor-lock.json").write_text(json.dumps({"schema_version": 1, "skills": {"zq-demo": {
            "repo": str(self.up), "path": "skills/zq-demo", "dest": "domains/demo/zq-demo",
            "track": "release", "ref": self.base, "version": "v1.0.0"}}}))

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.up), *args], env=self.env, check=True,
                              capture_output=True, text=True).stdout.strip()

    def release(self, old, new, tag):
        self.skill.write_text(self.skill.read_text().replace(old, new))
        self.git("commit", "-qam", tag)
        self.git("tag", tag)

    def sync(self, *args):
        return subprocess.run(["python3", str(SCRIPT), *args, "--root", str(self.root)],
                              env=self.env, capture_output=True, text=True)

    def local(self):
        return (self.root / "domains/demo/zq-demo/SKILL.md").read_text()

    def lock(self):
        return json.loads((self.root / "vendor-lock.json").read_text())["skills"]["zq-demo"]


@pytest.fixture
def fx(tmp_path):
    return Fixture(tmp_path)


def test_update_uebernimmt_upstream_und_erhaelt_lokalen_patch(fx):
    fx.release("zeile-a\n", "zeile-a UPSTREAM-NEU\n", "v1.1.0")
    r = fx.sync("update")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "zeile-a UPSTREAM-NEU" in fx.local() and "zeile-e LOKALER-PATCH" in fx.local()
    assert fx.lock()["version"] == "v1.1.0"


def test_konflikt_wird_gemeldet_haelt_den_lock_und_check_findet_marker(fx):
    fx.release("zeile-e\n", "zeile-e UPSTREAM-ANDERS\n", "v1.1.0")
    r = fx.sync("update")
    assert r.returncode == 1 and "KONFLIKTE: SKILL.md" in r.stdout
    assert fx.lock()["ref"] == fx.base
    r = fx.sync("check")
    assert r.returncode == 1 and "unresolved-conflict: domains/demo/zq-demo/SKILL.md" in r.stdout


def test_status_schreibt_nichts(fx):
    fx.release("zeile-a\n", "zeile-a UPSTREAM-NEU\n", "v1.1.0")
    before = fx.local()
    r = fx.sync("status")
    assert r.returncode == 0 and "available" in r.stdout
    assert fx.local() == before and fx.lock()["ref"] == fx.base


def test_ziel_ausserhalb_des_roots_wird_nicht_geschrieben(fx):
    outside = fx.t / "fremd/zq-demo"
    outside.parent.mkdir()
    (fx.root / "domains/demo/zq-demo").rename(outside)
    (fx.root / "domains/demo/zq-demo").symlink_to(outside)
    before = (outside / "SKILL.md").read_text()
    fx.release("zeile-a\n", "zeile-a UPSTREAM-NEU\n", "v1.1.0")
    r = fx.sync("update")
    assert r.returncode == 1 and "external" in r.stdout
    assert (outside / "SKILL.md").read_text() == before and fx.lock()["ref"] == fx.base


def test_repo_lock_ist_konsistent_mit_registry_und_kopien():
    root = SCRIPT.parents[2]
    lock = json.loads((root / "vendor-lock.json").read_text())["skills"]
    registry = json.loads((root / "registry.json").read_text())["skills"]
    assert lock, "vendor-lock.json ist leer"
    for sid, entry in lock.items():
        assert registry[sid]["path"] == entry["dest"], sid
    r = subprocess.run(["python3", str(SCRIPT), "check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_upstream_symlink_eintraege_werden_nicht_uebernommen(fx):
    (fx.up / "skills/zq-demo/evil").symlink_to("../../../ausserhalb")
    fx.release("zeile-a\n", "zeile-a UPSTREAM-NEU\n", "v1.1.0")
    fx.git("add", "-A")
    fx.git("commit", "-qm", "symlink")
    fx.git("tag", "v1.2.0")
    r = fx.sync("update")
    dest = fx.root / "domains/demo/zq-demo"
    assert not os.path.lexists(dest / "evil"), r.stdout
    assert "zeile-a UPSTREAM-NEU" in fx.local()


def test_lokaler_symlink_im_ziel_leitet_keine_schreibzugriffe_nach_aussen(fx):
    outside = fx.t / "ausserhalb"
    outside.mkdir()
    (fx.root / "domains/demo/zq-demo/sub").symlink_to(outside)
    (fx.up / "skills/zq-demo/sub").mkdir()
    (fx.up / "skills/zq-demo/sub/x.md").write_text("upstream\n")
    fx.git("add", "-A")
    fx.git("commit", "-qm", "sub")
    fx.git("tag", "v1.1.0")
    r = fx.sync("update")
    assert not (outside / "x.md").exists(), r.stdout
    assert r.returncode == 1 and "außerhalb" in r.stdout


@pytest.mark.parametrize("trusted, group, touched", [
    ([], "external", True), ([], "trusted", False),
    (["zq-owner"], "trusted", True), (["zq-owner"], "external", False),
])
def test_group_filtert_nach_vertrauenswuerdigem_upstream_besitzer(fx, trusted, group, touched):
    lock_path = fx.root / "vendor-lock.json"
    lock = json.loads(lock_path.read_text())
    lock["trusted_owners"] = trusted
    lock["skills"]["zq-demo"]["owner"] = "zq-owner"
    lock_path.write_text(json.dumps(lock))
    fx.release("zeile-a\n", "zeile-a UPSTREAM-NEU\n", "v1.1.0")
    r = fx.sync("update", "--group", group)
    assert r.returncode == 0, r.stdout + r.stderr
    assert ("zeile-a UPSTREAM-NEU" in fx.local()) is touched


def test_besitzer_kommt_aus_github_kurzform():
    import importlib.util
    spec = importlib.util.spec_from_file_location("vs", SCRIPT)
    vs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vs)
    assert vs.owner_of({"repo": "Paddione/skills"}) == "paddione"
    assert vs.owner_of({"repo": "https://github.com/Paddione/skills.git"}) == "paddione"
    assert vs.owner_of({"repo": "/tmp/up", "owner": "Zq"}) == "zq"
