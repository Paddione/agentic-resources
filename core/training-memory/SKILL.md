---
name: training-memory
description: Track and resume Unsloth training and finished GGUF evaluations for unsloth-boxes and the base dotfiles repository. Use for training status, experiment history, role-model comparisons, GGUF selection, evaluation results, or resuming a run. Keeps durable evidence-linked memory across sessions.
---

# Training Memory

Maintain the experiment history for the local CPU agent team. Read `memory/project.json` and run `python3 scripts/ledger.py summary` with paths resolved relative to this skill. The ledger is durable memory, not live process status. Check launcher/process state before claiming a job is still running. Empty history means no runs recorded, not no runs ever occurred.

## Scope and roles

Target repositories: `~/unsloth-boxes` and the dotfiles Git repository at `~`. Roles: coordinator, plan executor, CodeRepoGraph specialist, script/task specialist. Plans come from Codex, Claude or MuseSpark. Teach execution and tool-selection behavior; retrieve mutable code, graph relationships, script arguments and task definitions at runtime.

Training uses the RTX 5070 Ti. Deployment targets Ubuntu/WSL2, two 16 GB Intel-iGPU laptops and three quadcore-i5/16 GB CPU hosts. Keep CPU inference as the baseline. Start with coordinator plus one swappable specialist, not four simultaneously resident models. GGUF role artifacts include merged adapter weights; orchestration lives outside the weights.

## Resume and record

1. Read memory, current repository rules, the box configuration and relevant evidence. Inspect existing run manifests/reports before starting another experiment. Record missing evidence as unknown.
2. For live Studio state, discover the **Unsloth Studio MCP** tools and inspect their actual schemas. Read the Studio MCP integration in [references/workflow.md](references/workflow.md). Correlate Studio job/model/export IDs with local manifests and GGUF hashes; persist evidence-linked observations in the ledger.
3. Read [references/workflow.md](references/workflow.md) for training, evaluation or GGUF selection. Use the existing pipeline rather than installing another stack.
4. Append a ledger event after an observed state change, export, evaluation or selection decision. Use `scripts/ledger.py append --file <event.json>`. Record experiment IDs, revisions, fingerprints and evidence paths; never raw credentials or private traces.
5. Preserve raw manifests/reports as the primary evidence. Ledger records index them and retain history. Never silently overwrite earlier evaluations. Correct mistakes with a new event referencing the earlier event ID.
6. Before ending, record what completed, what failed or remains unknown, and the next concrete action. Update project decisions only when the user changes requirements or measured evidence warrants a change.

Create/edit/commit skill memory in an owned dotfiles worktree using `~/scripts/agent-workspace.py`; preserve unrelated changes. Use the current skill installation's memory as input so a fresh worktree cannot silently lose uncommitted newer events. Reconcile divergent event histories by event ID before publishing. Do not auto-merge branches or replace an installation with divergent memory.

## Evidence rules

- Training completion is not GGUF export, a passed evaluation, or deployment readiness.
- Link finished GGUFs by SHA-256, quantization, base revision and adapter/run ID. A filename alone is insufficient.
- Compare base, trained model and the actual exported GGUF on held-out tasks. Tag fixture runs as fixtures; they are not measurements of a model.
- Keep quality scores separate from CPU latency, decode throughput, peak RSS and context/KV-cache settings. Hardware and runtime build belong to each measurement.
- Test two-model residency and role switching separately from single-model inference. WSL's available memory may be lower than the host's 16 GB. No throughput promises without target-host measurements.
- `hf-mem` estimates inference weight/KV memory, not training activations, optimizer state or total process RSS.
- Do not launch training, publish to Hub, start services or change a database merely because this skill is invoked for status. Follow the user's authorized task.

The helper is standard-library Python on Linux/WSL. No HF/Unsloth MCP is required to read memory. Use available MCPs for authorized live operations, otherwise existing CLI/Python tools. See [references/workflow.md](references/workflow.md) for source links and event fields.
