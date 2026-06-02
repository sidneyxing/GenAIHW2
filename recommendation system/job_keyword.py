from llm_api import llm_api


def generate_job_keywords(
    user_experience: str,
    user_needs: str
) -> list:

    system_prompt = """
你是一個專業的職涯發展顧問與求職關鍵字分析專家。
請根據使用者的「工作經歷」與「求職需求」，為他媒合適合在求職網站上搜尋的「職位名稱（關鍵字）」。

【嚴格輸出規範】
1. 請「僅」提供 2 到 4 個最精準的職位名稱。
2. 這些職位名稱必須使用「英文半形逗號 (,)」進行分隔，不要有空格。
3. 輸出的內容中「絕對不能」包含任何前言、解釋、編號、問候語或任何標點符號（除了分隔用的逗號）。
4. 範例輸出：Python工程師,後端工程師,資料工程師
"""

    user_prompt = f"""
使用者工作經歷：
{user_experience}

使用者求職需求：
{user_needs}
"""

    ai_response = llm_api(
        system_prompt,
        user_prompt
    )

    if ai_response:
        keywords = [
            k.strip()
            for k in ai_response.split(",")
            if k.strip()
        ]

        return (
            keywords[:4]
            if len(keywords) >= 2
            else keywords
        )

    return []