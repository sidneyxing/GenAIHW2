"""Profile Builder pipeline entry point.

Runs the enrichment steps in sequence, driven by which input files exist:
  1. GitHub Enricher       (if inputs/github_url.txt is present + non-empty)
  2. Publication Enricher  (if inputs/publications.txt is present + non-empty)
  3. Profile Builder merge  (always; requires inputs/profile.md)

Usage:
    python main.py
"""
import github_enricher
import profile_builder
import publication_enricher


def main() -> None:
    print("=== Profile Builder pipeline ===")

    if github_enricher.run():
        pass
    else:
        print("[github] skipped (no github_url.txt)")

    if publication_enricher.run():
        pass
    else:
        print("[publications] skipped (no publications.txt)")

    profile_builder.run()
    print("=== Done ===")


if __name__ == "__main__":
    main()
