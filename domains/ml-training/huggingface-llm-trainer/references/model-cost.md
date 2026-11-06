# Base Model Selection & Cost Estimation

## Choose a Base Model (Model Selection)

**Identify models to train based on task type or benchmark results.**

Use `../scripts/hf_benchmarks.py` to identify top-performing models for specific tasks. This helps the user select a model as the base for training, whilst keeping size and hardware constraints in mind.

```bash
# Get help on the benchmarks command:
uv run ../scripts/hf_benchmarks.py --help
```

### Example -- choosing an OCR base model
```bash
# Search for benchmarks containing whose name contains the text `ocr`
uv run ../scripts/hf_benchmarks.py search --query ocr

# Get the ranked leaderboard for the allenai/olmOCR-bench benchmark
uv run ../scripts/hf_benchmarks.py leaderboard allenai/olmOCR-bench
```

## Cost Estimation

**Offer to estimate cost when planning jobs with known parameters.** Use `../scripts/estimate_cost.py`:

```bash
uv run ../scripts/estimate_cost.py \
  --model meta-llama/Llama-2-7b-hf \
  --dataset trl-lib/Capybara \
  --hardware a10g-large \
  --dataset-size 16000 \
  --epochs 3
```

Output includes estimated time, cost, recommended timeout (with buffer), and optimization suggestions.

**When to offer:** User planning a job, asks about cost/time, choosing hardware, job will run >1 hour or cost >$5
