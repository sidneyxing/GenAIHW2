# Profile Builder — Claude Code Spec

## Goal

Build the data enrichment pipeline that takes raw user inputs and produces a single
`enriched_profile.md` file. This file is the canonical input for the rest of the
resume agent pipeline and must be self-contained.

---

## Directory Structure

```
profile-builder/
├── inputs/
│   ├── profile.md            # User-provided: work experience, education, skills
│   ├── github_url.txt        # (optional) Single GitHub profile URL
│   └── publications.txt      # (optional) One DOI / arXiv URL / link per line
├── workspace/
│   ├── github_summary.md     # Output of GitHub enricher
│   └── publications_summary.md  # Output of publication enricher
└── output/
    └── enriched_profile.md   # Final merged profile, handed off to next stage
```

---

## MIMO API Convention

All LLM calls use the MIMO API (OpenAI-compatible). Use this pattern for every agent call:

```python
from openai import OpenAI

client = OpenAI(
    api_key="<MIMO_API_KEY>",        # load from environment variable MIMO_API_KEY
    base_url="https://api.xiaomimimo.com/v1"
)

def call_mimo(system_prompt: str, user_content: str, use_web_search: bool = False) -> str:
    kwargs = {
        "model": "mimo-v2.5",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ],
        "max_completion_tokens": 1024,
        "temperature": 1.0,
        "top_p": 0.95,
        "stream": False,
        "stop": None,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    if use_web_search:
        kwargs["tools"] = [
            {
                "type": "web_search",
                "max_keyword": 3,
                "force_search": True,
                "limit": 1,
            }
        ]
        kwargs["tool_choice"] = "auto"

    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content
```

Store the API key in a `.env` file and load with `python-dotenv`. Never hard-code it.

---

## Step 1 — GitHub Enricher

**Trigger**: runs only if `inputs/github_url.txt` exists and is non-empty.

**What to do**:
1. Extract the GitHub username from the URL
2. Call the GitHub REST API (no auth needed for public data):
   - `GET https://api.github.com/users/{username}/repos?sort=updated&per_page=30`
3. Filter repos: exclude forks, exclude repos with no description
4. Rank by a simple score: `stars × 2 + (days_since_push < 180 ? 1 : 0)`
5. Take the top 5
6. For each repo fetch `GET https://api.github.com/repos/{username}/{repo}/readme`,
   base64-decode the content, and truncate to the first 300 characters

**MIMO call** (`use_web_search=False` — data already fetched via GitHub API):

```
system: "You are helping build a resume. Summarise each GitHub repo into 1–2
resume-ready sentences in professional first-person tone. Focus on what the
project does, the tech stack, and any notable outcomes (stars, usage).
Return only a Markdown list — one bullet per repo. No preamble."

user: <raw repo metadata + README snippets>
```

**Output** — `workspace/github_summary.md`:

```markdown
---
source: github
username: <username>
generated_at: <ISO timestamp>
---

## GitHub projects

- **<repo-name>**: <1–2 sentence summary>
- **<repo-name>**: <1–2 sentence summary>
```

---

## Step 2 — Publication Enricher

**Trigger**: runs only if `inputs/publications.txt` exists and is non-empty.

**What to do**: for each URL/DOI in the file, pass it directly to MIMO with
`use_web_search=True` — let the model fetch and read the paper itself.
No manual API calls to CrossRef or arXiv needed.

**MIMO call** (`use_web_search=True`):

```
system: "You are helping build a resume. The user will give you a publication
URL or DOI. Fetch the paper and write 2–3 resume-ready sentences describing
the contribution, the problem it solves, and its significance (venue, year,
citations if available). Use professional first-person tone.
Return only a single Markdown bullet. No preamble."

user: <one URL or DOI per call>
```

Run one MIMO call per publication, then collect all bullets.

**Output** — `workspace/publications_summary.md`:

```markdown
---
source: publications
count: <N>
generated_at: <ISO timestamp>
---

## Publications

- **<Title>** (<Year>, <Venue>): <2–3 sentence summary>
- **<Title>** (<Year>, <Venue>): <2–3 sentence summary>
```

---

## Step 3 — Profile Builder (merge)

No API call needed — pure file merge.

Read the following files (skip any that do not exist):
1. `inputs/profile.md`
2. `workspace/github_summary.md`
3. `workspace/publications_summary.md`

Concatenate into a single structured document.

**Output** — `output/enriched_profile.md`:

```markdown
---
generated_at: <ISO timestamp>
sources: [profile, github, publications]   # list only sources that were present
---

## Basic info
<from profile.md>

## Work experience
<from profile.md>

## Education
<from profile.md>

## Skills
<from profile.md>

## Projects (from GitHub)
<from github_summary.md — omit section entirely if file absent>

## Publications
<from publications_summary.md — omit section entirely if file absent>
```

---

## Error Handling

- If a GitHub API call fails (rate limit, 404), log a warning and skip that repo —
  do not abort the pipeline
- If MIMO fails to retrieve a publication, write a placeholder bullet:
  `- **<original URL>**: Could not retrieve — please add manually`
- If `inputs/profile.md` is missing, exit immediately:
  `Error: inputs/profile.md is required`

---

## CLI Entry Point

```bash
python main.py
```

Reads from `inputs/`, writes to `workspace/` and `output/`.
No flags required — behaviour is driven by which input files are present.

---

## Implementation Order

1. Set up project: `pip install openai python-dotenv requests`, scaffold directories
2. Implement `call_mimo()` helper with optional `use_web_search`
3. GitHub Enricher (GitHub REST API fetch → rank → MIMO summarise)
4. Publication Enricher (one MIMO call per URL with web search enabled)
5. Profile Builder (pure merge, no API call)
6. Wire up `main.py` to run steps 3 → 4 → 5 in sequence
7. Test with a profile that has GitHub only, publications only, and both
