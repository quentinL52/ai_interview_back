from datetime import datetime
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.clients import cv_agent_api
from app.models.mongo.cv_model import CVModel
from app.models.mongo.interview_history_model import InterviewHistoryModel
from app.models.mongo.feedback_model import FeedbackModel
from app.schemas.interview_schemas import InterviewMessage

async def process_cv_upload(db: AsyncIOMotorDatabase, cv_file: UploadFile, user_id: str):
    parsed_data = await cv_agent_api.parse_cv(cv_file)
    cv_entry = CVModel(
        user_id=user_id,
        parsed_data=parsed_data,
        raw_text=None, # You might want to extract text from PDF here
        upload_date=datetime.utcnow().isoformat()
    )
    cv_id = await CVModel.create(db, CVModel.collection_name, cv_entry.model_dump(exclude_unset=True))
    return cv_id, parsed_data

async def start_interview_simulation(db: AsyncIOMotorDatabase, cv_id: str, initial_prompt: str, user_id: str):
    # Initial call to agent
    agent_response = await cv_agent_api.simulate_interview(initial_prompt)

    conversation = [
        InterviewMessage(role="user", content=initial_prompt).model_dump(),
        InterviewMessage(role="agent", content=agent_response.get("response")).model_dump()
    ]

    interview_entry = InterviewHistoryModel(
        user_id=user_id,
        cv_id=cv_id,
        conversation=conversation,
        start_time=datetime.utcnow().isoformat()
    )
    interview_id = await InterviewHistoryModel.create(db, InterviewHistoryModel.collection_name, interview_entry.model_dump(exclude_unset=True))
    return interview_id, conversation, agent_response.get("response")

async def continue_interview_simulation(db: AsyncIOMotorDatabase, interview_id: str, user_message: str):
    interview_history = await InterviewHistoryModel.get(db, InterviewHistoryModel.collection_name, {"_id": interview_id})
    if not interview_history:
        raise ValueError("Interview not found")

    current_conversation = interview_history.get("conversation", [])
    current_conversation.append(InterviewMessage(role="user", content=user_message).model_dump())

    # Send full conversation to agent for context
    full_prompt = "\n".join([msg["content"] for msg in current_conversation])
    agent_response = await cv_agent_api.simulate_interview(full_prompt)

    current_conversation.append(InterviewMessage(role="agent", content=agent_response.get("response")).model_dump())

    await InterviewHistoryModel.update(db, InterviewHistoryModel.collection_name, 
                                       {"_id": interview_id}, 
                                       {"conversation": current_conversation})
    
    return current_conversation, agent_response.get("response")

async def submit_feedback(db: AsyncIOMotorDatabase, interview_id: str, feedback_content: dict, user_id: str):
    feedback_entry = FeedbackModel(
        user_id=user_id,
        interview_id=interview_id,
        feedback_content=feedback_content,
        feedback_date=datetime.utcnow().isoformat()
    )
    feedback_id = await FeedbackModel.create(db, FeedbackModel.collection_name, feedback_entry.model_dump(exclude_unset=True))
    return feedback_id
