import json
import os
from interviewer_agent import generate_interview_questions, evaluate_interview_answer, aggregate_interview_result

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