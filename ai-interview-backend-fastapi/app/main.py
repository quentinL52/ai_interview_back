from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.auth.router import router as auth_router
from app.services.contact.router import router as contact_router
from app.services.interviews.router import router as interviews_router
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(contact_router, prefix=f"{settings.API_V1_STR}/contact", tags=["Contact"])
app.include_router(interviews_router, prefix=f"{settings.API_V1_STR}/interviews", tags=["Interviews"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Interview API"}
