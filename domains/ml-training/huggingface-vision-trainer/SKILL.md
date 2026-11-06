---
name: huggingface-vision-trainer
description: Trains and fine-tunes vision models for object detection (D-FINE, RT-DETR v2, DETR, YOLOS), image classification (timm models — MobileNetV3, MobileViT, ResNet, ViT/DINOv3 — plus any Transformers classifier), and SAM/SAM2 segmentation using Hugging Face Transformers on Hugging Face Jobs cloud GPUs. Covers COCO-format dataset preparation, Albumentations augmentation, mAP/mAR evaluation, accuracy metrics, SAM segmentation with bbox/point prompts, DiceCE loss, hardware selection, cost estimation, Trackio monitoring, and Hub persistence. Use when users mention training object detection, image classification, SAM, SAM2, segmentation, image matting, DETR, D-FINE, RT-DETR, ViT, timm, MobileNet, ResNet, bounding box models, or fine-tuning vision models on Hugging Face Jobs.
---

# Vision Model Training on Hugging Face Jobs

Train object detection, image classification, and SAM/SAM2 segmentation models on managed cloud GPUs. No local GPU setup required—results are automatically saved to the Hugging Face Hub.

## When to Use This Skill

Use this skill when users want to:
- Fine-tune object detection models (D-FINE, RT-DETR v2, DETR, YOLOS) on cloud GPUs or local
- Fine-tune image classification models (timm: MobileNetV3, MobileViT, ResNet, ViT/DINOv3, or any Transformers classifier) on cloud GPUs or local
- Fine-tune SAM or SAM2 models for segmentation / image matting using bbox or point prompts
- Train bounding-box detectors on custom datasets
- Train image classifiers on custom datasets
- Train segmentation models on custom mask datasets with prompts
- Run vision training jobs on Hugging Face Jobs infrastructure
- Ensure trained vision models are permanently saved to the Hub

## Related Skills

- **`huggingface-llm-trainer`** — General HF Jobs infrastructure: token authentication, hardware flavors, timeout management, cost estimation, secrets, environment variables, scheduled jobs, and result persistence. **See that skill's Jobs sections for any non-training-specific Jobs questions** (e.g., "how do secrets work?", "what hardware is available?", "how do I pass tokens?").
- **`trl-training`** — TRL-based language model training (SFT, DPO, GRPO). Use that skill for text/language model fine-tuning.

## Local Script Execution

Helper scripts use PEP 723 inline dependencies. Run them with `uv run`:
```bash
uv run scripts/dataset_inspector.py --dataset username/dataset-name --split train
uv run scripts/estimate_cost.py --help
```

## Training workflow

Follow [references/workflow.md](references/workflow.md) step by step and track progress with the user:

1. **Verify prerequisites** (account, token, dataset) — [references/prerequisites.md](references/prerequisites.md)
2. **Validate dataset** before GPU time (inspector + bbox preprocessing) — [references/dataset-validation.md](references/dataset-validation.md)
3. **Ask user preferences** (dataset size, validation split, hardware) via AskUserQuestion tool
4. **Prepare training script** (OD / IC / SAM templates + copy-paste args) — [references/quickstart-object-detection.md](references/quickstart-object-detection.md), [references/quickstart-image-classification.md](references/quickstart-image-classification.md), [references/quickstart-sam.md](references/quickstart-sam.md)
5. **Save, submit, report** (job ID, monitoring URL, Trackio dashboard, cost) — submission methods in [references/job-directives.md](references/job-directives.md#1-job-submission-hf_jobs-mcp-tool-vs-python-api)

**Critical rules** (submission syntax, token injection, flags, timeouts, Trackio): [references/job-directives.md](references/job-directives.md) — follow exactly, they prevent the common failures.

**Models & hardware** (OD / IC / SAM tables, VRAM guidance): [references/models-hardware.md](references/models-hardware.md).

**During the run** (status checks, OOM, format errors, push 401s, timeouts): [references/operations.md](references/operations.md).

## Reference files

- [scripts/object_detection_training.py](scripts/object_detection_training.py) — Production-ready object detection training script
- [scripts/image_classification_training.py](scripts/image_classification_training.py) — Production-ready image classification training script (supports timm models)
- [scripts/sam_segmentation_training.py](scripts/sam_segmentation_training.py) — Production-ready SAM/SAM2 segmentation training script (bbox & point prompts)
- [scripts/dataset_inspector.py](scripts/dataset_inspector.py) — Validate dataset format for OD, classification, and SAM segmentation
- [scripts/estimate_cost.py](scripts/estimate_cost.py) — Estimate training costs for any vision model (includes SAM/SAM2)
- [references/prerequisites.md](references/prerequisites.md) — Account, dataset requirements, critical settings
- [references/dataset-validation.md](references/dataset-validation.md) — Inspector usage and bbox preprocessing
- [references/workflow.md](references/workflow.md) — Full 5-step workflow incl. AskUserQuestion template
- [references/job-directives.md](references/job-directives.md) — Submission methods, token injection, flags, timeouts, Trackio
- [references/models-hardware.md](references/models-hardware.md) — Model tables and hardware guidance
- [references/quickstart-object-detection.md](references/quickstart-object-detection.md) — Copy-paste OD args
- [references/quickstart-image-classification.md](references/quickstart-image-classification.md) — Copy-paste IC args
- [references/quickstart-sam.md](references/quickstart-sam.md) — Copy-paste SAM args
- [references/operations.md](references/operations.md) — Status checks and failure modes
- [references/object_detection_training_notebook.md](references/object_detection_training_notebook.md) — Object detection training workflow, augmentation strategies, and training patterns
- [references/image_classification_training_notebook.md](references/image_classification_training_notebook.md) — Image classification training workflow with ViT, preprocessing, and evaluation
- [references/finetune_sam2_trainer.md](references/finetune_sam2_trainer.md) — SAM2 fine-tuning walkthrough with MicroMat dataset, DiceCE loss, and Trainer integration
- [references/timm_trainer.md](references/timm_trainer.md) — Using timm models with HF Trainer (TimmWrapper, transforms, full example)
- [references/hub_saving.md](references/hub_saving.md) — Detailed Hub persistence guide and verification checklist
- [references/reliability_principles.md](references/reliability_principles.md) — Failure prevention principles from production experience

## External links

- [Transformers Object Detection Guide](https://huggingface.co/docs/transformers/tasks/object_detection)
- [Transformers Image Classification Guide](https://huggingface.co/docs/transformers/tasks/image_classification)
- [DETR Model Documentation](https://huggingface.co/docs/transformers/model_doc/detr)
- [ViT Model Documentation](https://huggingface.co/docs/transformers/model_doc/vit)
- [HF Jobs Guide](https://huggingface.co/docs/huggingface_hub/guides/jobs) — Main Jobs documentation
- [HF Jobs Configuration](https://huggingface.co/docs/hub/en/jobs-configuration) — Hardware, secrets, timeouts, namespaces
- [HF Jobs CLI Reference](https://huggingface.co/docs/huggingface_hub/guides/cli#hf-jobs) — Command line interface
- [Object Detection Models](https://huggingface.co/models?pipeline_tag=object-detection)
- [Image Classification Models](https://huggingface.co/models?pipeline_tag=image-classification)
- [SAM2 Model Documentation](https://huggingface.co/docs/transformers/model_doc/sam2)
- [SAM Model Documentation](https://huggingface.co/docs/transformers/model_doc/sam)
- [Object Detection Datasets](https://huggingface.co/datasets?task_categories=task_categories:object-detection)
- [Image Classification Datasets](https://huggingface.co/datasets?task_categories=task_categories:image-classification)
