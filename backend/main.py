
import os
import httpx

from fastapi import UploadFile, File, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
from gnani.tts import GnaniTTSClient, AudioConfig
from fastapi.responses import Response
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

@app.post("/api/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    if not GNANI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gnani API key is not configured"
        )

    audio_content = await audio_file.read()

    if not audio_content:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty"
        )

    files = {
        "audio_file": (
            audio_file.filename or "audio.mp3",
            audio_content,
            audio_file.content_type or "application/octet-stream"
        )
    }

    data = {
        "model": "prisma-v3.0",
        "language_code": "hi-IN",
        "format": "transcribe"
    }

    headers = {
        "X-API-Key-ID": GNANI_API_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.vachana.ai/stt/v3",
                headers=headers,
                data=data,
                files=files
            )

        response.raise_for_status()
        result = response.json()

        return {
            "success": True,
            "transcript": result.get("transcript"),
            "detected_language": result.get("detected_language"),
            "model": result.get("model")
        }

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail="Gnani transcription API failed"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Gnani API"
        )

    
# Text-to-Speech Request Model
class TTSRequest(BaseModel):
    text: str
    language: str = "hi-IN"
    voice: str = "Nalini"
    speed: float = 1.0


# Text-to-Speech API
@app.post("/api/tts")
def generate_speech(request: TTSRequest):

    if not GNANI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gnani API key is not configured"
        )

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty"
        )

    if not 0.85 <= request.speed <= 1.15:
        raise HTTPException(
            status_code=400,
            detail="Speed must be between 0.85 and 1.15"
        )

    try:
        client = GnaniTTSClient(api_key=GNANI_API_KEY)

        audio = client.synthesize(
            request.text,
            voice=request.voice,
            model="timbre-v2.5",
            language=request.language,
            speed=request.speed,
            audio_config=AudioConfig(
                container="mp3",
                sample_rate=44100,
                bitrate="128k"
            )
        )

        return Response(
            content=audio,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=sutrAI_speech.mp3"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Gnani TTS API failed: {str(e)}"
        )


