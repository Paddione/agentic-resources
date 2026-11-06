# Operations: Job Status & Failure Modes

## Checking job status

**MCP tool (if available):**
```
hf_jobs("ps")                                   # List all jobs
hf_jobs("logs", {"job_id": "your-job-id"})      # View logs
hf_jobs("inspect", {"job_id": "your-job-id"})   # Job details
```

**Python API fallback:**
```python
from huggingface_hub import HfApi
api = HfApi()
api.list_jobs()                                  # List all jobs
api.get_job_logs(job_id="your-job-id")           # View logs
api.get_job(job_id="your-job-id")                # Job details
```

## Common failure modes

### OOM (CUDA out of memory)
Reduce `per_device_train_batch_size` (try 4, then 2), reduce `IMAGE_SIZE`, or upgrade hardware (`t4-small` → `l4x1` → `a10g-large` → `l40s` → `a100-large`).

### Dataset format errors
Run `../scripts/dataset_inspector.py` first. The training script auto-detects xyxy vs xywh, converts string categories to integer IDs, and adds `image_id` if missing. Ensure `objects.bbox` contains 4-value coordinate lists in absolute pixels and `objects.category` contains either integer IDs or string labels.

### Hub push failures (401)
Verify: (1) job secrets include token (see [job-directives.md](job-directives.md#2-authentication-via-job-secrets--explicit-hub_token-injection)), (2) script sets `training_args.hub_token` BEFORE creating the `Trainer`, (3) `push_to_hub=True` is set, (4) correct `hub_model_id`, (5) token has write permissions.

### Job timeout
Increase timeout (see [job-directives.md](job-directives.md#5-timeout-management) table), reduce epochs/dataset, or use checkpoint strategy with `hub_strategy="every_save"`.

### KeyError: 'test' (missing test split)
The object detection training script handles this gracefully — it falls back to the `validation` split. Ensure you're using the latest `../scripts/object_detection_training.py`.

### Single-class dataset: "iteration over a 0-d tensor"
`torchmetrics.MeanAveragePrecision` returns scalar (0-d) tensors for per-class metrics when there's only one class. The template `../scripts/object_detection_training.py` handles this by calling `.unsqueeze(0)` on these tensors. Ensure you're using the latest template.

### Poor detection performance (mAP < 0.15)
Increase epochs (30-50), ensure 500+ images, check per-class mAP for imbalanced classes, try different learning rates (1e-5 to 1e-4), increase image size.

For comprehensive troubleshooting: see [reliability_principles.md](reliability_principles.md)
