import json
import re

from resume.profile_reviwer.mimo_client import call_mimo


def parse_evaluations(raw_response: str) -> dict:

    text = re.sub(
        r"```(?:json)?",
        "",
        raw_response
    ).strip()

    start = text.find("{")

    if start == -1:
        return {
            "success": False,
            "error": "no JSON found",
            "data": None
        }

    depth = 0
    json_str = None

    for i, ch in enumerate(text[start:], start):

        if ch == "{":
            depth += 1

        elif ch == "}":
            depth -= 1

            if depth == 0:
                json_str = text[start:i + 1]
                break

    if not json_str:
        return {
            "success": False,
            "error": "unbalanced JSON braces",
            "data": None
        }

    try:
        data = json.loads(json_str)

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"JSON decode error: {e}",
            "data": None
        }

    evaluations = data.get("evaluations")

    if not isinstance(evaluations, list):
        return {
            "success": False,
            "error": "missing or invalid evaluations",
            "data": None
        }

    parsed = []

    for item in evaluations:

        try:

            score = max(
                1.0,
                min(
                    10.0,
                    float(item["score"])
                )
            )

            parsed.append(
                {
                    "id": str(item["id"]),
                    "score": round(score, 1),
                    "verdict": str(
                        item["verdict"]
                    ).strip()
                }
            )

        except (
            KeyError,
            TypeError,
            ValueError
        ):
            continue

    if not parsed:
        return {
            "success": False,
            "error": "no valid evaluation entries",
            "data": None
        }

    return {
        "success": True,
        "error": None,
        "data": parsed
    }


def rerank_jobs(
    user_profile: str,
    jobs: list
) -> list:

    system_prompt = """
你是一位專業的職涯顧問與職缺評估專家。

你會收到：

1. 求職者背景
2. 一份職缺清單

請先將所有職缺放在同一個候選池中進行整體比較，再進行評分。

評分時請從求職者角度出發，綜合考量所有可能影響求職決策的重要因素，包括但不限於：

- 工作內容與技能匹配度
- 職涯成長與未來發展性
- 技術或產業前景
- 學習機會與履歷加值效果
- 公司與團隊環境
- 工作條件與地點
- 薪資福利與整體待遇
- 工作穩定性
- 求職者的轉職目標與需求
- 其他你認為重要的因素

不要機械式地依照固定維度打分。

請根據整體吸引力與長期價值進行判斷。

評分必須反映：
「如果你是這位求職者，綜合考量後會有多想投遞這份職缺」。

請對所有職缺進行相對排序評分：

- 10 分代表極度推薦
- 8~9 分代表明顯值得優先考慮
- 6~7 分代表可考慮
- 4~5 分代表吸引力有限
- 1~3 分代表不太建議投入時間

只回傳合法 JSON，不要有任何 markdown 或其他文字。

Schema：
{
  "evaluations": [
    {
      "id": "<來自輸入的職缺 id>",
      "score": <1.0-10.0>,
      "verdict": "<繁體中文一句話，最多30字，說明這份職缺最主要的優勢或疑慮>"
    }
  ]
}
"""

    user_prompt = f"""
求職者個人資訊：
{user_profile}

職缺清單：
{json.dumps(jobs, ensure_ascii=False, indent=2)}
"""

    raw_response = call_mimo(
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    result = parse_evaluations(
        raw_response
    )

    if not result["success"]:
        print(result["error"])
        return jobs

    evaluation_map = {
        str(item["id"]): item
        for item in result["data"]
    }

    ranked_jobs = []

    for job in jobs:

        job_id = str(job["id"])

        eval_info = evaluation_map.get(
            job_id,
            {
                "score": 1.0,
                "verdict": "未取得評分"
            }
        )

        ranked_jobs.append(
            {
                **job,
                "score": eval_info["score"],
                "verdict": eval_info["verdict"]
            }
        )

    ranked_jobs.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranked_jobs