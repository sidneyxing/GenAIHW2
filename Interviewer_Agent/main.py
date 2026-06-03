import json
import os
from interviewer_agent import generate_interview_questions, evaluate_interview_answer

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
    print("啟動面試模擬 Agent...")
    
    # 1. 設定檔案路徑 (相對於專案根目錄 GenAIHW2)
    # 注意：這裡使用會議中提到的路徑
    resume_path = "resume/profile_reviwer/workspace/resume_final.md" 
    jobs_path = "recommendation system/ranked_jobs.json"

    # 2. 讀取實體履歷檔案
    print(f"正在讀取履歷: {resume_path}")
    resume_content = load_file_content(resume_path)
    if not resume_content:
        resume_content = "Software Engineer with Python and Docker experience." # 防呆預設值

    # 3. 讀取實體職缺檔案
    print(f"正在讀取職缺: {jobs_path}")
    jobs_data = load_json_content(jobs_path)
    
    target_job_title = "未指定職缺"
    job_desc = "未提供詳細說明"
    
    # 解析職缺資料 (假設推薦系統吐出來的是一個 List，我們取第一個)
    if isinstance(jobs_data, list) and len(jobs_data) > 0:
        first_job = jobs_data[0]
        # 假設職缺名稱存在 'title' 或 'job_title' 欄位
        target_job_title = first_job.get("title", first_job.get("job_title", "Software Engineer"))
        job_desc = json.dumps(first_job, ensure_ascii=False) 
    
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

    # 6. 模擬面試回答與評分 (你剛剛提到的 Evaluation Result)
    if result["success"] and result["data"]["questions"]:
        # 抓出第一題來測試
        first_question = result["data"]["questions"][0]["question"]
        
        print("\n" + "="*40)
        print("💡 進入面試評分測試階段")
        print("="*40)
        print(f"🤖 面試官提問: {first_question}")
        
        # 這裡我們模擬一個求職者的回答
        test_answer = "我會使用 Python 的 pandas 套件讀取資料，並使用 fillna 方法將缺失值補上平均數，或者用 dropna 將損壞的資料刪除。"
        print(f"👤 求職者回答: {test_answer}")
        
        print("\n⏳ 正在呼叫評分 Agent 進行專業評估...")
        eval_result = evaluate_interview_answer(
            target_job=target_job_title,
            question=first_question,
            answer=test_answer,
            resume_summary=resume_content,
            skills=[]
        )
        
        print("\n=== Evaluation Result (單題評分結果) ===")
        print(json.dumps(eval_result, ensure_ascii=False, indent=2))
        
        # 將評估結果也存成 JSON 檔案，讓前端可以直接讀取畫圖
        eval_filename = "Interviewer_Agent/evaluation_result.json"
        with open(eval_filename, "w", encoding="utf-8") as f:
            json.dump(eval_result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 評分結果已成功儲存至 {eval_filename}！")

if __name__ == "__main__":
    main()