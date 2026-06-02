import json
from interviewer_agent import generate_interview_questions, evaluate_interview_answer


# Replace this with your real API key or set it in environment variable.
# Ensure MIMO_API_KEY is configured before running tests.
# Example:
# export MIMO_API_KEY=your_key

resume_summary = "Computer science student with experience in Python, SQL, and machine learning projects."
skills = ["Python", "SQL", "Machine Learning"]
target_job = "Data Analyst Intern"
job_description = "Analyze data, clean datasets, create reports, and support business decision making."

questions_result = generate_interview_questions(
    resume_summary=resume_summary,
    skills=skills,
    target_job=target_job,
    job_description=job_description,
)

print("=== Generated Questions ===")
print(json.dumps(questions_result, ensure_ascii=False, indent=2))

if questions_result["success"]:
    first_question = questions_result["data"]["questions"][0]["question"]

    answer_result = evaluate_interview_answer(
        target_job=target_job,
        question=first_question,
        answer="I will remove the rows with missing values.",
        resume_summary=resume_summary,
        skills=skills,
    )

    print("\n=== Evaluation Result ===")
    print(json.dumps(answer_result, ensure_ascii=False, indent=2))
