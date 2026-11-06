# Methods (Detailed)

All paths below are relative to the skill root — prefix with `../` from this file, e.g. `uv run ../scripts/paper_manager.py ...`. Before running any script, first `cd` to the skill directory or use the full path.

## Method 1: Index Paper from arXiv

Add a paper to Hugging Face Paper Pages from arXiv.

**Basic Usage:**
```bash
uv run ../scripts/paper_manager.py index \
  --arxiv-id "2301.12345"
```

**Check If Paper Exists:**
```bash
uv run ../scripts/paper_manager.py check \
  --arxiv-id "2301.12345"
```

**Direct URL Access:**
You can also visit `https://huggingface.co/papers/{arxiv-id}` directly to index a paper.

## Method 2: Link Paper to Model/Dataset

Add paper references to model or dataset README with proper YAML metadata.

**Add to Model Card:**
```bash
uv run ../scripts/paper_manager.py link \
  --repo-id "username/model-name" \
  --repo-type "model" \
  --arxiv-id "2301.12345"
```

**Add to Dataset Card:**
```bash
uv run ../scripts/paper_manager.py link \
  --repo-id "username/dataset-name" \
  --repo-type "dataset" \
  --arxiv-id "2301.12345"
```

**Add Multiple Papers:**
```bash
uv run ../scripts/paper_manager.py link \
  --repo-id "username/model-name" \
  --repo-type "model" \
  --arxiv-ids "2301.12345,2302.67890,2303.11111"
```

**With Custom Citation:**
```bash
uv run ../scripts/paper_manager.py link \
  --repo-id "username/model-name" \
  --repo-type "model" \
  --arxiv-id "2301.12345" \
  --citation "$(cat citation.txt)"
```

### How Linking Works

When you add an arXiv paper link to a model or dataset README:
1. The Hub extracts the arXiv ID from the link
2. A tag `arxiv:<PAPER_ID>` is automatically added to the repository
3. Users can click the tag to view the Paper Page
4. The Paper Page shows all models/datasets citing this paper
5. Papers are discoverable through filters and search

## Method 3: Claim Authorship

Verify your authorship on papers published on Hugging Face.

**Start Claim Process:**
```bash
uv run ../scripts/paper_manager.py claim \
  --arxiv-id "2301.12345" \
  --email "your.email@institution.edu"
```

**Manual Process:**
1. Navigate to your paper's page: `https://huggingface.co/papers/{arxiv-id}`
2. Find your name in the author list
3. Click your name and select "Claim authorship"
4. Wait for admin team verification

**Check Authorship Status:**
```bash
uv run ../scripts/paper_manager.py check-authorship \
  --arxiv-id "2301.12345"
```

## Method 4: Manage Paper Visibility

Control which verified papers appear on your public profile.

**List Your Papers:**
```bash
uv run ../scripts/paper_manager.py list-my-papers
```

**Toggle Visibility:**
```bash
uv run ../scripts/paper_manager.py toggle-visibility \
  --arxiv-id "2301.12345" \
  --show true
```

**Manage in Settings:**
Navigate to your account settings → Papers section to toggle "Show on profile" for each paper.

## Method 5: Create Research Article

Generate a professional markdown-based research paper using modern templates.

**Create from Template:**
```bash
uv run ../scripts/paper_manager.py create \
  --template "standard" \
  --title "Your Paper Title" \
  --output "paper.md"
```

**Available Templates:**
- `standard` - Traditional scientific paper structure
- `modern` - Clean, web-friendly format inspired by Distill
- `arxiv` - arXiv-style formatting
- `ml-report` - Machine learning experiment report

**Generate Complete Paper:**
```bash
uv run ../scripts/paper_manager.py create \
  --template "modern" \
  --title "Fine-Tuning Large Language Models with LoRA" \
  --authors "Jane Doe, John Smith" \
  --abstract "$(cat abstract.txt)" \
  --output "paper.md"
```

**Convert to HTML:**
```bash
uv run ../scripts/paper_manager.py convert \
  --input "paper.md" \
  --output "paper.html" \
  --style "modern"
```
