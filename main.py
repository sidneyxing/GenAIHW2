import os
import json
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "resume" / ".env")



# ============ STAGE1 INPUT ============
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

user_needs_input = (
    "Looking for a job in Taipei."
    "Hoping for a salary of NT$40,000 or more."
)

# ============ STAGE2 INPUT ============
pick = 0  # the job user pick

# ============ STAGE3 INPUT ============
# The program will use `input()` to dynamically prompt the user for input (user_answer).


# ============ RESUME FUNCTION ============
RESUME = Path(__file__).parent / "resume"
BUILDER_DIR = RESUME / "profile_builder"
REVIEWER_DIR = RESUME / "profile_reviwer"
BUILDER_OUTPUT = BUILDER_DIR / "output" / "enriched_profile.md"
BUILDER_WORKSPACE = BUILDER_DIR / "workspace"
REVIEWER_INPUT = REVIEWER_DIR / "input" / "enriched_profile.md"
REVIEWER_OUTPUT = REVIEWER_DIR / "output" / "resume_final.md"
FINAL_OUTPUT = RESUME / "resume_final.md"

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


def _run_builder(PROFILE_CONTENT: str) -> None:
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



# ============ Interviewer_Agent FUNCTION ============
from Interviewer_Agent.interviewer_agent import generate_interview_questions, evaluate_interview_answer, aggregate_interview_result

def load_file_content(file_path: str) -> str:
    """讀取檔案內容的轉接器"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"⚠️ 找不到檔案: {file_path}")
        return ""

def load_json_content(file_path: str):
    """讀取 JSON 檔案的轉接器"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"⚠️ 找不到 JSON 檔案: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"⚠️ JSON 格式錯誤: {file_path}")
        return None



def main():
    # ===============================================
    # ============ recommendation_system ============
    # ===============================================
    from recommendation_system.job_keyword import generate_job_keywords
    from recommendation_system.crawler import run_batch_crawler
    from recommendation_system.reranker import rerank_jobs

    PROFILE_CONTENT = f"""
## Basic info

Name: {Name}
Email: {Email}
Location: {Location}

## Work experience

{Work_experience}

## Education

{Education}

## Skills

{Skills}
"""

    target_job_keywords = generate_job_keywords(
        user_experience=PROFILE_CONTENT,
        user_needs=user_needs_input
    )

    final_job_list = run_batch_crawler(
        target_job_keywords
    )

    user_profile = f"""
工作經歷：
{PROFILE_CONTENT}

求職需求：
{user_needs_input}
"""

    ranked_jobs = rerank_jobs(
        user_profile=user_profile,
        jobs=final_job_list
    )

    FIELD_NAMES = {
        "job_title": "職缺名稱",
        "company_name": "公司",
        "location": "工作地點",
        "salary": "薪資",
        "education": "學歷要求",
        "experience": "經驗要求",
        "description": "工作內容",
        "link": "職缺連結",
        "verdict": "評語",
    }

    exclude_fields = {"id", "score"}

    # OUTPUT
    for job in ranked_jobs:
        print(f"# {job['job_title']}")
        print()

        for key, value in job.items():
            if key not in exclude_fields:
                title = FIELD_NAMES.get(key, key)
                print(f"## {title}")
                print(value)
                print()

    # ===============================================
    # =================== resume ====================
    # ===============================================
    TARGET_JOB = ranked_jobs[pick]

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
        _run_builder(PROFILE_CONTENT)
        if not BUILDER_OUTPUT.exists():
            sys.exit(f"[ERROR] Expected output not found: {BUILDER_OUTPUT}")

    # ── Handoff: copy enriched profile to reviewer input ─────────────────────
    REVIEWER_INPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BUILDER_OUTPUT, REVIEWER_INPUT)
    print(f"\n[handoff] {BUILDER_OUTPUT.relative_to(RESUME)}  →  {REVIEWER_INPUT.relative_to(RESUME)}")

    # ── Part 2: Resume Optimizer ──────────────────────────────────────────────
    _run_reviewer(
        "Part 2 — Resume Optimizer",
        extra_args=["--max-iter", str(args.max_iter), "--pass-score", str(args.pass_score)],
        job=TARGET_JOB,
    )

    _banner("Pipeline Complete")
    if REVIEWER_OUTPUT.exists():
        shutil.copy2(REVIEWER_OUTPUT, FINAL_OUTPUT)
        print(f"  Final resume → {FINAL_OUTPUT.relative_to(RESUME)}")
    else:
        print(f"  [WARNING] Expected output not found: {REVIEWER_OUTPUT}")

    # ===============================================
    # ============== Interviewer_Agent ==============
    # ===============================================
    print("啟動面試模擬 Agent...")
    
    # 1. 設定檔案路徑 (相對於專案根目錄 GenAIHW2)
    # 注意：這裡使用會議中提到的路徑
    resume_path = "resume/profile_reviwer/workspace/resume_final.md"

    # 2. 讀取實體履歷檔案
    print(f"正在讀取履歷: {resume_path}")
    resume_content = load_file_content(resume_path)
    if not resume_content:
        resume_content = "Software Engineer with Python and Docker experience." # 防呆預設值

    # 3. 讀取實體職缺檔案
    target_job_title = "未指定職缺"
    job_desc = "未提供詳細說明"
    
    target_job_title = TARGET_JOB.get("title", TARGET_JOB.get("job_title", "Software Engineer"))
    job_desc = json.dumps(TARGET_JOB, ensure_ascii=False) 
    
    # 4. 執行核心邏輯：呼叫 Agent 生成面試題
    print(f"\n✅ 資料載入完成！目標職缺: {target_job_title}")
    print("⏳ 正在根據履歷與職缺生成專屬面試題...\n")
    
    result = generate_interview_questions(
        resume_summary=resume_content,
        skills=[], # 因為履歷字串已經包含全部資訊，所以技能清單給空陣列讓模型自己抓
        target_job=target_job_title,
        job_description=job_desc
    )

    # === 面試題目生成結果 ===
    print("=== 面試題目生成結果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 5. 將產出的面試題存成實體檔案，完美對接後端
    output_filename = "Interviewer_Agent/interview_questions.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 面試題目已成功儲存至 {output_filename}！")

    # 6. 進行完整的 5 題互動面試與評分
    if result["success"] and result["data"]["questions"]:
        print("\n" + "="*40)
        print("💡 進入【完整面試實戰】階段 (共 5 題)")
        print("="*40)
        
        chat_history = []
        questions_list = result["data"]["questions"]
        last_eval_result = None
        
        # 使用 for 迴圈，把 5 題一題一題抓出來問
        for i, q_data in enumerate(questions_list, 1):
            question_text = q_data["question"]
            print(f"\n🤖 第 {i} 題 ({q_data['type']} / 難度: {q_data['difficulty']}):")
            print(f"面試官提問: {question_text}")
            
            # 使用 input() 讓你可以直接在終端機打字回答！
            user_answer = input("👤 你的回答 (輸入完按 Enter): ")
            
            print("⏳ 正在評估你的回答...")
            eval_result = evaluate_interview_answer(
                target_job=target_job_title,
                question=question_text,
                answer=user_answer,
                resume_summary=resume_content,
                skills=[]
            )
            last_eval_result = eval_result
            
            # 印出單題評分讓你知道剛剛答得怎樣
            evaluation_data = eval_result.get("data", {})
            print(f"👉 系統評分: {evaluation_data.get('score', 0)} / 10")
            print(f"👉 建議: {evaluation_data.get('feedback', '')}\n")
            
            # 將每一題的問答與評分記錄存進陣列
            chat_history.append({
                "question": question_text, 
                "answer": user_answer, 
                "score": evaluation_data.get("score", 0),
                "strengths": evaluation_data.get("strengths", []),
                "weaknesses": evaluation_data.get("weaknesses", [])
            })
            
        # 將最後一題的評估結果存成檔案 (前端示意用)
        if last_eval_result:
            eval_filename = "Interviewer_Agent/evaluation_result.json"
            with open(eval_filename, "w", encoding="utf-8") as f:
                json.dump(last_eval_result, f, ensure_ascii=False, indent=2)
            print(f"✅ 單題評分結果已儲存至 {eval_filename}")

        # 7. 模擬面試結束，產生最終總結 (Final Summary)
        print("\n" + "="*40)
        print("📊 面試結束！正在產出最終總結報告...")
        print("="*40)
        
        final_summary = aggregate_interview_result(
            target_job=target_job_title,
            evaluated_answers=chat_history
        )
        
        print("\n=== Final Interview Summary (最終面試總結) ===")
        print(json.dumps(final_summary, ensure_ascii=False, indent=2))
        
        final_filename = "Interviewer_Agent/final_summary.json"
        with open(final_filename, "w", encoding="utf-8") as f:
            json.dump(final_summary, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 最終總結已成功儲存至 {final_filename}！")


if __name__ == "__main__":
    main()