# Prerequisites Checklist

Before starting any training job, verify:

## ✅ **Account & Authentication**
- Hugging Face Account with [Pro](https://hf.co/pro), [Team](https://hf.co/enterprise), or [Enterprise](https://hf.co/enterprise) plan (Jobs require paid plan)
- Authenticated login: Check with `hf_whoami()`
- **HF_TOKEN for Hub Push** ⚠️ CRITICAL - Training environment is ephemeral, must push to Hub or ALL training results are lost
- Token must have write permissions
- **MUST pass `secrets={"HF_TOKEN": "$HF_TOKEN"}` in job config** to make token available (the `$HF_TOKEN` syntax
  references your actual token value)

## ✅ **Dataset Requirements**
- Dataset must exist on Hub or be loadable via `datasets.load_dataset()`
- Format must match training method (SFT: "messages"/text/prompt-completion; DPO: chosen/rejected; GRPO: prompt-only)
- **ALWAYS validate unknown datasets** before GPU training to prevent format failures (see [dataset-validation.md](dataset-validation.md))
- Size appropriate for hardware (Demo: 50-100 examples on t4-small; Production: 1K-10K+ on a10g-large/a100-large)

## ⚠️ **Critical Settings**
- **Timeout must exceed expected training time** - Default 30min is TOO SHORT for most training. Minimum recommended: 1-2 hours. Job fails and loses all progress if timeout is exceeded.
- **Hub push must be enabled** - Config: `push_to_hub=True`, `hub_model_id="username/model-name"`; Job: `secrets={"HF_TOKEN": "$HF_TOKEN"}`
