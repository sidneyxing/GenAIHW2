import json
import re
from typing import Any, Dict, List, Optional

from mimo_client import call_mimo


def extract_json(raw_response: str) -> Dict[str, Any]:
    """
    Extract the first valid JSON object from an LLM response.
    This is useful because sometimes the model returns ```json blocks.
    """
    text = re.sub(r"```(?:json)?", "", raw_response).replace("```", "").strip()

    start = text.find("{")
    if start == -1:
        return {
            "success": False,
            "error": "no JSON found",
            "data": None,
        }

    depth = 0
    json_str = None

    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                json_str = text[start : i + 1]
                break

    if not json_str:
        return {
            "success": False,
            "error": "unbalanced JSON braces",
            "data": None,
        }

    try:
        return {
            "success": True,
            "error": None,
            "data": json.loads(json_str),
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON decode error: {e}",
            "data": None,
        }


def generate_interview_questions(
    resume_summary: str,
    skills: List[str],
    target_job: str,
    job_description: Optional[str] = None,
    question_count: int = 5,
) -> Dict[str, Any]:
    """
    Interviewer Agent - Question Generator

    Input:
    - resume_summary: candidate resume summary from resume agent
    - skills: candidate skills from skill scanner / resume agent
    - target_job: job selected or typed by user
    - job_description: optional job detail from recommendation system

    Output:
    - job_title
    - job_field
    - candidate_level
    - interview_focus
    - questions
    """

    system_prompt = """
You are an AI Interviewer Agent in a multi-agent job recommendation website.

Your main role is to simulate a professional interviewer for any job position typed by the user.

You will receive:
1. candidate resume summary
2. candidate skills
3. target job typed freely by the user
4. optional job description

Your tasks:
1. Understand the target job, even if the user types it freely.
2. Classify the job field automatically.
3. Estimate the candidate level based on resume and skills.
4. Generate interview questions suitable for that job field.
5. Make the questions relevant to the candidate's skills and target job.
6. Ask realistic questions like a real interviewer.

Question design rules:
- Include different question types: technical, project_experience, problem_solving, behavioral, follow_up.
- If the target job is technical, ask skill-based technical questions.
- If the target job is non-technical, ask domain-related practical questions.
- If the candidate skill is not enough, ask beginner-level questions.
- Do not ask random or unrelated questions.
- Use simple, clear, and professional English.
- Return valid JSON only. Do not include markdown.

JSON schema:
{
  "job_title": "",
  "job_field": "",
  "candidate_level": "Beginner | Intermediate | Advanced",
  "interview_focus": ["", ""],
  "questions": [
    {
      "type": "technical | project_experience | problem_solving | behavioral | follow_up",
      "difficulty": "beginner | intermediate | advanced",
      "question": ""
    }
  ]
}
"""

    user_prompt = f"""
Candidate resume summary:
{resume_summary or "Not provided"}

Candidate skills:
{json.dumps(skills or [], ensure_ascii=False)}

Target job typed by user:
{target_job}

Job description:
{job_description or "Not provided"}

Please generate exactly {question_count} interview questions.
"""

    raw_response = call_mimo(
        system_prompt=system_prompt,
        user_content=user_prompt,
        use_web_search=False,
    )

    result = extract_json(raw_response)

    if not result["success"]:
        return {
            "success": False,
            "error": result["error"],
            "data": None,
        }

    return {
        "success": True,
        "error": None,
        "data": result["data"],
    }


def evaluate_interview_answer(
    target_job: str,
    question: str,
    answer: str,
    resume_summary: Optional[str] = None,
    skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Interviewer Agent - Answer Evaluator

    Input:
    - target_job
    - question
    - candidate answer

    Output:
    - score
    - feedback
    - strengths
    - weaknesses
    - better_answer
    - follow_up_question
    """

    system_prompt = """
You are an AI Interviewer Agent and interview evaluator.

Your task is to evaluate a candidate's interview answer based on the target job and question.

Evaluation rules:
- Score from 1 to 10.
- Be fair and professional.
- Explain strengths and weaknesses clearly.
- Provide a better answer example.
- Ask one follow-up question based on the candidate's answer.
- Use simple, clear, and professional English.
- Return valid JSON only. Do not include markdown.

JSON schema:
{
  "score": 0,
  "feedback": "",
  "strengths": ["", ""],
  "weaknesses": ["", ""],
  "better_answer": "",
  "follow_up_question": ""
}
"""

    user_prompt = f"""
Target job:
{target_job}

Candidate resume summary:
{resume_summary or "Not provided"}

Candidate skills:
{json.dumps(skills or [], ensure_ascii=False)}

Interview question:
{question}

Candidate answer:
{answer}
"""

    raw_response = call_mimo(
        system_prompt=system_prompt,
        user_content=user_prompt,
        use_web_search=False,
    )

    result = extract_json(raw_response)

    if not result["success"]:
        return {
            "success": False,
            "error": result["error"],
            "data": None,
        }

    data = result["data"]

    try:
        score = float(data.get("score", 0))
        data["score"] = max(1.0, min(10.0, round(score, 1)))
    except (TypeError, ValueError):
        data["score"] = 0

    return {
        "success": True,
        "error": None,
        "data": data,
    }


def aggregate_interview_result(
    target_job: str,
    evaluated_answers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Interviewer Agent - Overall Interview Result Aggregator

    Input:
    - target_job: the job the candidate is applying for
    - evaluated_answers: list of evaluate_interview_answer results
      Each item should have: question, answer, score, feedback,
      strengths, weaknesses, better_answer, follow_up_question

    Output:
    - total_questions
    - average_score
    - overall_level: "Poor" | "Fair" | "Good" | "Excellent"
    - summary: short paragraph
    - strong_areas: list
    - weak_areas: list
    - recommendation: "Recommended" | "Maybe" | "Not Recommended"
    """

    if not evaluated_answers:
        return {
            "success": False,
            "error": "no evaluated answers provided",
            "data": None,
        }

    scores = []
    qa_pairs = []

    for item in evaluated_answers:
        try:
            score = float(item.get("score", 0))
            scores.append(score)
            qa_pairs.append({
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "score": score,
                "strengths": item.get("strengths", []),
                "weaknesses": item.get("weaknesses", []),
            })
        except (TypeError, ValueError):
            continue

    if not scores:
        return {
            "success": False,
            "error": "no valid scores found",
            "data": None,
        }

    average_score = round(sum(scores) / len(scores), 1)

    if average_score >= 8.5:
        overall_level = "Excellent"
        recommendation = "Recommended"
    elif average_score >= 6.5:
        overall_level = "Good"
        recommendation = "Recommended"
    elif average_score >= 4.5:
        overall_level = "Fair"
        recommendation = "Maybe"
    else:
        overall_level = "Poor"
        recommendation = "Not Recommended"

    system_prompt = """
You are an AI interview evaluator writing a final interview summary.

You will receive:
1. The target job
2. A list of Q&A pairs with individual scores, strengths, and weaknesses

Your tasks:
1. Write a short summary paragraph (2-3 sentences) about the candidate's overall interview performance.
2. List 2-3 strong areas observed across all answers.
3. List 2-3 weak areas observed across all answers.

Return valid JSON only. Do not include markdown.

JSON schema:
{
  "summary": "",
  "strong_areas": ["", ""],
  "weak_areas": ["", ""]
}
"""

    user_prompt = f"""
Target job: {target_job}

Interview Q&A results:
{json.dumps(qa_pairs, ensure_ascii=False, indent=2)}
"""

    raw_response = call_mimo(
        system_prompt=system_prompt,
        user_content=user_prompt,
        use_web_search=False,
    )

    result = extract_json(raw_response)

    if not result["success"]:
        # fallback: return numeric results without LLM summary
        return {
            "success": True,
            "error": None,
            "data": {
                "total_questions": len(scores),
                "average_score": average_score,
                "overall_level": overall_level,
                "recommendation": recommendation,
                "summary": "Summary not available.",
                "strong_areas": [],
                "weak_areas": [],
            },
        }

    llm_data = result["data"]

    return {
        "success": True,
        "error": None,
        "data": {
            "total_questions": len(scores),
            "average_score": average_score,
            "overall_level": overall_level,
            "recommendation": recommendation,
            "summary": llm_data.get("summary", ""),
            "strong_areas": llm_data.get("strong_areas", []),
            "weak_areas": llm_data.get("weak_areas", []),
        },
    }