#!/usr/bin/env python3
"""Append-only local experiment index. No services, packages or training started."""
import argparse
import datetime
import fcntl
import json
import math
from pathlib import Path
import re
import uuid

KINDS = {"training", "artifact", "evaluation", "decision", "checkpoint"}
STATUSES = {"planned", "running", "completed", "failed", "unknown", "selected", "rejected", "paused", "deleted"}
# A deleted artifact must say what it was; null marks a value as unknown.
DELETED_KEYS = ("quantization", "source", "role", "metrics")

def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite metrics are not allowed")
    if isinstance(value, dict):
        for item in value.values(): finite(item)
    if isinstance(value, list):
        for item in value: finite(item)

def digest(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))

def validate(event):
    if not isinstance(event, dict): raise ValueError("event must be an object")
    if event.get("kind") not in KINDS: raise ValueError("invalid kind")
    if event.get("status") not in STATUSES: raise ValueError("invalid status")
    if not isinstance(event.get("subject"), str) or not event["subject"].strip():
        raise ValueError("subject required")
    details = event.get("details")
    if not isinstance(details, dict): raise ValueError("details object required")
    finite(event)
    if event["status"] in {"completed", "selected"}:
        refs = event.get("evidence")
        if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and r.strip() for r in refs):
            raise ValueError("completed/selected requires evidence references")
    if event["kind"] == "artifact" and event["status"] == "completed":
        if not digest(details.get("sha256")) or not details.get("quantization"):
            raise ValueError("completed artifact requires SHA-256 and quantization")
    if event["status"] == "deleted":
        if event["kind"] != "artifact": raise ValueError("deleted is only valid for artifacts")
        refs = event.get("evidence")
        if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and r.strip() for r in refs):
            raise ValueError("deleted artifact requires evidence references")
        if not digest(details.get("sha256")): raise ValueError("deleted artifact requires SHA-256")
        size = details.get("bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise ValueError("deleted artifact requires bytes")
        for key in ("path", "reason"):
            if not isinstance(details.get(key), str) or not details[key].strip():
                raise ValueError("deleted artifact requires " + key)
        missing = [key for key in DELETED_KEYS if key not in details]
        if missing: raise ValueError("deleted artifact requires " + ", ".join(missing) + " (null if unknown)")
    if event["kind"] == "evaluation" and event["status"] == "completed":
        if not all(digest(details.get(k)) for k in ("artifact_sha256", "testset_sha256")):
            raise ValueError("completed evaluation requires artifact and testset SHA-256")
        for key in ("runtime", "hardware", "metrics"):
            if not isinstance(details.get(key), dict) or not details[key]:
                raise ValueError("completed evaluation requires " + key + " object")
    return event

def read_events(handle):
    handle.seek(0)
    return [json.loads(line) for line in handle if line.strip()]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory-dir", type=Path, default=Path(__file__).resolve().parents[1] / "memory")
    commands = parser.add_subparsers(dest="command", required=True)
    append = commands.add_parser("append")
    append.add_argument("--file", type=Path, required=True)
    commands.add_parser("summary")
    args = parser.parse_args()
    path = args.memory_dir / "events.jsonl"
    if args.command == "summary":
        events = []
        if path.exists():
            with path.open() as handle:
                fcntl.flock(handle, fcntl.LOCK_SH)
                events = read_events(handle)
        print(json.dumps({"event_count": len(events), "events": events}, indent=2, ensure_ascii=False))
        return
    event = validate(json.loads(args.file.read_text()))
    event["id"] = str(uuid.uuid4())
    event["recorded_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    event["schema_version"] = 1
    # Never initialize memory implicitly: a wrong worktree/path must be visible.
    with path.open("r+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        read_events(handle)  # Refuse to append to corrupt/truncated history.
        handle.seek(0, 2)
        handle.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n")
        handle.flush()
        import os
        os.fsync(handle.fileno())
    print(event["id"])

if __name__ == "__main__":
    try: main()
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
