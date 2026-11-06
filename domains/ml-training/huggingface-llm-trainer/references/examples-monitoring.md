# Example Scripts, Monitoring & Failure Modes

## Example Training Scripts

**Production-ready templates with all best practices:**

Load these scripts for correctly:

- **`../scripts/train_sft_example.py`** - Complete SFT training with Trackio, LoRA, checkpoints
- **`../scripts/train_dpo_example.py`** - DPO training for preference learning
- **`../scripts/train_grpo_example.py`** - GRPO training for online RL

These scripts demonstrate proper Hub saving, Trackio integration, checkpoint management, and optimized parameters. Pass their content inline to `hf_jobs()` or use as templates for custom scripts.

## Monitoring and Tracking

**Trackio** provides real-time metrics visualization. See [trackio_guide.md](trackio_guide.md) for complete setup guide.

**Key points:**
- Add `trackio` to dependencies
- Configure trainer with `report_to="trackio" and run_name="meaningful_name"`

### Trackio Configuration Defaults

**Use sensible defaults unless user specifies otherwise.** When generating training scripts with Trackio:

**Default Configuration:**
- **Space ID**: `{username}/trackio` (use "trackio" as default space name)
- **Run naming**: Unless otherwise specified, name the run in a way the user will recognize (e.g., descriptive of the task, model, or purpose)
- **Config**: Keep minimal - only include hyperparameters and model/dataset info
- **Project Name**: Use a Project Name to associate runs with a particular Project

**User overrides:** If user requests specific trackio configuration (custom space, run naming, grouping, or additional config), apply their preferences instead of defaults.


This is useful for managing multiple jobs with the same configuration or keeping training scripts portable.

See [trackio_guide.md](trackio_guide.md) for complete documentation including grouping runs for experiments.

### Check Job Status

```python
# List all jobs
hf_jobs("ps")

# Inspect specific job
hf_jobs("inspect", {"job_id": "your-job-id"})

# View logs
hf_jobs("logs", {"job_id": "your-job-id"})
```

**Remember:** Wait for user to request status checks. Avoid polling repeatedly.

## Converting Models to GGUF

After training, convert models to **GGUF format** for use with llama.cpp, Ollama, LM Studio, and other local inference tools. **See:** [gguf_conversion.md](gguf_conversion.md) for complete conversion guide; **quick conversion** submits the script there via `hf_jobs("uv", ...)` with `ADAPTER_MODEL`/`BASE_MODEL`/`OUTPUT_REPO` env vars.

## Common Training Patterns

See [training_patterns.md](training_patterns.md) for detailed examples including:
- Quick demo (5-10 minutes)
- Production with checkpoints
- Multi-GPU training
- DPO training (preference learning)
- GRPO training (online RL)

## Common Failure Modes

### Out of Memory (OOM)

**Fix (try in order):**
1. Reduce batch size: `per_device_train_batch_size=1`, increase `gradient_accumulation_steps=8`. Effective batch size is `per_device_train_batch_size` x `gradient_accumulation_steps`. For best performance keep effective batch size close to 128.
2. Enable: `gradient_checkpointing=True`
3. Upgrade hardware: t4-small → l4x1, a10g-small → a10g-large etc.

### Dataset Misformatted

**Fix:**
1. Validate first with dataset inspector:
   ```bash
   uv run https://huggingface.co/datasets/mcp-tools/skills/raw/main/dataset_inspector.py \
     --dataset name --split train
   ```
2. Check output for compatibility markers (✓ READY, ✗ NEEDS MAPPING, ✗ INCOMPATIBLE)
3. Apply mapping code from inspector output if needed

### Job Timeout

**Fix:**
1. Check logs for actual runtime: `hf_jobs("logs", {"job_id": "..."})`
2. Increase timeout with buffer: `"timeout": "3h"` (add 30% to estimated time)
3. Or reduce training: lower `num_train_epochs`, use smaller dataset, enable `max_steps`
4. Save checkpoints: `save_strategy="steps"`, `save_steps=500`, `hub_strategy="every_save"`

**Note:** Default 30min is insufficient for real training. Minimum 1-2 hours.

### Hub Push Failures

**Fix:**
1. Add to job: `secrets={"HF_TOKEN": "$HF_TOKEN"}`
2. Add to config: `push_to_hub=True`, `hub_model_id="username/model-name"`
3. Verify auth: `mcp__huggingface__hf_whoami()`
4. Check token has write permissions and repo exists (or set `hub_private_repo=True`)

### Missing Dependencies

**Fix:**
Add to PEP 723 header:
```python
# /// script
# dependencies = ["trl>=0.12.0", "peft>=0.7.0", "trackio", "missing-package"]
# ///
```

## Troubleshooting

**Common issues:**
- Job times out → Increase timeout, reduce epochs/dataset, use smaller model/LoRA
- Model not saved to Hub → Check push_to_hub=True, hub_model_id, secrets=HF_TOKEN
- Out of Memory (OOM) → Reduce batch size, increase gradient accumulation, enable LoRA, use larger GPU
- Dataset format error → Validate with dataset inspector (see [dataset-validation.md](dataset-validation.md))
- Import/module errors → Add PEP 723 header with dependencies, verify format
- Authentication errors → Check `mcp__huggingface__hf_whoami()`, token permissions, secrets parameter

**See:** [troubleshooting.md](troubleshooting.md) for complete troubleshooting guide
