# Resume Pipeline

An end-to-end AI pipeline that builds and polishes a resume from your raw profile data.

## How TO RUN

```
python main.py
```

## Inputs

Edit the variables at the top of `main.py`:

| Variable | Description | Example |
|---|---|---|
| `Name` | Full name | `"Jane Doe"` |
| `Email` | Contact email | `"jane@example.com"` |
| `Location` | City, Country | `"San Francisco, CA"` |
| `Work_experience` | Work history in plain text or Markdown | See `main.py` |
| `Education` | Degree(s) and institution(s) | `"B.S. CS, UC Berkeley (2018)"` |
| `Skills` | Comma-separated skill list | `"Python, Go, AWS"` |
| `GITHUB_URL` | Your GitHub profile URL (set `""` to skip) | `"https://github.com/username"` |
| `PUBLICATION_URLS` | List of paper URLs, e.g. arXiv links (set `[]` to skip) | `["https://arxiv.org/abs/..."]` |
| `TARGET_JOB` | Job dict to tailor the resume toward (set `None` to skip) | See `main.py` |

## Output

**`resume/resume_final.md`** — the polished, job-tailored resume.

## Requirements
```
pip install openai python-dotenv requests
```