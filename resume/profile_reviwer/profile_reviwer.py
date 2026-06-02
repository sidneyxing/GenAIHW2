import os
import time
import re
from dotenv import load_dotenv

from mimo_client import call_mimo

load_dotenv()

# ==========================================
# 1. LLM Client Module 
# ==========================================
class LLMClient:
    def __init__(self):
        pass

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.5) -> str:
        try:
            return call_mimo(
                system_prompt=system_prompt, 
                user_content=user_prompt, 
                use_web_search=False
            ).strip()
        except Exception as e:
            print(f"[-] MIMO API call failed: {e}")
            return ""

# ==========================================
# 2. Core Agents Definition
# ==========================================
class OrchestratorAgent:
    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = """
        You are an elite career strategy analyst.
        Your task is to analyze the candidate's raw "profile.md" and extract their most valuable technical strengths.
        
        You must output a strategy brief named "brief.md" containing:
        1. Core Positioning: The primary persona the candidate should project (e.g., "High-Concurrency Backend Expert").
        2. Key Highlights: Specific experiences (GitHub repos, publications, skills) from the profile that carry the highest value and MUST be emphasized.
        3. Refinement Strategy: How to package and improve any weak or thin descriptions in their experience.
        """

    def run(self, profile_content: str) -> str:
        user_prompt = f"--- Raw Profile ---\n{profile_content}"
        return self.client.generate(self.system_prompt, user_prompt, temperature=0.3)


class ResumeWriterAgent:
    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = """
        You are a top-tier technical resume writer.
        Your task is to write or revise a highly persuasive Markdown resume based on the "Strategy Brief" and "Raw Profile".
        
        CRITICAL RULES:
        1. NO FABRICATION: All experiences and metrics must come directly from the Raw Profile. Do not invent details.
        2. STAR METHOD: Format experiences using Situation, Task, Action, Result.
        3. STRICT REVISION: If feedback is provided, you MUST address the critiques in your revision.
        4. OUTPUT FORMAT (CRITICAL): Output ONLY the raw Markdown content of the resume. Do NOT include any conversational filler, greetings, acknowledgments, or explanations. Do not wrap the output in ```markdown blocks. Start immediately with the resume text.
        """

    def run(self, profile_content: str, brief_content: str, feedback_content: str = None, previous_resume: str = None) -> str:
        if feedback_content and previous_resume:
            user_prompt = f"--- Raw Profile ---\n{profile_content}\n\n--- Strategy Brief ---\n{brief_content}\n\n--- Previous Resume Draft ---\n{previous_resume}\n\n--- Reviewer Feedback ---\n{feedback_content}\n\nTask: Revise the previous resume draft strictly based on the reviewer feedback. OUTPUT ONLY THE REVISED MARKDOWN RESUME. NO CHAT."
        else:
            user_prompt = f"--- Raw Profile ---\n{profile_content}\n\n--- Strategy Brief ---\n{brief_content}\n\nTask: Draft the first version of a highly professional Markdown resume based on the Strategy Brief. OUTPUT ONLY THE MARKDOWN RESUME. NO CHAT."
            
        result = self.client.generate(self.system_prompt, user_prompt, temperature=0.5)
        
        result = result.replace("```markdown\n", "").replace("```markdown", "")
        if result.endswith("```"):
            result = result[:-3]
        return result.strip()


class ReviewAgent:
    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = """
        You are an extremely strict senior technical interviewer and recruiter.
        Your task is to review the resume draft and score it (out of 100) based on four criteria:
        
        [Scoring Criteria]
        1. Strategy Alignment (30 pts): Does it perfectly project the core positioning defined in the strategy brief?
        2. Technical Depth (30 pts): Are there specific algorithms, tools, or architectural details mentioned? (Reject vague descriptions like "participated in development").
        3. Quantitative Metrics (20 pts): Does it include specific metrics like performance improvements, GitHub stars, or user counts?
        4. Authenticity & Conciseness (20 pts): Are the sentences professional and concise? Is there any fabricated information?
        
        [MANDATORY OUTPUT FORMAT]
        You MUST strictly follow this exact structure without omitting the tags. Do not add any other text.
        
        ===FEEDBACK===
        (List your harsh critiques here. Be specific about what deductions were made and what needs to be changed.)
        
        ===SCORE===
        (Output ONLY a single integer from 0 to 100, e.g., 85)
        """

    def run(self, brief_content: str, resume_content: str) -> str:
        user_prompt = f"--- Strategy Brief ---\n{brief_content}\n\n--- Resume Draft ---\n{resume_content}"
        return self.client.generate(self.system_prompt, user_prompt, temperature=0.2)

# ==========================================
# 3. Core Pipeline Controller
# ==========================================
class ResumePipeline:
    def __init__(self, 
                 input_filepath: str = "./output/enriched_profile.md", 
                 output_filepath: str = "./output/resume_final.md",
                 workspace_dir: str = "./workspace"):
        
        self.input_filepath = input_filepath
        self.output_filepath = output_filepath
        self.workspace_dir = workspace_dir
        
        os.makedirs(self.workspace_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.output_filepath), exist_ok=True)
        
        self.client = LLMClient()
        self.orchestrator = OrchestratorAgent(self.client)
        self.writer = ResumeWriterAgent(self.client)
        self.reviewer = ReviewAgent(self.client)

    def _write_file(self, filename: str, content: str):
        path = os.path.join(self.workspace_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def execute(self, max_iterations: int = 3, pass_score: int = 85):
        print("\n[INIT] Starting Part 2: Resume Optimization Engine (Powered by MIMO)...")
        
        try:
            if not os.path.exists(self.input_filepath):
                raise FileNotFoundError(f"File not found: {self.input_filepath}. Please ensure Part 1 (Profile Builder) was executed successfully.")
            
            with open(self.input_filepath, "r", encoding="utf-8") as f:
                profile_content = f.read()
                
        except Exception as e:
            print(f"[ERROR] Initialization failed: {e}")
            return
        
        print("\n[ORCHESTRATOR] Analyzing profile and generating Strategy Brief...")
        brief_content = self.orchestrator.run(profile_content)
        self._write_file("brief.md", brief_content)
        print("[SUCCESS] brief.md generated.")
        
        current_resume = None
        feedback_content = None
        
        # Actor-Critic Iteration Loop
        for i in range(1, max_iterations + 1):
            print(f"\n[ITERATION {i}/{max_iterations}] Started...")
            
            print(f" └─ [WRITER] Drafting resume_v{i}.md...")
            current_resume = self.writer.run(profile_content, brief_content, feedback_content, current_resume)
            self._write_file(f"resume_v{i}.md", current_resume)
            
            print(f" └─ [REVIEWER] Evaluating draft based on strict criteria...")
            raw_feedback = self.reviewer.run(brief_content, current_resume)
            
            score = 0
            feedback_content = raw_feedback
            
            # Parse feedback and score
            try:
                if "===SCORE===" in raw_feedback:
                    parts = raw_feedback.split("===SCORE===")
                    feedback_content = parts[0].replace("===FEEDBACK===", "").strip()
                    score_match = re.search(r'\d+', parts[1])
                    if score_match:
                        score = int(score_match.group())
            except Exception as e:
                print(f" └─ [WARNING] Failed to parse score, defaulting to 0 ({e})")
            
            self._write_file("feedback.md", feedback_content)
            print(f" └─ [CURRENT SCORE]: {score} / 100")
            
            # Check termination condition
            if score >= pass_score:
                print(f"\n[PASS] Resume reached target score ({score} >= {pass_score})! Terminating loop.")
                break
            else:
                print(f" └─ [REJECTED] Score below {pass_score}. Feedback sent back to Writer for revision.")
                if i < max_iterations:
                    time.sleep(2) 
                
        # Output final result to the output directory
        print("\n[COMPLETE] Outputting Final Resume...")
        with open(self.output_filepath, "w", encoding="utf-8") as f:
            f.write(current_resume)
        print(f"[SUCCESS] Final resume saved to: {self.output_filepath}")

# ==========================================
# 4. Entry Point
# ==========================================
if __name__ == "__main__":
    INPUT_FILE = "./input/enriched_profile.md"
    OUTPUT_FILE = "./output/resume_final.md"
    WORKSPACE = "./workspace"
    
    print(f"[INFO] Preparing to start Part 2. Ensure `{INPUT_FILE}` exists.")
    
    try:
        pipeline = ResumePipeline(
            input_filepath=INPUT_FILE, 
            output_filepath=OUTPUT_FILE,
            workspace_dir=WORKSPACE
        )
        pipeline.execute(max_iterations=3, pass_score=85)
    except KeyboardInterrupt:
        print("\n[WARNING] Process interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")