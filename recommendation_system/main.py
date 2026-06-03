import os
import json

from job_keyword import generate_job_keywords
from crawler import run_batch_crawler
from reranker import rerank_jobs


def main():

    os.environ["OPENAI_API_KEY"] = "API_KEY"

    # INPUT 1
    user_experience_input = (
        "我有兩年 Python 後端開發經驗，"
        "熟悉 Django 和 FastAPI，"
        "前端稍微懂一些 Vue.js，"
        "有用過 Docker 部署專案。"
    )

    # INPUT 2
    user_needs_input = (
        "想找台北的工作，"
        "薪資希望在 40k 以上。"
    )

    target_job_keywords = generate_job_keywords(
        user_experience=user_experience_input,
        user_needs=user_needs_input
    )

    final_job_list = run_batch_crawler(
        target_job_keywords
    )

    user_profile = f"""
工作經歷：
{user_experience_input}

求職需求：
{user_needs_input}
"""

    ranked_jobs = rerank_jobs(
        user_profile=user_profile,
        jobs=final_job_list
    )

    output_file = "ranked_jobs.json"

    # FILE
    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            ranked_jobs,
            f,
            ensure_ascii=False,
            indent=2
        )

    # OUTPUT
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

    for job in ranked_jobs:
        print(f"# {job['job_title']}")
        print()

        for key, value in job.items():
            if key not in exclude_fields:
                title = FIELD_NAMES.get(key, key)
                print(f"## {title}")
                print(value)
                print()


if __name__ == "__main__":
    main()