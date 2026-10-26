#!/usr/bin/env python3
"""runtimes/scripts/vendor-sync.py — Extern bezogene Skills in agentic-resources aktuell halten.

SSOT der Herkunft: vendor-lock.json (Repo-Wurzel). Übernommen aus Bachelorprojekt
scripts/vendor-sync.py (Skill-Teil); Plugins und Inventar bleiben dort.

Kommandos
  status   Gelockter Stand vs. neueste Upstream-Version je Skill (schreibt nichts).
  update   Hebt jeden Skill auf die neueste Release (bzw. Branch-HEAD) an. Dateiweiser
           3-Wege-Merge (Basis = gelockter Upstream-Commit, ours = Repo-Kopie, theirs =
           neuer Upstream): lokale Anpassungen bleiben erhalten, echte Konflikte landen
           als Marker in der Datei und im Report. Der Lock steigt nur bei konfliktfreiem
           Merge; nach dem Auflösen hebt `update --only <id>` ihn an. Ziele außerhalb
           von --root werden nie geschrieben.
  check    Jeder Vendor-Skill hat SKILL.md, passenden `name:` und keine Konfliktmarker
           (Exit 1 bei Befund).

Optionen
  --root DIR      Repo-Wurzel (Default: zwei Ebenen über diesem Skript; Env VENDOR_SYNC_ROOT)
  --only ID       nur diesen Eintrag (mehrfach erlaubt)
  --report FILE   Maschinenlesbarer JSON-Report (update/status)

Exit-Codes: 0 sauber, 1 Befund/Konflikt, 2 Nutzungs- oder Umgebungsfehler.
Cache der Upstream-Klone: ${VENDOR_SYNC_CACHE:-${XDG_CACHE_HOME:-~/.cache}/vendor-sync}
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

LOCK_REL = "vendor-lock.json"
CONFLICT_RE = re.compile(r"^(<<<<<<< |>>>>>>> )", re.M)


def die(msg, code=2):
    print("vendor-sync: " + msg, file=sys.stderr)
    sys.exit(code)


def run(cmd, cwd=None, check=True, text=True, input=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=text, input=input)
    if check and p.returncode != 0:
        err = p.stderr if text else p.stderr.decode("utf-8", "replace")
        die("Befehl fehlgeschlagen: %s\n%s" % (" ".join(cmd), err.strip()))
    return p


def repo_url(spec):
    if re.match(r"^[\w.-]+/[\w.-]+$", spec):
        return "https://github.com/%s" % spec
    return spec


def cache_dir():
    base = os.environ.get("VENDOR_SYNC_CACHE")
    if not base:
        base = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "vendor-sync")
    os.makedirs(base, exist_ok=True)
    return base


_fetched = {}


def upstream(spec):
    """Bare-Klon des Upstreams im Cache, einmal pro Lauf aktualisiert."""
    url = repo_url(spec)
    if url in _fetched:
        return _fetched[url]
    d = os.path.join(cache_dir(), hashlib.sha1(url.encode()).hexdigest()[:16])
    if not os.path.isdir(d):
        run(["git", "-c", "transfer.fsckObjects=true", "clone", "-q", "--bare", url, d])
    run(["git", "-C", d, "-c", "transfer.fsckObjects=true", "fetch", "-q", "--prune", "--tags", "--force", url,
         "+refs/heads/*:refs/heads/*"])
    _fetched[url] = d
    return d


def semver_key(v):
    m = re.match(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$", v)
    if not m:
        return None
    return tuple(int(x or 0) for x in m.groups())


def resolve_latest(entry):
    """-> (sha, version|None). track=release: höchste stabile SemVer-Tag, sonst Branch."""
    d = upstream(entry["repo"])
    if entry.get("track", "release") == "release":
        prefix = entry.get("tag_prefix", "")
        best = None
        for tag in run(["git", "-C", d, "tag", "--list"]).stdout.split():
            if not tag.startswith(prefix):
                continue
            key = semver_key(tag[len(prefix):])
            if key is not None and (best is None or key > best[0]):
                best = (key, tag)
        if best:
            sha = run(["git", "-C", d, "rev-parse", best[1] + "^{commit}"]).stdout.strip()
            return sha, best[1]
    ref = entry.get("branch") or "HEAD"
    sha = run(["git", "-C", d, "rev-parse", ref + "^{commit}"]).stdout.strip()
    return sha, None


def tree_files(d, sha, path):
    """{relpfad: (mode, blob)} unterhalb von path im Commit sha."""
    out = run(["git", "-C", d, "ls-tree", "-r", "-z", sha, "--", path.rstrip("/") + "/"]).stdout
    files = {}
    for rec in out.split("\0"):
        if not rec:
            continue
        meta, p = rec.split("\t", 1)
        mode, typ, blob = meta.split()
        if typ == "blob":
            rel = os.path.relpath(p, path)
            # Upstream-Bäume sind fremder Input: keine Symlinks, keine Pfade aus dem
            # Skill-Verzeichnis heraus.
            parts = rel.split("/")
            if mode == "120000" or os.path.isabs(rel) or ".." in parts or ".git" in parts:
                continue
            files[rel] = (mode, blob)
    return files


def blob(d, sha):
    return run(["git", "-C", d, "cat-file", "blob", sha], text=False).stdout


def is_binary(b):
    return b is not None and b"\0" in b[:8000]


def norm(b):
    return None if b is None or is_binary(b) else b.replace(b"\r\n", b"\n")


def read_local(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError):
        return None


def merge_text(ours, base, theirs):
    """-> (merged_bytes, konflikt?)"""
    with tempfile.TemporaryDirectory() as t:
        paths = []
        for name, data in (("ours", ours), ("base", base or b""), ("theirs", theirs)):
            p = os.path.join(t, name)
            with open(p, "wb") as f:
                f.write(data)
            paths.append(p)
        p = subprocess.run(["git", "merge-file", "-p", "-L", "lokal", "-L", "basis", "-L", "upstream"] + paths,
                           capture_output=True)
        if p.returncode < 0 or p.returncode > 127:
            die("git merge-file fehlgeschlagen: " + p.stderr.decode("utf-8", "replace"))
        return p.stdout, p.returncode > 0


def merge_skill(root, sid, entry, new_sha):
    d = upstream(entry["repo"])
    dest = os.path.join(root, entry["dest"])
    base_files = tree_files(d, entry["ref"], entry["path"]) if entry.get("ref") else {}
    new_files = tree_files(d, new_sha, entry["path"])
    if not new_files:
        return {"id": sid, "status": "upstream-removed",
                "detail": "%s fehlt im Upstream-Stand %s" % (entry["path"], new_sha[:12])}

    local = set()
    for dp, _, fns in os.walk(dest):
        for fn in fns:
            local.add(os.path.relpath(os.path.join(dp, fn), dest))

    res = {"id": sid, "status": "updated", "added": [], "modified": [], "deleted": [],
           "conflicts": [], "kept_local": []}
    for rel in sorted(set(base_files) | set(new_files) | local):
        target = os.path.join(dest, rel)
        if not inside(dest, target):
            res["conflicts"].append({"file": rel, "reason": "Pfad liegt außerhalb des Skill-Verzeichnisses"})
            continue
        b_raw = blob(d, base_files[rel][1]) if rel in base_files else None
        t_raw = blob(d, new_files[rel][1]) if rel in new_files else None
        o_raw = read_local(target)
        b, t, o = norm(b_raw), norm(t_raw), norm(o_raw)
        binary = any(is_binary(x) for x in (b_raw, t_raw, o_raw))
        if binary:
            b, t, o = b_raw, t_raw, o_raw

        if t == b:                      # Upstream unverändert -> lokaler Stand gilt
            if o != b:
                res["kept_local"].append(rel)
            continue
        if o == b:                      # lokal unverändert -> Upstream übernehmen
            if t is None:
                os.remove(target)
                res["deleted"].append(rel)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(t)
                if new_files[rel][0] == "100755":
                    os.chmod(target, 0o755)
                res["added" if o is None else "modified"].append(rel)
            continue
        if o == t:                      # beide Seiten identisch geändert
            continue
        # beide Seiten verschieden geändert
        if binary or t is None or o is None:
            why = ("binär" if binary else "upstream gelöscht, lokal geändert" if t is None
                   else "lokal gelöscht, upstream geändert")
            res["conflicts"].append({"file": rel, "reason": why})
            continue
        merged, conflict = merge_text(o, b, t)
        with open(target, "wb") as f:
            f.write(merged)
        res["modified"].append(rel)
        if conflict:
            res["conflicts"].append({"file": rel, "reason": "Textkonflikt (Marker in Datei)"})

    res["frontmatter"] = frontmatter_changes(d, entry, new_sha)
    res["upstream_log"] = run(["git", "-C", d, "log", "--oneline", "--no-decorate", "-n", "40",
                               "%s..%s" % (entry["ref"], new_sha), "--", entry["path"]],
                              check=False).stdout.splitlines() if entry.get("ref") else []
    if res["conflicts"]:
        res["status"] = "conflict"
    return res


def parse_frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text or "", re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"^([\w-]+):\s*(.*)$", line)
            if mm:
                fm[mm.group(1)] = mm.group(2).strip().strip("'\"")
    return fm


def frontmatter_changes(d, entry, new_sha):
    def at(sha):
        if not sha:
            return {}
        p = run(["git", "-C", d, "show", "%s:%s/SKILL.md" % (sha, entry["path"].rstrip("/"))], check=False)
        return parse_frontmatter(p.stdout if p.returncode == 0 else "")
    old, new = at(entry.get("ref")), at(new_sha)
    return {k: {"from": old.get(k), "to": new.get(k)}
            for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)}


def load_lock(root):
    p = os.path.join(root, LOCK_REL)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        die("Lock fehlt: %s" % p)
    except ValueError as e:
        die("Lock unlesbar: %s (%s)" % (p, e))


def save_lock(root, lock):
    with open(os.path.join(root, LOCK_REL), "w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2, ensure_ascii=False)
        f.write("\n")


def inside(root, path):
    r = os.path.realpath(root)
    return os.path.commonpath([os.path.realpath(path), r]) == r


def cmd_update(root, args, dry):
    lock = load_lock(root)
    report = {"skills": []}
    for sid in sorted(lock.get("skills", {})):
        if args.only and sid not in args.only:
            continue
        entry = lock["skills"][sid]
        sha, version = resolve_latest(entry)
        if sha == entry.get("ref"):
            report["skills"].append({"id": sid, "status": "current", "version": version or sha[:12]})
            continue
        span = {"from": entry.get("version") or (entry.get("ref") or "")[:12], "to": version or sha[:12]}
        if dry:
            report["skills"].append(dict(span, id=sid, status="available"))
            continue
        if not inside(root, os.path.join(root, entry["dest"])):
            report["skills"].append(dict(span, id=sid, status="external",
                                         detail="Ziel liegt außerhalb von --root — nicht geschrieben"))
            continue
        res = merge_skill(root, sid, entry, sha)
        res.update(span)
        if res["status"] == "updated":
            entry["ref"], entry["version"] = sha, version
        report["skills"].append(res)
    if not dry:
        save_lock(root, lock)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            f.write("\n")
    for s in report["skills"]:
        line = "skill  %-32s %-12s" % (s["id"], s["status"])
        if s.get("to") and s["status"] != "current":
            line += " %s -> %s" % (s.get("from"), s["to"])
        if s.get("conflicts"):
            line += "  KONFLIKTE: " + ", ".join("%s (%s)" % (c["file"], c["reason"]) for c in s["conflicts"])
        if s.get("detail"):
            line += "  " + s["detail"]
        print(line)
    bad = [s for s in report["skills"] if s["status"] in ("conflict", "upstream-removed", "external")]
    return 1 if bad else 0


def cmd_check(root, args):
    lock = load_lock(root)
    findings = []
    for sid, e in sorted(lock.get("skills", {}).items()):
        dest = os.path.join(root, e["dest"])
        skill_md = os.path.join(dest, "SKILL.md")
        if not os.path.isfile(skill_md):
            findings.append("vendor-skill-missing: %s (%s/SKILL.md fehlt)" % (sid, e["dest"]))
            continue
        with open(skill_md, encoding="utf-8", errors="replace") as f:
            name = parse_frontmatter(f.read()).get("name")
        if name != sid:
            findings.append("vendor-skill-name-mismatch: %s (frontmatter name=%r)" % (sid, name))
        for dp, _, fns in os.walk(dest):
            for fn in fns:
                fp = os.path.join(dp, fn)
                data = read_local(fp)
                if data and not is_binary(data) and CONFLICT_RE.search(data.decode("utf-8", "replace")):
                    findings.append("unresolved-conflict: %s" % os.path.relpath(fp, root))
    for f in findings:
        print(f)
    if findings:
        print("vendor-sync check: %d Befund(e)" % len(findings), file=sys.stderr)
        return 1
    print("vendor-sync check: sauber")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["status", "update", "check"])
    ap.add_argument("--root", default=os.environ.get("VENDOR_SYNC_ROOT") or
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument("--only", action="append")
    ap.add_argument("--report")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if args.command == "check":
        return cmd_check(root, args)
    return cmd_update(root, args, dry=args.command == "status")


if __name__ == "__main__":
    sys.exit(main())
