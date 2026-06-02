# Profile Builder

Enriches a raw profile with GitHub project summaries and publication summaries, producing a single `enriched_profile.md` for the resume pipeline.

## Setup

```bash
pip install openai python-dotenv requests
```

Create a `.env` file:
```
MIMO_API_KEY=your_key_here
```

## Run

```bash
python main.py
```

## Inputs

| File | Required | Description |
|------|----------|-------------|
| `inputs/profile.md` | Yes | Work experience, education, skills |
| `inputs/github_url.txt` | No | Single GitHub profile URL |
| `inputs/publications.txt` | No | One DOI / arXiv URL per line |

## Outputs

| File | Description |
|------|-------------|
| `workspace/github_summary.md` | Top-5 repo summaries (if GitHub URL provided) |
| `workspace/publications_summary.md` | Publication summaries (if publications provided) |
| `output/enriched_profile.md` | Final merged profile — input for next pipeline stage |
