"""Step 1 - GitHub Enricher.

Fetches a user's public repos, ranks them, pulls README snippets, and asks MIMO
to turn them into resume-ready bullets. Writes workspace/github_summary.md.
"""
import base64
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

from mimo_client import call_mimo

GITHUB_API = "https://api.github.com"
INPUT_FILE = Path("inputs/github_url.txt")
OUTPUT_FILE = Path("workspace/github_summary.md")  # used when run standalone

SYSTEM_PROMPT = (
    "You are helping build a resume. Summarise each GitHub repo into 1-2 "
    "resume-ready sentences in professional first-person tone. Focus on what the "
    "project does, the tech stack, and any notable outcomes (stars, usage). "
    "Each bullet must start with the repo name in bold, e.g. **repo-name** — then the description. "
    "Return only a Markdown list - one bullet per repo. No preamble."
)


def _extract_username(url: str) -> str:
    """Pull the username out of a GitHub profile URL or bare handle."""
    url = url.strip().rstrip("/")
    match = re.search(r"github\.com/([^/]+)", url)
    if match:
        return match.group(1)
    # Fall back to treating the whole line as a bare username.
    return url.split("/")[-1]


def _days_since(iso_ts: str) -> float:
    pushed = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - pushed).total_seconds() / 86400


def _fetch_readme_snippet(username: str, repo: str) -> str:
    try:
        resp = requests.get(
            f"{GITHUB_API}/repos/{username}/{repo}/readme", timeout=20
        )
        if resp.status_code != 200:
            print(f"  warning: README fetch failed for {repo} ({resp.status_code})")
            return ""
        content = resp.json().get("content", "")
        decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        return decoded[:300]
    except (requests.RequestException, ValueError) as exc:
        print(f"  warning: README fetch error for {repo}: {exc}")
        return ""


def run(github_url: str = None, output_file: Path = None) -> bool:
    """Run the GitHub enricher. Returns True if a summary file was written.

    Args:
        github_url: GitHub profile URL. Falls back to INPUT_FILE if not given.
        output_file: Where to write the summary. Defaults to OUTPUT_FILE.
    """
    if github_url is None:
        if not INPUT_FILE.exists() or not INPUT_FILE.read_text().strip():
            return False
        github_url = INPUT_FILE.read_text().strip().splitlines()[0]

    if not github_url.strip():
        return False

    out = output_file or OUTPUT_FILE
    url = github_url.strip()
    username = _extract_username(url)
    print(f"[github] enriching profile for: {username}")

    try:
        resp = requests.get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"sort": "updated", "per_page": 30},
            timeout=20,
        )
        resp.raise_for_status()
        repos = resp.json()
    except requests.RequestException as exc:
        print(f"  warning: could not list repos for {username}: {exc} - skipping")
        return False

    candidates = [
        r for r in repos if not r.get("fork") and (r.get("description") or "").strip()
    ]

    def score(r):
        recent = 1 if _days_since(r["pushed_at"]) < 180 else 0
        return r.get("stargazers_count", 0) * 2 + recent

    candidates.sort(key=score, reverse=True)
    top = candidates[:5]

    if not top:
        print("  warning: no qualifying repos found - skipping GitHub enrichment")
        return False

    blocks = []
    for r in top:
        snippet = _fetch_readme_snippet(username, r["name"])
        blocks.append(
            f"Repo: {r['name']}\n"
            f"Description: {r.get('description', '')}\n"
            f"Language: {r.get('language', 'n/a')}\n"
            f"Stars: {r.get('stargazers_count', 0)}\n"
            f"URL: {r.get('html_url', '')}\n"
            f"README snippet: {snippet}\n"
        )

    user_content = "\n---\n".join(blocks)
    summary = call_mimo(SYSTEM_PROMPT, user_content, use_web_search=False)

    out.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    out.write_text(
        f"---\n"
        f"source: github\n"
        f"username: {username}\n"
        f"generated_at: {generated_at}\n"
        f"---\n\n"
        f"## GitHub projects\n\n"
        f"{summary.strip()}\n"
    )
    print(f"[github] wrote {out}")
    return True


if __name__ == "__main__":
    run()
