---
name: huggingface-paper-publisher
description: Publish and manage research papers on Hugging Face Hub. Supports creating paper pages, linking papers to models/datasets, claiming authorship, and generating professional markdown-based research articles. Publishing only; to read or summarize papers, use huggingface-papers.
---

# Overview
This skill provides comprehensive tools for AI engineers and researchers to publish, manage, and link research papers on the Hugging Face Hub. It streamlines the workflow from paper creation to publication, including integration with arXiv, model/dataset linking, and authorship management.

## Integration with HF Ecosystem
- **Paper Pages**: Index and discover papers on Hugging Face Hub
- **arXiv Integration**: Automatic paper indexing from arXiv IDs
- **Model/Dataset Linking**: Connect papers to relevant artifacts through metadata
- **Authorship Verification**: Claim and verify paper authorship
- **Research Article Template**: Generate professional, modern scientific papers

# Version
1.0.0

# Dependencies
The included script uses PEP 723 inline dependencies. Prefer `uv run` over
manual environment setup.

- huggingface_hub>=0.26.0
- pyyaml>=6.0.3
- requests>=2.32.5
- markdown>=3.5.0
- python-dotenv>=1.2.1

# Core Capabilities

- **Paper Page Management** — index from arXiv, claim authorship, manage visibility, discover papers
- **Link Papers to Artifacts** — model/dataset cards, auto `arxiv:` tags, citations
- **Research Article Creation** — markdown templates (`standard`, `modern`, `arxiv`, `ml-report`), LaTeX math, HTML convert
- **Metadata Management** — YAML frontmatter, citation tracking, multi-paper links

# Usage

Scripts live in `scripts/`; run with `uv run` and a Write-access `HF_TOKEN`. All paths are relative to the skill root — `cd` there first or use full paths.

- **Methods** (index, link, claim, visibility, create): [references/methods.md](references/methods.md)
- **Templates, command reference, YAML metadata**: [references/templates-commands.md](references/templates-commands.md)
- **Workflows** (publish new, link existing, update model), **advanced use** (batch, info, citation, validate), **patterns**, **Python API**: [references/workflows.md](references/workflows.md)
- **Best practices, errors, troubleshooting, roadmap**: [references/ops.md](references/ops.md)
- **Quick reference**: [references/quick_reference.md](references/quick_reference.md)

Complements [tfrere's research article template](https://huggingface.co/spaces/tfrere/research-article-template): write there, publish + link here.

# Resources and References

- **Hugging Face Paper Pages**: [hf.co/papers](https://huggingface.co/papers)
- **Model Cards Guide**: [hf.co/docs/hub/model-cards](https://huggingface.co/docs/hub/en/model-cards)
- **Dataset Cards Guide**: [hf.co/docs/hub/datasets-cards](https://huggingface.co/docs/hub/en/datasets-cards)
- **Research Article Template**: [tfrere/research-article-template](https://huggingface.co/spaces/tfrere/research-article-template)
- **arXiv Format Guide**: [arxiv.org/help/submit](https://arxiv.org/help/submit)
