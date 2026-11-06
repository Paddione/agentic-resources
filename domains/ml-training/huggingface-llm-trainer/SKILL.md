---
name: huggingface-llm-trainer
description: Train or fine-tune language and vision models using TRL (Transformer Reinforcement Learning) or Unsloth with Hugging Face Jobs infrastructure. Covers SFT, DPO, GRPO and reward modeling training methods, plus GGUF conversion for local deployment. Includes guidance on the TRL Jobs package, UV scripts with PEP 723 format, dataset preparation and validation, hardware selection, cost estimation, Trackio monitoring, Hub authentication, model selection/leaderboards and model persistence. Use for tasks involving cloud GPU training, GGUF conversion, or when users mention training on Hugging Face Jobs without local GPU setup.
license: Complete terms in LICENSE.txt
---

# TRL Training on Hugging Face Jobs

## Overview

Train language models using TRL (Transformer Reinforcement Learning) on fully managed Hugging Face infrastructure. No local GPU setup required—models train on cloud GPUs and results are automatically saved to the Hugging Face Hub.

**TRL provides multiple training methods:**
- **SFT** (Supervised Fine-Tuning) - Standard instruction tuning
- **DPO** (Direct Preference Optimization) - Alignment from preference data
- **GRPO** (Group Relative Policy Optimization) - Online RL training
- **Reward Modeling** - Train reward models for RLHF

**For detailed TRL method documentation:**
```python
hf_doc_search("your query", product="trl")
hf_doc_fetch("https://huggingface.co/docs/trl/sft_trainer")  # SFT
hf_doc_fetch("https://huggingface.co/docs/trl/dpo_trainer")  # DPO
# etc.
```

**See also:** `references/training_methods.md` for method overviews and selection guidance

## When to Use This Skill

Use this skill when users want to:
- Fine-tune language models on cloud GPUs without local infrastructure
- Train with TRL methods (SFT, DPO, GRPO, etc.)
- Run training jobs on Hugging Face Jobs infrastructure
- Convert trained models to GGUF for local deployment (Ollama, LM Studio, llama.cpp)
- Ensure trained models are permanently saved to the Hub
- Use modern workflows with optimized defaults

### When to Use Unsloth

Use **Unsloth** (`references/unsloth.md`) instead of standard TRL when:
- **Limited GPU memory** - Unsloth uses ~60% less VRAM
- **Speed matters** - Unsloth is ~2x faster
- Training **large models (>13B)** - memory efficiency is critical
- Training **Vision-Language Models (VLMs)** - Unsloth has `FastVisionModel` support

See `references/unsloth.md` for complete Unsloth documentation and `scripts/unsloth_sft_example.py` for a production-ready training script.

## Key Directives

When assisting with training jobs:

1. **ALWAYS use `hf_jobs()` MCP tool** - Submit jobs using `hf_jobs("uv", {...})`, NOT bash `trl-jobs` commands. The `script` parameter accepts Python code directly. Do NOT save to local files unless the user explicitly requests it. Pass the script content as a string to `hf_jobs()`. If user asks to "train a model", "fine-tune", or similar requests, you MUST create the training script AND submit the job immediately using `hf_jobs()`.

2. **Always include Trackio** - Every training script should include Trackio for real-time monitoring. Use example scripts in `scripts/` as templates.

3. **Provide job details after submission** - After submitting, provide job ID, monitoring URL, estimated time, and note that the user can request status checks later.

4. **Use example scripts as templates** - Reference `scripts/train_sft_example.py`, `scripts/train_dpo_example.py`, etc. as starting points.

## Local Script Execution

Repository scripts use PEP 723 inline dependencies. Run them with `uv run`:
```bash
uv run scripts/estimate_cost.py --help
uv run scripts/dataset_inspector.py --help
```

## Workflow

1. **Verify prerequisites** (account, token, dataset) — [references/prerequisites.md](references/prerequisites.md)
2. **Validate dataset** before GPU time (esp. DPO column names) — [references/dataset-validation.md](references/dataset-validation.md)
3. **Submit asynchronously** (create script with Trackio, submit via `hf_jobs()`, report, don't poll) — [references/async-guidelines.md](references/async-guidelines.md)
4. **Pick approach** (UV scripts default, TRL maintained scripts, Hub collections, CLI, trl-jobs) — [references/quickstart.md](references/quickstart.md)
5. **Size hardware, enable Hub push, set timeout** (LoRA >7B, push checklist, 30min default too short) — [references/hardware-hub.md](references/hardware-hub.md)
6. **Choose base model / estimate cost** (benchmarks, when to offer) — [references/model-cost.md](references/model-cost.md)
7. **Run & monitor** (example templates, Trackio defaults, job status, GGUF conversion, patterns) — [references/examples-monitoring.md](references/examples-monitoring.md)

## Reference files

- [references/prerequisites.md](references/prerequisites.md) — Account, dataset, critical settings
- [references/async-guidelines.md](references/async-guidelines.md) — Async submission flow incl. example response
- [references/quickstart.md](references/quickstart.md) — Sequence length + all four approaches
- [references/hardware-hub.md](references/hardware-hub.md) — Hardware table, Hub-push checklist, timeouts
- [references/model-cost.md](references/model-cost.md) — Benchmarks + cost estimation
- [references/dataset-validation.md](references/dataset-validation.md) — Inspector usage, DPO mapping
- [references/examples-monitoring.md](references/examples-monitoring.md) — Templates, Trackio, GGUF, patterns, failures
- [references/training_methods.md](references/training_methods.md) - Overview of SFT, DPO, GRPO, KTO, PPO, Reward Modeling
- [references/training_patterns.md](references/training_patterns.md) - Common training patterns and examples
- [references/unsloth.md](references/unsloth.md) - Unsloth for fast VLM training (~2x speed, 60% less VRAM)
- [references/gguf_conversion.md](references/gguf_conversion.md) - Complete GGUF conversion guide
- [references/trackio_guide.md](references/trackio_guide.md) - Trackio monitoring setup
- [references/hardware_guide.md](references/hardware_guide.md) - Hardware specs and selection
- [references/hub_saving.md](references/hub_saving.md) - Hub authentication troubleshooting
- [references/troubleshooting.md](references/troubleshooting.md) - Common issues and solutions
- [references/local_training_macos.md](references/local_training_macos.md) - Local training on macOS
- [scripts/train_sft_example.py](scripts/train_sft_example.py) - Production SFT template
- [scripts/train_dpo_example.py](scripts/train_dpo_example.py) - Production DPO template
- [scripts/train_grpo_example.py](scripts/train_grpo_example.py) - Production GRPO template
- [scripts/unsloth_sft_example.py](scripts/unsloth_sft_example.py) - Unsloth text LLM training template (faster, less VRAM)
- [scripts/estimate_cost.py](scripts/estimate_cost.py) - Estimate time and cost (offer when appropriate)
- [scripts/convert_to_gguf.py](scripts/convert_to_gguf.py) - Complete GGUF conversion script
- [scripts/hf_benchmarks.py](scripts/hf_benchmarks.py) - Search for benchmark results and leaderboards by task, alias or free text.

## External Links

- [TRL Documentation](https://huggingface.co/docs/trl)
- [TRL Jobs Training Guide](https://huggingface.co/docs/trl/en/jobs_training)
- [TRL Jobs Package](https://github.com/huggingface/trl-jobs)
- [HF Jobs Documentation](https://huggingface.co/docs/huggingface_hub/guides/jobs)
- [TRL Example Scripts](https://github.com/huggingface/trl/tree/main/examples/scripts)
- [UV Scripts Guide](https://docs.astral.sh/uv/guides/scripts/)
- [UV Scripts Organization](https://huggingface.co/uv-scripts)

## Key Takeaways

1. **Submit scripts inline** - The `script` parameter accepts Python code directly; no file saving required unless user requests
2. **Jobs are asynchronous** - Don't wait/poll; let user check when ready
3. **Always set timeout** - Default 30 min is insufficient; minimum 1-2 hours recommended
4. **Always enable Hub push** - Environment is ephemeral; without push, all results lost
5. **Include Trackio** - Use example scripts as templates for real-time monitoring
6. **Offer cost estimation** - When parameters are known, use `scripts/estimate_cost.py`
7. **Use UV scripts (Approach 1)** - Default to `hf_jobs("uv", {...})` with inline scripts; TRL maintained scripts for standard training; avoid bash `trl-jobs` commands in Claude Code
8. **Use hf_doc_fetch/hf_doc_search** for latest TRL documentation
9. **Validate dataset format** before training with dataset inspector (see [references/dataset-validation.md](references/dataset-validation.md))
10. **Choose appropriate hardware** for model size; use LoRA for models >7B
