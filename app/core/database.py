from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# MongoDB
mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
mongo_db = mongo_client[settings.MONGO_DB_NAME]

# PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
