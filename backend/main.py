import os
import json
import subprocess

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from google import genai
from google.genai import types
from gnani.tts import GnaniTTSClient, AudioConfig
from pydantic import BaseModel

# Load environment variables from .env
load_dotenv()

# ---------------------------------------------------------------------------
# MEMORY FILES
# They are stored OUTSIDE the project folder (in ~/sutrai_data).
# Reason: VS Code Live Server reloads the page whenever ANY file in the
# project folder changes. Saving chat_memory.json right before the reply
# was sent is what made your page refresh.
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.expanduser("~"), "sutrai_data")
os.makedirs(DATA_DIR, exist_ok=True)

MEMORY_FILE = os.path.join(DATA_DIR, "chat_memory.json")
USER_MEMORY_FILE = os.path.join(DATA_DIR, "user_memory.json")


def _load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_memory():
    return _load_json(MEMORY_FILE)


def save_memory(memory):
    _save_json(MEMORY_FILE, memory)


def load_user_memory():
    return _load_json(USER_MEMORY_FILE)


def save_user_memory(memory):
    _save_json(USER_MEMORY_FILE, memory)


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

GEMINI_MODEL = "gemini-3.5-flash-lite"

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
        "http://127.0.0.1:5502",
        "http://localhost:5502",
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
        "api_key_configured": bool(GNANI_API_KEY),
        "gemini_key_configured": bool(os.getenv("GEMINI_API_KEY"))
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# SPEECH TO TEXT
# ---------------------------------------------------------------------------
@app.post("/api/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    if not GNANI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gnani API key is not configured"
        )

    audio_content = await audio_file.read()

    if not audio_content:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    # Convert WebM/MP4 audio to WAV using FFmpeg
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

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="FFmpeg is not installed on the server"
        )

    except subprocess.CalledProcessError as e:
        print("FFmpeg Error:", e.stderr.decode(errors="ignore"))
        raise HTTPException(status_code=400, detail="Audio conversion failed")

    files = {
        "audio_file": ("recording.wav", wav_content, "audio/wav")
    }

    data = {
        "language_code": "hi-IN",
        "preferred_language": "hi-IN",
        "format": "transcribe",
        "itn_native_numerals": "true"
    }

    headers = {"X-API-Key-ID": GNANI_API_KEY}

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


# ---------------------------------------------------------------------------
# TEXT TO SPEECH
# ---------------------------------------------------------------------------
class TTSRequest(BaseModel):
    text: str
    language: str = "hi-IN"
    voice: str = "Nalini"
    speed: float = 1.0


@app.post("/api/tts")
def generate_speech(request: TTSRequest):

    if not GNANI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gnani API key is not configured"
        )

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

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


# ---------------------------------------------------------------------------
# CHAT (GEMINI) + MEMORY
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str


def parse_facts(text):
    """Gemini often wraps JSON in ```json fences. Remove them, then parse."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    facts = json.loads(text)
    if not isinstance(facts, list):
        return []
    return [f.strip() for f in facts if isinstance(f, str) and f.strip()]


def extract_and_save_facts(message: str):
    """Runs AFTER the reply is sent, so the user never waits for it."""
    try:
        extraction_prompt = f"""
        Extract important long-term facts about the user from this message.
        Save useful facts like name, education, interests, preferences, and goals.
        Ignore temporary details.
        Return only a JSON array of short strings.
        If there are no useful facts, return [].

        User message: {message}
        """

        extraction_response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=extraction_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )

        new_facts = parse_facts(extraction_response.text)
        if not new_facts:
            return

        user_memory = load_user_memory()
        user_facts = user_memory.get("facts", [])

        for fact in new_facts:
            if fact not in user_facts:
                user_facts.append(fact)

        user_memory["facts"] = user_facts
        save_user_memory(user_memory)

    except Exception as e:
        # Memory is a bonus feature: never let it break the chat.
        print("Memory extraction skipped:", str(e))


@app.post("/api/chat")
def chat_with_gemini(request: ChatRequest, background_tasks: BackgroundTasks):
    memory = load_memory()
    history = memory.get(request.session_id, [])
    user_facts = load_user_memory().get("facts", [])

    memory_context = "User's long-term memory: " + json.dumps(
        user_facts, ensure_ascii=False
    )

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                *history,
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": memory_context
                            + "\n\nUser's message: "
                            + request.message
                        }
                    ],
                },
            ],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level="LOW"
                )
            ),
        )

        reply = response.text
        if not reply:
            raise ValueError("Gemini returned an empty response")

    except Exception as e:
        print("Gemini Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

    # Save chat history
    history.append({"role": "user", "parts": [{"text": request.message}]})
    history.append({"role": "model", "parts": [{"text": reply}]})
    memory[request.session_id] = history
    save_memory(memory)

    # Learn long-term facts in the background
    background_tasks.add_task(extract_and_save_facts, request.message)

    return {"reply": reply}