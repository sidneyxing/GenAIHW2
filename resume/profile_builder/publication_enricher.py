"""Step 2 - Publication Enricher.

For each URL/DOI, asks MIMO (with web search) to fetch and summarise the paper.
Writes workspace/publications_summary.md.
"""
from datetime import datetime, timezone
from pathlib import Path

from mimo_client import call_mimo

INPUT_FILE = Path("inputs/publications.txt")
OUTPUT_FILE = Path("workspace/publications_summary.md")  # used when run standalone

SYSTEM_PROMPT = (
    "You are helping build a resume. The user will give you a publication URL or DOI. "
    "Fetch the paper and respond with EXACTLY two lines, nothing else:\n"
    "TITLE: <full paper title>\n"
    "SUMMARY: <2-3 resume-ready sentences in professional first-person tone describing "
    "the contribution, the problem it solves, and its significance (venue, year, "
    "citations if available)>"
)


def _parse_structured(raw: str) -> tuple[str, str]:
    """Parse TITLE:/SUMMARY: response into (title, summary). Falls back gracefully."""
    title = summary = ""
    for line in raw.splitlines():
        if line.startswith("TITLE:"):
            title = line[len("TITLE:"):].strip()
        elif line.startswith("SUMMARY:"):
            summary = line[len("SUMMARY:"):].strip()
    if not title or not summary:
        # If the model didn't follow the format, use the whole response as summary
        raise ValueError(f"unexpected format: {raw[:120]!r}")
    return title, summary


def run(urls: list = None, output_file: Path = None) -> bool:
    """Run the publication enricher. Returns True if a summary file was written.

    Args:
        urls: List of publication URLs/DOIs. Falls back to INPUT_FILE if not given.
        output_file: Where to write the summary. Defaults to OUTPUT_FILE.
    """
    if urls is None:
        if not INPUT_FILE.exists() or not INPUT_FILE.read_text().strip():
            return False
        urls = [l.strip() for l in INPUT_FILE.read_text().splitlines() if l.strip()]

    entries = [u.strip() for u in urls if u.strip()]
    if not entries:
        return False

    out = output_file or OUTPUT_FILE
    print(f"[publications] enriching {len(entries)} publication(s)")

    bullets = []
    for entry in entries:
        print(f"  - {entry}")
        try:
            raw = call_mimo(SYSTEM_PROMPT, entry, use_web_search=True)
            raw = (raw or "").strip()
            if not raw:
                raise ValueError("empty response")
            title, summary = _parse_structured(raw)
            bullets.append(f"- **{title}** — {summary}")
        except Exception as exc:  # noqa: BLE001 - never abort the pipeline
            print(f"    warning: could not retrieve {entry}: {exc}")
            bullets.append(
                f"- **{entry}**: Could not retrieve - please add manually"
            )

    out.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    out.write_text(
        f"---\n"
        f"source: publications\n"
        f"count: {len(entries)}\n"
        f"generated_at: {generated_at}\n"
        f"---\n\n"
        f"## Publications\n\n"
        f"{chr(10).join(bullets)}\n"
    )
    print(f"[publications] wrote {out}")
    return True


if __name__ == "__main__":
    run()
