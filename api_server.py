"""
api_server.py
FastAPI wrapper for GenAIHW2 backend modules.

Run from the project root:
    pip install fastapi uvicorn python-dotenv openai beautifulsoup4 lxml selenium
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

Required .env:
    MIMO_API_KEY=your_key_here

Frontend:
    CONFIG.API_BASE_URL = 'http://localhost:8000'
    CONFIG.USE_API = true
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent

env_paths = [
    ROOT / ".env",
    ROOT / "resume" / ".env",
    ROOT / "resume" / "profile_reviwer" / ".env",
    ROOT / "resume" / "profile_reviewer" / ".env",
]

print("ROOT =", ROOT)

for env_path in env_paths:
    print("CHECK ENV:", env_path, "EXISTS:", env_path.exists())
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print("LOADED ENV:", env_path)

print("MIMO_API_KEY =", "FOUND" if os.getenv("MIMO_API_KEY") else "NOT FOUND")

# Make local folders importable even when modules use non-package imports.
for p in [
    ROOT,
    ROOT / "recommendation_system",
    ROOT / "Interviewer_Agent",
    ROOT / "resume" / "profile_reviwer",
    ROOT / "resume" / "profile_reviewer",
]:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

app = FastAPI(title="GenAIHW2 AI Career API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    user_experience_input: Optional[str] = None
    user_needs_input: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    workExperience: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[str] = None
    github: Optional[str] = None
    publications: Optional[str] = None
    needs: Optional[str] = None


class ResumeRequest(RecommendRequest):
    job: Dict[str, Any]
    max_iter: int = Field(default=2, ge=1, le=5)
    pass_score: int = Field(default=85, ge=1, le=100)


class QuestionsRequest(BaseModel):
    job: Dict[str, Any]
    profile: str = ""
    skills: List[str] = Field(default_factory=list)
    question_count: int = Field(default=5, ge=1, le=10)


class EvaluateRequest(BaseModel):
    job: Dict[str, Any]
    profile: str = ""
    skills: List[str] = Field(default_factory=list)
    question: str
    answer: str


class SummaryRequest(BaseModel):
    job: Dict[str, Any]
    evaluated_answers: List[Dict[str, Any]] = Field(default_factory=list)


def _profile_content(data: RecommendRequest) -> str:
    if data.user_experience_input:
        return data.user_experience_input

    return f"""
## Basic info

Name: {data.name or ''}
Email: {data.email or ''}
Location: {data.location or ''}

## Work experience

{data.workExperience or ''}

## Education

{data.education or ''}

## Skills

{data.skills or ''}

## GitHub

{data.github or ''}

## Publications

{data.publications or ''}
""".strip()


def _needs(data: RecommendRequest) -> str:
    return data.user_needs_input or data.needs or ""


def _job_title(job: Dict[str, Any]) -> str:
    return job.get("job_title") or job.get("title") or job.get("jobTitle") or "Selected Job"


def _job_description(job: Dict[str, Any]) -> str:
    return json.dumps(job, ensure_ascii=False, indent=2)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "success": True,
        "message": "GenAIHW2 API server is running",
        "mimo_key_loaded": bool(os.environ.get("MIMO_API_KEY")),
    }


@app.post("/recommend")
def recommend(req: RecommendRequest) -> Dict[str, Any]:
    try:
        from recommendation_system.job_keyword import generate_job_keywords
        from recommendation_system.crawler import run_batch_crawler
        from recommendation_system.reranker import rerank_jobs

        profile = _profile_content(req)
        needs = _needs(req)

        keywords = generate_job_keywords(user_experience=profile, user_needs=needs)
        jobs = run_batch_crawler(keywords)

        user_profile = f"""
工作經歷：
{profile}

求職需求：
{needs}
"""
        ranked_jobs = rerank_jobs(user_profile=user_profile, jobs=jobs)

        return {
            "success": True,
            "error": None,
            "keywords": keywords,
            "rankedJobs": ranked_jobs,
            "data": ranked_jobs,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {exc}") from exc


@app.post("/resume")
def resume(req: ResumeRequest) -> Dict[str, Any]:
    """
    Generate a resume in realtime.

    This endpoint uses the existing ResumePipeline when available. It writes the
    user profile to a temporary file and lets the resume reviewer pipeline produce
    Markdown output tailored to the selected job.
    """
    try:
        try:
            from resume.profile_reviwer.profile_reviwer import ResumePipeline
        except Exception:
            from profile_reviwer import ResumePipeline  # fallback if run from that folder

        profile = _profile_content(req)

        with tempfile.TemporaryDirectory(prefix="genaihw2_resume_") as tmpdir:
            tmp = Path(tmpdir)
            input_file = tmp / "enriched_profile.md"
            output_file = tmp / "resume_final.md"
            workspace = tmp / "workspace"
            input_file.write_text(profile, encoding="utf-8")

            pipeline = ResumePipeline(
                input_filepath=str(input_file),
                output_filepath=str(output_file),
                workspace_dir=str(workspace),
                job=req.job,
            )
            pipeline.execute(max_iterations=req.max_iter, pass_score=req.pass_score)

            resume_text = output_file.read_text(encoding="utf-8") if output_file.exists() else ""

        return {
            "success": True,
            "error": None,
            "resumeFinal": resume_text,
            "data": resume_text,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {exc}") from exc


@app.post("/interview/questions")
def interview_questions(req: QuestionsRequest) -> Dict[str, Any]:
    try:
        from Interviewer_Agent.interviewer_agent import generate_interview_questions

        result = generate_interview_questions(
            resume_summary=req.profile,
            skills=req.skills,
            target_job=_job_title(req.job),
            job_description=_job_description(req.job),
            question_count=req.question_count,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {exc}") from exc


@app.post("/interview/evaluate")
def interview_evaluate(req: EvaluateRequest) -> Dict[str, Any]:
    try:
        from Interviewer_Agent.interviewer_agent import evaluate_interview_answer

        result = evaluate_interview_answer(
            target_job=_job_title(req.job),
            question=req.question,
            answer=req.answer,
            resume_summary=req.profile,
            skills=req.skills,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Answer evaluation failed: {exc}") from exc


@app.post("/interview/summary")
def interview_summary(req: SummaryRequest) -> Dict[str, Any]:
    try:
        from Interviewer_Agent.interviewer_agent import aggregate_interview_result

        result = aggregate_interview_result(
            target_job=_job_title(req.job),
            evaluated_answers=req.evaluated_answers,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {exc}") from exc
