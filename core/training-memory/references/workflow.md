# Local workflow and event contract

## Curated sources

Original synthesis of selected practices, not a vendored copy of upstream skills:
- [TRL training](https://github.com/huggingface/skills/tree/main/skills/trl-training): SFT uses demonstrations; DPO uses chosen/rejected pairs; GRPO needs executable reward functions. Begin with SFT for tool trajectories.
- [Community evals](https://github.com/huggingface/skills/tree/main/skills/huggingface-community-evals): smoke tests, consistent task/backend configuration, inspect-ai/lighteval where useful. These complement repo task tests; they do not prove plan-execution ability.
- [hf-mem](https://github.com/huggingface/skills/tree/main/skills/hf-mem): estimate inference memory before downloading; verify real RSS on target hosts.
- [Unsloth GGUF export](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf): merge/export, preserve the chat template, evaluate quantized artifacts.
- Local `~/.zcode/skills/unsloth-buddy/SKILL.md`: use hardware inspection, checkpoint continuity and role-aware export ideas. Do not inherit its automatic project creation, global memory writes or deployment lifecycle.

Check current library documentation and pinned local code before changing APIs. Existing repository dependency locks take precedence over upstream example pins.

## Existing integration points

Read current files under `~/unsloth-boxes` (or its owned worktree):
- `README.md`, `BOXES.md`, `decision-train/box.toml`, `decision-train/pyproject.toml`, `uv.lock`: launcher and environment contracts. Train and vLLM serving remain separate environments.
- `decision-train/src/measure_corpus.py`, `template_guard.py`, `train.py`: corpus lengths and template checks before training. Inspect CLI help before composing a command.
- `decision-train/src/langfuse_tracking.py`: local manifests/metrics are primary evidence; link optional existing Langfuse identifiers rather than implementing another telemetry client.
- `decision-train/src/eval_harness.py`, `eval_scoring.py`: existing action/no-action/clarification comparisons. Check whether a run uses fixtures or actual inference; this harness alone does not establish exported GGUF performance.
- `decision-train/src/export_gguf.py`: inspect merge-memory checks and quantization options.
- `decision-train/src/model-registry.sh`, `registry-db.sql`: existing registry may provide current values, but upserted scores are not an immutable history. Preserve report references in the ledger; do not deploy SQL for a status request.

GPU routing: repository docs require explicit `CUDA_DEVICE_ORDER=PCI_BUS_ID` and `CUDA_VISIBLE_DEVICES=1` for the 5070 Ti. Recheck device enumeration; shell defaults have previously selected the 3060 Ti. Documentation reports an earlier smoke run, not current readiness.

## Unsloth Studio MCP

The local Unsloth Studio MCP is configured in `~/.config/muse/settings.json` under server name `unsloth`, with URL `http://127.0.0.1:8888/mcp/` (configuration observed 2026-10-08). This is a configuration reference, not proof of connectivity or availability in another agent. Discover the current harness tools and read their schemas; do not invent tool names or assume all Studio capabilities are exposed.

For status/resume requests, use exposed read-only tools to inspect jobs, progress, model/checkpoint metadata and exports where supported. Capture the observation time, Studio job/model/export IDs and source alongside matching local manifest/report references. Mark conflicting or unavailable state explicitly; do not treat an old running record as a live job or overwrite history from a current snapshot.

For user-authorized training/export operations, use Studio MCP when its exposed tools support the requested operation and the correct environment/GPU can be selected. Keep Studio's environment distinct from `decision-train`/`decision-serve`; record which backend and configuration actually ran. Starting, cancelling, resuming or exporting through MCP must stay within the current task's authorization.

MCP export completion does not establish GGUF quality. Resolve the output artifact and its SHA-256, then evaluate that GGUF on the Ubuntu/WSL target hardware. Persist Studio evidence in the same ledger as CLI-launched experiments.

If the MCP is not exposed or unreachable, report that limitation and use existing local launcher/manifests for authorized work. Do not start Studio, change MCP configuration or generate credentials just to read the training-memory ledger. Bootstrap references, when setup is actually requested: `~/scripts/unsloth-studio-setup.py` and `~/agent-resources/unsloth-studio.json`. Read configuration without printing authorization headers, tokens or environment secrets.

## Training and evaluation

Use successful, sanitized trajectories from both repositories: plan step, actual tool schemas/results, edits, verification, and outcome. Include unnecessary-tool avoidance, failed tools and clarifications. Deduplicate and split by complete task/scenario, not turns from the same episode. Fingerprint corpora, testsets, prompts and templates.

Benchmark Qwen3.5 0.8B/2B/4B with the existing ladder alongside LFM2.5 (`LFM2.5-1.2B-Instruct`, `LFM2.5-1.2B-Thinking`, `LFM2.5-2.6B`, and sparse MoE `LFM2.5-8B-A1B` with ~1.5B active parameters for `coordinator` and `plan-executor`). For LFM2/LFM2.5 models, use `target_modules = ["w1", "w2", "w3", "q_proj", "k_proj", "v_proj", "out_proj", "in_proj"]` and verify `model.print_trainable_parameters()` before training. For Qwen3.5 check current upstream guidance and the trainer's precision safeguards; do not assume QLoRA is the default. Select model size per role based on measured results.

Compare Q4_K_M and Q5_K_M exports, optionally Q8_0 as a reference, initially 2048–4096 context tokens. Quantization names do not establish quality or speed. Measure exported GGUFs via llama.cpp CPU first, iGPU separately when supported. Record runtime commit/build, threads, CPU model, RAM availability, prompt tokens, output tokens, seed, sampler and repetitions. Record warm/cold load and first-token latency separately, and the two-model combined peak RSS. Select a role artifact only after its declared quality and resource criteria are met.

## Event JSON

Required common fields: `kind`, `subject`, `status`, `details` (object). Helper adds `id`, UTC `recorded_at`, schema version. Kinds: `training`, `artifact`, `evaluation`, `decision`, `checkpoint`. Statuses: `planned`, `running`, `completed`, `failed`, `unknown`, `selected`, `rejected`, `paused`, `deleted`.

- training: subject is run ID; details include role, base/revision, corpus hash, config, repo commits, checkpoint, manifest, GPU and next action. `completed` requires an evidence reference.
- artifact: subject identifies an export; details include `sha256`, `quantization`, path, bytes, training run ID, template fingerprint. `completed` requires evidence plus SHA-256 and quantization.
- artifact/deleted: history of a removed file, appended before the file is deleted. details require `path`, `sha256`, integer `bytes`, `reason` and the keys `quantization`, `source` (HF repo@revision or run ID), `role`, `metrics` (eval references or values); null marks an unknown value. Requires evidence. Never delete a file whose event could not be appended.
- evaluation: subject identifies one evaluation invocation; details include `artifact_sha256`, `testset_sha256`, `runtime`, `hardware`, `metrics`, role, baseline, context/sampler settings and report path. `completed` requires these identity/config fields and evidence. Use separate invocations for hardware/quant/context variants.
- decision: subject is role/selection name; details include candidate hashes, evaluation IDs, criteria, limitations and next action. `selected` requires evidence; no selection from loss alone.
- checkpoint: notes, reconciliation or corrections; include `corrects_event_id` when correcting an earlier entry. Summary is a chronological index; read correction events before relying on past claims.

`evidence` is a non-empty list of report/manifest paths or identifiers, stored at the top level. Paths may later be unavailable: verify before citing conclusions. Record absent values as null/unknown, not zero. Credentials and raw session dumps never belong in memory.
