# Backend API Contract Recommendation

The frontend can already run in static demo mode. To connect it to the real backend, ask the backend team to expose these endpoints.

## 1. Generate job recommendations

`POST /api/recommendations`

Request:

```json
{
  "user_experience_input": {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "location": "San Francisco, CA",
    "work_experience": "...",
    "education": "...",
    "skills": "...",
    "github_url": "...",
    "publication_urls": ["..."]
  },
  "user_needs_input": "Looking for a job in Taipei. Hoping for salary above NT$40,000."
}
```

Response:

```json
{
  "jobs": [
    {
      "id": 3,
      "job_title": "...",
      "company_name": "...",
      "location": "...",
      "salary": "...",
      "education": "...",
      "experience": "...",
      "description": "...",
      "link": "...",
      "score": 9.0,
      "verdict": "..."
    }
  ]
}
```

## 2. Generate optimized resume

`POST /api/resume`

Request:

```json
{
  "user_experience_input": { "...": "..." },
  "job": { "...selected job object...": "..." }
}
```

Response:

```json
{
  "resume_markdown": "Jane Doe\nSoftware Engineer\n..."
}
```

The frontend can directly render this markdown.

## 3. Generate interview questions

`POST /api/interview/questions`

Request:

```json
{
  "job": { "...selected job object...": "..." },
  "profile": "optimized resume or profile summary"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "job_title": "Python Backend Engineer",
    "job_field": "Backend Engineering",
    "candidate_level": "Advanced",
    "interview_focus": ["Python Development", "System Architecture"],
    "questions": [
      {
        "type": "technical",
        "difficulty": "advanced",
        "question": "..."
      }
    ]
  }
}
```

## 4. Evaluate one interview answer

`POST /api/interview/evaluate`

Request:

```json
{
  "job": { "...selected job object...": "..." },
  "profile": "optimized resume or profile summary",
  "question": "...",
  "answer": "..."
}
```

Response:

```json
{
  "success": true,
  "data": {
    "score": 7.0,
    "feedback": "...",
    "strengths": ["..."],
    "weaknesses": ["..."],
    "better_answer": "...",
    "follow_up_question": "..."
  }
}
```

## 5. Generate final interview summary

`POST /api/interview/summary`

Request:

```json
{
  "job": { "...selected job object...": "..." },
  "evaluated_answers": [
    {
      "question": "...",
      "answer": "...",
      "score": 7.0,
      "strengths": ["..."],
      "weaknesses": ["..."]
    }
  ]
}
```

Response:

```json
{
  "success": true,
  "data": {
    "total_questions": 5,
    "average_score": 5.8,
    "overall_level": "Fair",
    "recommendation": "Maybe",
    "summary": "...",
    "strong_areas": ["..."],
    "weak_areas": ["..."]
  }
}
```
