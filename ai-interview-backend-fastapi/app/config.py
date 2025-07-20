from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "AI Interview API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email
    GMAIL_USER: str
    GMAIL_PASSWORD: str

    # MongoDB
    MONGO_URI: str
    MONGO_DB_NAME: str
    MONGO_CV_COLLECTION: str
    MONGO_INTERVIEW_COLLECTION: str
    MONGO_FEEDBACK_COLLECTION: str

    # PostgreSQL
    DATABASE_URL: str
    PG_USER: str

    # External APIs
    API_TIMEOUT: int = 10
    JOB_API_URL: str
    MODEL_API_URL: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()

