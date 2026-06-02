"""Step 3 - Profile Builder (merge).

Pure file merge: combines inputs/profile.md with the workspace enrichment
summaries into output/enriched_profile.md. No API calls.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

PROFILE_FILE = Path("inputs/profile.md")
GITHUB_FILE = Path("workspace/github_summary.md")
PUBLICATIONS_FILE = Path("workspace/publications_summary.md")
OUTPUT_FILE = Path("output/enriched_profile.md")


def _strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block, if present."""
    text = text.lstrip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].lstrip()
    return text


def run() -> None:
    if not PROFILE_FILE.exists():
        sys.exit("Error: inputs/profile.md is required")

    sources = ["profile"]
    sections = [_strip_frontmatter(PROFILE_FILE.read_text()).strip()]

    if GITHUB_FILE.exists():
        sources.append("github")
        sections.append(_strip_frontmatter(GITHUB_FILE.read_text()).strip())

    if PUBLICATIONS_FILE.exists():
        sources.append("publications")
        sections.append(_strip_frontmatter(PUBLICATIONS_FILE.read_text()).strip())

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    body = "\n\n".join(s for s in sections if s)
    OUTPUT_FILE.write_text(
        f"---\n"
        f"generated_at: {generated_at}\n"
        f"sources: [{', '.join(sources)}]\n"
        f"---\n\n"
        f"{body}\n"
    )
    print(f"[merge] wrote {OUTPUT_FILE} (sources: {', '.join(sources)})")


if __name__ == "__main__":
    run()
