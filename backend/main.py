
import os
import httpx
import subprocess
from google import genai
from dotenv import load_dotenv
from fastapi import UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gnani.tts import GnaniTTSClient, AudioConfig
from fastapi.responses import Response
from google.genai import types
from fastapi import FastAPI

# Load environment variables from .env
load_dotenv()

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=2,
            initial_delay=0.5,
            max_delay=2.0,
        )
    )
)

# Create the FastAPI application 
app = FastAPI(
    title="SutrAI",
    description="Voice-first AI assistant for understanding documents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    # Convert WebM audio to WAV using FFmpeg
    try:
        conversion = subprocess.run(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-ac", "1",
                "-ar", "16000",
                "-f", "wav",
                "pipe:1"
            ],
            input=audio_content,
            capture_output=True,
            check=True
        )

        wav_content = conversion.stdout

    except subprocess.CalledProcessError as e:
        print("FFmpeg Error:", e.stderr.decode(errors="ignore"))

        raise HTTPException(
            status_code=400,
            detail="Audio conversion failed"
        )

    files = {
        "audio_file": (
            "recording.wav",
            wav_content,
            "audio/wav"
        )
    }

    data = {
        "language_code": "hi-IN",
        "preferred_language": "hi-IN",
        "format": "transcribe",
        "itn_native_numerals": "true"
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

        print("Gnani Response:", result)

        return {
            "success": True,
            "transcript": result.get("transcript"),
            "detected_language": result.get("detected_language"),
            "model": result.get("model")
        }

    except httpx.HTTPStatusError as e:
        print("Gnani API Status:", e.response.status_code)
        print("Gnani API Error:", e.response.text)

        raise HTTPException(
            status_code=502,
            detail=f"Gnani API Error: {e.response.status_code} - {e.response.text}"
        )

    except httpx.RequestError as e:
        print("Gnani Connection Error:", str(e))

        raise HTTPException(
            status_code=502,
            detail=f"Unable to connect to Gnani API: {str(e)}"
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


class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
def chat_with_gemini(request: ChatRequest):
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=request.message,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level="LOW"
        )
    )
)

        return {"reply": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))