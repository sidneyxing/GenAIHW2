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
OUTPUT_FILE = Path("output/enriched_profile.md")  # used when run standalone


def _strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block, if present."""
    text = text.lstrip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].lstrip()
    return text


def run(
    profile_content: str = None,
    github_file: Path = None,
    publications_file: Path = None,
    output_file: Path = None,
) -> None:
    """Merge profile + enrichment files into enriched_profile.md.

    Args:
        profile_content: Raw profile text. Falls back to PROFILE_FILE if not given.
        github_file: Path to github_summary.md. Defaults to GITHUB_FILE.
        publications_file: Path to publications_summary.md. Defaults to PUBLICATIONS_FILE.
        output_file: Where to write the merged result. Defaults to OUTPUT_FILE.
    """
    if profile_content is None:
        if not PROFILE_FILE.exists():
            sys.exit("Error: inputs/profile.md is required")
        profile_content = PROFILE_FILE.read_text()

    gh_file = github_file or GITHUB_FILE
    pub_file = publications_file or PUBLICATIONS_FILE
    out = output_file or OUTPUT_FILE

    sources = ["profile"]
    sections = [_strip_frontmatter(profile_content).strip()]

    if gh_file.exists():
        sources.append("github")
        sections.append(_strip_frontmatter(gh_file.read_text()).strip())

    if pub_file.exists():
        sources.append("publications")
        sections.append(_strip_frontmatter(pub_file.read_text()).strip())

    out.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    body = "\n\n".join(s for s in sections if s)
    out.write_text(
        f"---\n"
        f"generated_at: {generated_at}\n"
        f"sources: [{', '.join(sources)}]\n"
        f"---\n\n"
        f"{body}\n"
    )
    print(f"[merge] wrote {out} (sources: {', '.join(sources)})")


if __name__ == "__main__":
    run()
