import os
import tempfile
import uuid
import uvicorn
from typing import Dict, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from logic import InterviewBot, InterviewSession
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv


load_dotenv()


# Initialize FastAPI app
app = FastAPI(
    title="AI Interview Chatbot API",
    description="An AI-powered interview chatbot that processes resumes and conducts technical interviews",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for sessions (in production, use Redis or database)
sessions: Dict[str, InterviewSession] = {}
interview_bot: Optional[InterviewBot] = None

# Pydantic models
class StartInterviewResponse(BaseModel):
    session_id: str
    first_question: str
    progress: str

class SubmitAnswerRequest(BaseModel):
    answer: str

class SubmitAnswerResponse(BaseModel):
    next_question: Optional[str] = None
    progress: Optional[str] = None
    is_completed: bool = False
    grade: Optional[str] = None
    feedback: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# Dependency to get interview bot instance
def get_interview_bot() -> InterviewBot:
    global interview_bot
    if interview_bot is None:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(
                status_code=500, 
                detail="GOOGLE_API_KEY environment variable not set"
            )
        interview_bot = InterviewBot(google_api_key)
    return interview_bot

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Interview Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/start-interview": "POST - Upload resume and start interview",
            "/submit-answer/{session_id}": "POST - Submit answer to current question",
            "/get-question/{session_id}": "GET - Get current question",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Interview Chatbot"}

@app.post("/start-interview", response_model=StartInterviewResponse)
async def start_interview(
    file: UploadFile = File(...),
    bot: InterviewBot = Depends(get_interview_bot)
):
    """
    Start a new interview session by uploading a resume.
    
    - **file**: Resume file (PDF or image format)
    - Returns session ID and first question
    """
    try:
        # Validate file type
        if not file.content_type.startswith(('image/', 'application/pdf')):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and image files are supported"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process resume
            resume_text = bot.process_resume(tmp_file_path)
            
            # Generate questions
            questions = bot.generate_interview_questions(resume_text)
            
            # Create session
            session_id = str(uuid.uuid4())
            session = InterviewSession(questions)
            sessions[session_id] = session
            
            # Get first question
            first_question = session.get_current_question()
            progress = session.get_question_progress()
            
            return StartInterviewResponse(
                session_id=session_id,
                first_question=first_question,
                progress=progress
            )
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.post("/submit-answer/{session_id}", response_model=SubmitAnswerResponse)
async def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    bot: InterviewBot = Depends(get_interview_bot)
):
    """
    Submit an answer to the current question.
    
    - **session_id**: Interview session ID
    - **request**: Answer text
    - Returns next question or completion status with grade
    """
    try:
        # Get session
        session = sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.is_completed:
            raise HTTPException(status_code=400, detail="Interview already completed")
        
        # Submit answer
        continues = session.submit_answer(request.answer)
        
        if continues:
            # Get next question
            next_question = session.get_next_question()
            progress = session.get_question_progress()
            
            return SubmitAnswerResponse(
                next_question=next_question,
                progress=progress,
                is_completed=False
            )
        else:
            # Interview completed, generate grade
            grade, feedback = bot.generate_grade_report(session.answers)
            
            # Clean up session
            del sessions[session_id]
            
            return SubmitAnswerResponse(
                is_completed=True,
                grade=grade,
                feedback=feedback
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")

@app.get("/get-question/{session_id}")
async def get_current_question(session_id: str):
    """
    Get the current question for a session.
    
    - **session_id**: Interview session ID
    - Returns current question and progress
    """
    try:
        session = sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.is_completed:
            return {
                "is_completed": True,
                "message": "Interview completed"
            }
        
        current_question = session.get_current_question()
        progress = session.get_question_progress()
        
        return {
            "question": current_question,
            "progress": progress,
            "is_completed": False
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting question: {str(e)}")

@app.delete("/end-interview/{session_id}")
async def end_interview(session_id: str):
    """
    End an interview session early.
    
    - **session_id**: Interview session ID
    - Returns confirmation message
    """
    try:
        session = sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Clean up session
        del sessions[session_id]
        
        return {"message": "Interview session ended successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending interview: {str(e)}")

@app.get("/sessions")
async def get_active_sessions():
    """
    Get list of active sessions (for debugging/monitoring).
    
    - Returns list of active session IDs and their progress
    """
    active_sessions = []
    for session_id, session in sessions.items():
        active_sessions.append({
            "session_id": session_id,
            "progress": session.get_question_progress(),
            "is_completed": session.is_completed,
            "questions_answered": len(session.answers)
        })
    
    return {
        "active_sessions": len(sessions),
        "sessions": active_sessions
    }

# Error handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)