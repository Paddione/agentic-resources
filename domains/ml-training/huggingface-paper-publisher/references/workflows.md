# Integration Workflows & API

Run from the skill root (`../scripts/` from this file).

## Workflow 1: Publish New Research
```bash
# 1. Create research article
uv run ../scripts/paper_manager.py create \
  --template "modern" \
  --title "Novel Fine-Tuning Approach" \
  --output "paper.md"

# 2. Edit paper.md with your content

# 3. Submit to arXiv (external process)
# Upload to arxiv.org, get arXiv ID

# 4. Index on Hugging Face
uv run ../scripts/paper_manager.py index --arxiv-id "2301.12345"

# 5. Link to your model
uv run ../scripts/paper_manager.py link \
  --repo-id "your-username/your-model" \
  --repo-type "model" \
  --arxiv-id "2301.12345"

# 6. Claim authorship
uv run ../scripts/paper_manager.py claim \
  --arxiv-id "2301.12345" \
  --email "your.email@edu"
```

## Workflow 2: Link Existing Paper
```bash
# 1. Check if paper exists
uv run ../scripts/paper_manager.py check --arxiv-id "2301.12345"

# 2. Index if needed
uv run ../scripts/paper_manager.py index --arxiv-id "2301.12345"

# 3. Link to multiple repositories
uv run ../scripts/paper_manager.py link \
  --repo-id "username/model-v1" \
  --repo-type "model" \
  --arxiv-id "2301.12345"

uv run ../scripts/paper_manager.py link \
  --repo-id "username/training-data" \
  --repo-type "dataset" \
  --arxiv-id "2301.12345"

uv run ../scripts/paper_manager.py link \
  --repo-id "username/demo-space" \
  --repo-type "space" \
  --arxiv-id "2301.12345"
```

## Workflow 3: Update Model with Paper Reference
```bash
# 1. Get current README
hf download username/model-name README.md

# 2. Add paper link
uv run ../scripts/paper_manager.py link \
  --repo-id "username/model-name" \
  --repo-type "model" \
  --arxiv-id "2301.12345" \
  --citation "Full citation for the paper"

# The script will:
# - Add YAML metadata if missing
# - Insert arXiv link in README
# - Add formatted citation
# - Preserve existing content
```

## Advanced Usage

**Batch Link Papers:**
```bash
# Link multiple papers to one repository
for arxiv_id in "2301.12345" "2302.67890" "2303.11111"; do
  uv run ../scripts/paper_manager.py link \
    --repo-id "username/model-name" \
    --repo-type "model" \
    --arxiv-id "$arxiv_id"
done
```

**Extract Paper Info:**
```bash
# Get paper metadata from arXiv
uv run ../scripts/paper_manager.py info \
  --arxiv-id "2301.12345" \
  --format "json"
```

**Generate Citation:**
```bash
# Create BibTeX citation
uv run ../scripts/paper_manager.py citation \
  --arxiv-id "2301.12345" \
  --format "bibtex"
```

**Validate Links:**
```bash
# Check all paper links in a repository
uv run ../scripts/paper_manager.py validate \
  --repo-id "username/model-name" \
  --repo-type "model"
```

## Common Patterns

**Pattern 1: New Paper Publication**
```bash
# Write → Publish → Index → Link
uv run ../scripts/paper_manager.py create --template modern --output paper.md
# (Submit to arXiv)
uv run ../scripts/paper_manager.py index --arxiv-id "2301.12345"
uv run ../scripts/paper_manager.py link --repo-id "user/model" --arxiv-id "2301.12345"
```

**Pattern 2: Existing Paper Discovery**
```bash
# Search → Check → Link
uv run ../scripts/paper_manager.py search --query "transformers"
uv run ../scripts/paper_manager.py check --arxiv-id "2301.12345"
uv run ../scripts/paper_manager.py link --repo-id "user/model" --arxiv-id "2301.12345"
```

**Pattern 3: Author Portfolio Management**
```bash
# Claim → Verify → Organize
uv run ../scripts/paper_manager.py claim --arxiv-id "2301.12345"
uv run ../scripts/paper_manager.py list-my-papers
uv run ../scripts/paper_manager.py toggle-visibility --arxiv-id "2301.12345" --show true
```

## API Integration

**Python Script Example:**
```python
from scripts.paper_manager import PaperManager

pm = PaperManager(hf_token="your_token")

# Index paper
pm.index_paper("2301.12345")

# Link to model
pm.link_paper(
    repo_id="username/model",
    repo_type="model",
    arxiv_id="2301.12345",
    citation="Full citation text"
)

# Check status
status = pm.check_paper("2301.12345")
print(status)
```
