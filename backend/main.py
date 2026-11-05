
import os

from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables from .env
load_dotenv()

# Create the FastAPI application
app = FastAPI(
    title="SutrAI",
    description="Voice-first AI assistant for understanding documents",
    version="1.0.0"
)

# Read Gnani API key securely
GNANI_API_KEY = os.getenv("GNANI_API_KEY")


@app.get("/")
def home():
    return {
        "project": "SutrAI",
        "status": "Backend is running",
        "api_key_configured": bool(GNANI_API_KEY)
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }
