import base64
import os
import re
import tempfile
from typing import List, Tuple, Optional
from pdf2image import convert_from_path
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


class InterviewBot:
    def __init__(self, google_api_key: str):
        """Initialize the Interview Bot with Google API key."""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.7,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            google_api_key=google_api_key
        )
    
    def process_image(self, image_path: str) -> str:
        """Process a single image and extract resume information."""
        try:
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
            
            msg = HumanMessage(content=[
                {
                    "type": "text", 
                    "text": """Extract in format:
                    Skills: [comma-separated]
                    Education: [degrees with institutions]
                    Only include these sections"""
                },
                {
                    "type": "image_url", 
                    "image_url": f"data:image/jpeg;base64,{encoded}"
                }
            ])
            
            return self.llm.invoke([msg]).content
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")
    
    def process_resume(self, file_path: str) -> str:
        """Process resume file (PDF or image) and extract content."""
        try:
            if file_path.lower().endswith('.pdf'):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    images = convert_from_path(file_path, output_folder=tmp_dir)
                    content = []
                    for i, img in enumerate(images):
                        img_path = f"{tmp_dir}/page_{i+1}.jpg"
                        img.save(img_path, "JPEG")
                        content.append(self.process_image(img_path))
                    return "\n".join(content)
            else:
                return self.process_image(file_path)
        except Exception as e:
            raise Exception(f"Error processing resume: {str(e)}")
    
    def generate_interview_questions(self, resume_text: str) -> List[str]:
        """Generate 25 technical questions based on resume content."""
        try:
            prompt = f"""Generate 25 technical questions based on:
            {resume_text}

            Format STRICTLY as:
            1. Tell me about yourself
            2. [Question about first skill]
            3. [Question about education]
            ...
            25. [Final question]

            Include only numbered questions, no other text."""

            response = self.llm.invoke([HumanMessage(content=prompt)]).content
            questions = []
            
            for line in response.split('\n'):
                match = re.match(r'^\d+\.\s*(.+)', line.strip())
                if match and len(questions) < 25:
                    questions.append(match.group(1))
            
            # Ensure we have exactly 25 questions
            if len(questions) < 25:
                base_questions = questions if questions else ["Tell me about yourself"]
                while len(base_questions) < 25:
                    base_questions.append(f"Question {len(base_questions) + 1}")
                return base_questions[:25]
            
            return questions[:25]
        except Exception as e:
            # Fallback questions
            return ["Tell me about yourself"] + [f"Question {i}" for i in range(2, 26)]
    
    def generate_grade_report(self, answers: List[str]) -> Tuple[str, str]:
        """Generate grade and feedback based on interview answers."""
        try:
            answer_log = "\n".join([f"{i+1}. {a}" for i, a in enumerate(answers)])

            prompt = f"""Evaluate interview performance:
            {answer_log}

            Provide output EXACTLY as:
            Grade: [A+/A/B+/B/C/D]
            Feedback: [50-60 character assessment]

            Consider: technical accuracy, communication, completeness"""

            response = self.llm.invoke([HumanMessage(content=prompt)]).content
            
            grade_match = re.search(r'Grade:\s*([A+ABCD]+)', response)
            feedback_match = re.search(r'Feedback:\s*(.+?)(\n|$)', response)
            
            grade = grade_match.group(1) if grade_match else "N/A"
            feedback = feedback_match.group(1) if feedback_match else "Evaluation failed"
            
            return grade, feedback
        except Exception as e:
            return "N/A", f"Evaluation failed: {str(e)}"


class InterviewSession:
    """Manages an individual interview session state."""
    
    def __init__(self, questions: List[str]):
        self.questions = questions
        self.current_question_idx = 0
        self.answers = []
        self.is_completed = False
    
    def get_current_question(self) -> Optional[str]:
        """Get the current question."""
        if self.current_question_idx < len(self.questions):
            return self.questions[self.current_question_idx]
        return None
    
    def get_question_progress(self) -> str:
        """Get question progress string."""
        return f"{self.current_question_idx + 1}/{len(self.questions)}"
    
    def submit_answer(self, answer: str) -> bool:
        """Submit an answer and move to next question. Returns True if interview continues."""
        if self.is_completed:
            return False
        
        self.answers.append(answer)
        self.current_question_idx += 1
        
        if self.current_question_idx >= len(self.questions):
            self.is_completed = True
            return False
        
        return True
    
    def get_next_question(self) -> Optional[str]:
        """Get the next question after submitting an answer."""
        if self.is_completed:
            return None
        return self.get_current_question()