from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import mongo_db
from app.schemas.interview_schemas import CVParseResponse, InterviewStartRequest, InterviewResponse, FeedbackRequest
from app.services.interviews import service
from app.services.auth.security import get_current_user # Assuming user authentication is required
from app.schemas.interview_schemas import CVParseResponse, InterviewStartRequest, InterviewResponse, FeedbackRequest, InterviewMessage 
router = APIRouter()

async def get_mongo_db():
    return mongo_db

@router.post("/cv", response_model=CVParseResponse)
async def upload_cv(cv: UploadFile = File(...), db: AsyncIOMotorDatabase = Depends(get_mongo_db), current_user: dict = Depends(get_current_user)):
    try:
        cv_id, parsed_data = await service.process_cv_upload(db, cv, str(current_user["id"]))
        return CVParseResponse(cv_id=cv_id, parsed_data=parsed_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CV: {e}")

@router.post("/simulation/start", response_model=InterviewResponse)
async def start_simulation(request: InterviewStartRequest, db: AsyncIOMotorDatabase = Depends(get_mongo_db), current_user: dict = Depends(get_current_user)):
    try:
        interview_id, conversation, agent_response = await service.start_interview_simulation(db, request.cv_id, request.initial_prompt, str(current_user["id"]))
        return InterviewResponse(interview_id=interview_id, conversation=conversation, agent_response=agent_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {e}")

@router.post("/simulation/{interview_id}/continue", response_model=InterviewResponse)
async def continue_simulation(interview_id: str, message: InterviewMessage, db: AsyncIOMotorDatabase = Depends(get_mongo_db), current_user: dict = Depends(get_current_user)):
    try:
        conversation, agent_response = await service.continue_interview_simulation(db, interview_id, message.content)
        return InterviewResponse(interview_id=interview_id, conversation=conversation, agent_response=agent_response)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to continue simulation: {e}")

@router.post("/feedback", status_code=201)
async def submit_feedback(request: FeedbackRequest, db: AsyncIOMotorDatabase = Depends(get_mongo_db), current_user: dict = Depends(get_current_user)):
    try:
        feedback_id = await service.submit_feedback(db, request.interview_id, request.feedback_content, str(current_user["id"]))
        return {"message": "Feedback submitted successfully", "feedback_id": feedback_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {e}")