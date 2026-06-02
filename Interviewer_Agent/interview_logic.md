# Interviewer Agent Logic

## Goal

The Interviewer Agent generates interview questions based on the candidate’s resume, skills, and target job.

## Workflow

1. Receive input from user or other agents:

   * resume_summary
   * skills
   * target_job
   * job_description

2. Analyze the target job:

   * Identify job title
   * Classify job field
   * Detect important skills for the job
   * Estimate interview difficulty level

3. Generate interview questions:

   * Technical question
   * Project experience question
   * Problem-solving question
   * Behavioral question
   * Follow-up style question

4. Adapt the question difficulty:

   * Beginner: basic concepts and simple examples
   * Intermediate: practical experience and problem solving
   * Advanced: system design, optimization, decision making

5. Return structured JSON output so backend/frontend can use it easily.

## Job Classification Examples

If user types "data analyst", classify as:

* field: Data Analysis
* focus: SQL, Excel, Python, data cleaning, visualization

If user types "frontend engineer", classify as:

* field: Frontend Development
* focus: HTML, CSS, JavaScript, React, UI interaction

If user types "AI engineer", classify as:

* field: Artificial Intelligence / Machine Learning
* focus: Python, model training, dataset, evaluation, overfitting

If user types "marketing specialist", classify as:

* field: Marketing
* focus: market research, campaign planning, communication, data analysis

If user types "project manager", classify as:

* field: Project Management
* focus: planning, teamwork, communication, risk management

## Output Requirement

The agent must always return JSON with:

* job_title
* job_field
* candidate_level
* interview_focus
* questions
