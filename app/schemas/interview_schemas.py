from pydantic import BaseModel, Field

class CVParseResponse(BaseModel):
    cv_id: str
    parsed_data: dict

class InterviewStartRequest(BaseModel):
    cv_id: str
    initial_prompt: str

class InterviewMessage(BaseModel):
    role: str
    content: str

class InterviewResponse(BaseModel):
    interview_id: str
    conversation: list[InterviewMessage]
    agent_response: str

class FeedbackRequest(BaseModel):
    interview_id: str
    feedback_content: dict
