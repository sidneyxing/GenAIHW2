"""End-to-end resume pipeline.

Part 1 – Profile Builder  (profile_builder/)
    Enriches the raw profile with GitHub and publication data, writing
    profile_builder/output/enriched_profile.md.

Part 2 – Resume Optimizer (profile_reviwer/)
    Actor-critic loop that drafts and refines a polished resume, writing
    profile_reviwer/output/resume_final.md.

Usage:
    python main.py
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).parent
BUILDER_DIR = BASE / "profile_builder"
REVIEWER_DIR = BASE / "profile_reviwer"

# ── User Inputs ───────────────────────────────────────────────────────────────

Name = "Jane Doe"
Email = "jane.doe@example.com"
Location = "San Francisco, CA"
Work_experience = """\
**Senior Backend Engineer**, Acme Corp (2021–present)
Designed and scaled distributed services handling 2M+ requests/day. Led migration
to event-driven architecture, cutting p99 latency by 40%.

**Software Engineer**, Startup Inc (2018–2021)
Built the core REST API and CI/CD pipeline from scratch."""
Education = "B.S. Computer Science, University of California, Berkeley (2018)"
Skills = "Python, Go, PostgreSQL, Kubernetes, AWS, distributed systems, REST APIs"

GITHUB_URL = "https://github.com/tiangolo"  # set to "" to skip GitHub enrichment

PUBLICATION_URLS = [
    "https://arxiv.org/abs/1706.03762",
    "https://arxiv.org/abs/2507.06448",
]  # set to [] to skip publication enrichment

# Target job from the recommendation system (set to None to skip job-tailoring)
TARGET_JOB = {
    "id": 2,
    "job_title": "I105PythonWeb工程師(可遠端工作)",
    "company_name": "台灣大哥大股份有限公司",
    "location": "台北市大安區",
    "salary": "面議（經常性薪資達4萬元或以上）",
    "education": "資訊缺失",
    "experience": "經驗不拘",
    "description": "【工作內容】\n1.PythonWeb Application開發(Flask + jQuery單體架構 或 FastAPI + ReactJS前後端分離) \n2. 網路爬蟲程式開發\n3. 無限可能的多元領域 : 科技新創服務 / 加值服務 / 通路營運 / 虛擬通路 / 企業創新服務\n\n【必備技能】\n1.PythonWeb開發能力(Flask or FastAPI尤佳，Django經驗也可)\n2. 有開發前端經驗如jQuery或JS等經驗\n3. 網路爬蟲程式開發\n\n【加分條件】\n1. ReactJS 經驗尤佳\n2. GCP/ AWS / K8S 經驗尤佳\n3. Java  Web Application開發經驗尤佳\n4. 具備英文聽/說/讀/寫基本能力，有多益(TOEIC)聽讀550分以上尤佳",
    "link": "https://www.1111.com.tw/job/130373408",
    "score": 8.0,
    "verdict": "穩定環境與學習機會，適合進一步發展。",
}


















# ── Paths ─────────────────────────────────────────────────────────────────────
PROFILE_CONTENT = f"""
## Basic info

{Name} — Software Engineer
Email: {Email}
Location: {Location}

## Work experience

{Work_experience}

## Education

{Education}

## Skills

{Skills}
"""


BUILDER_OUTPUT = BUILDER_DIR / "output" / "enriched_profile.md"
BUILDER_WORKSPACE = BUILDER_DIR / "workspace"
REVIEWER_INPUT = REVIEWER_DIR / "input" / "enriched_profile.md"
REVIEWER_OUTPUT = REVIEWER_DIR / "output" / "resume_final.md"
FINAL_OUTPUT = BASE / "resume_final.md"


def _banner(title: str) -> None:
    bar = "=" * 60
    print(f"\n{bar}\n  {title}\n{bar}")


def _run_reviewer(label: str, extra_args: list[str] = (), job: dict = None) -> None:
    _banner(label)
    cmd = [sys.executable, "profile_reviwer.py"] + list(extra_args)
    tmp_job_file = None
    try:
        if job:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            )
            json.dump(job, tmp)
            tmp.close()
            tmp_job_file = tmp.name
            cmd += ["--job-file", tmp_job_file]
        subprocess.run(cmd, cwd=REVIEWER_DIR, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"\n[ERROR] {label} failed (exit {exc.returncode}). Aborting.")
        sys.exit(exc.returncode)
    finally:
        if tmp_job_file and os.path.exists(tmp_job_file):
            os.unlink(tmp_job_file)


def _run_builder() -> None:
    """Run Part 1 inline: import builder modules and call them with the variables above."""
    _banner("Part 1 — Profile Builder")

    # Add profile_builder/ to path so its local imports (mimo_client etc.) resolve.
    sys.path.insert(0, str(BUILDER_DIR))
    try:
        import github_enricher
        import profile_builder
        import publication_enricher

        gh_out = BUILDER_WORKSPACE / "github_summary.md"
        pub_out = BUILDER_WORKSPACE / "publications_summary.md"

        if github_enricher.run(github_url=GITHUB_URL, output_file=gh_out):
            pass
        else:
            print("[github] skipped (GITHUB_URL is empty)")

        if publication_enricher.run(urls=PUBLICATION_URLS, output_file=pub_out):
            pass
        else:
            print("[publications] skipped (PUBLICATION_URLS is empty)")

        profile_builder.run(
            profile_content=PROFILE_CONTENT,
            github_file=gh_out,
            publications_file=pub_out,
            output_file=BUILDER_OUTPUT,
        )
    finally:
        sys.path.pop(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Full resume pipeline")
    parser.add_argument(
        "--skip-builder",
        action="store_true",
        help="Skip Part 1 and use the existing enriched_profile.md",
    )
    parser.add_argument("--max-iter", type=int, default=3, help="Reviewer iterations (default 3)")
    parser.add_argument("--pass-score", type=int, default=85, help="Target score to stop early (default 85)")
    args = parser.parse_args()

    load_dotenv(BUILDER_DIR / ".env")
    if not os.environ.get("MIMO_API_KEY"):
        sys.exit("[ERROR] MIMO_API_KEY not set — add it to profile_builder/.env")

    _banner("Resume Pipeline — Start")

    # ── Part 1: Profile Builder ───────────────────────────────────────────────
    if args.skip_builder:
        print("\n[skip] Part 1 skipped by --skip-builder flag.")
        if not BUILDER_OUTPUT.exists():
            sys.exit(
                f"[ERROR] --skip-builder requires {BUILDER_OUTPUT} to exist. "
                "Run without the flag first."
            )
    else:
        _run_builder()
        if not BUILDER_OUTPUT.exists():
            sys.exit(f"[ERROR] Expected output not found: {BUILDER_OUTPUT}")

    # ── Handoff: copy enriched profile to reviewer input ─────────────────────
    REVIEWER_INPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BUILDER_OUTPUT, REVIEWER_INPUT)
    print(f"\n[handoff] {BUILDER_OUTPUT.relative_to(BASE)}  →  {REVIEWER_INPUT.relative_to(BASE)}")

    # ── Part 2: Resume Optimizer ──────────────────────────────────────────────
    _run_reviewer(
        "Part 2 — Resume Optimizer",
        extra_args=["--max-iter", str(args.max_iter), "--pass-score", str(args.pass_score)],
        job=TARGET_JOB,
    )

    _banner("Pipeline Complete")
    if REVIEWER_OUTPUT.exists():
        shutil.copy2(REVIEWER_OUTPUT, FINAL_OUTPUT)
        print(f"  Final resume → {FINAL_OUTPUT.relative_to(BASE)}")
    else:
        print(f"  [WARNING] Expected output not found: {REVIEWER_OUTPUT}")


if __name__ == "__main__":
    main()
