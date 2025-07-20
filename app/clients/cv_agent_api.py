import httpx
from fastapi import UploadFile
from app.config import settings

async def parse_cv(cv: UploadFile):
    async with httpx.AsyncClient(timeout=settings.API_TIMEOUT) as client:
        files = {'file': (cv.filename, await cv.read(), cv.content_type)}
        response = await client.post(f"{settings.MODEL_API_URL}/parse", files=files)
        response.raise_for_status()
        return response.json()

async def simulate_interview(prompt: str):
    async with httpx.AsyncClient(timeout=settings.API_TIMEOUT) as client:
        response = await client.post(f"{settings.MODEL_API_URL}/simulate", json={"prompt": prompt})
        response.raise_for_status()
        return response.json()
