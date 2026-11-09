# SutrAI: Voice-First Document Assistant

SutrAI helps you understand documents by talking to them. Upload a PDF or text file, ask questions by voice or text, and get answers in Hindi, Hinglish or English that are also read aloud.

Built by Yuvraj Makani and Aanya Aggarwal.

- **Demo video:** [paste your video link here]
- **One-page pitch:** [PITCH.md](PITCH.md)

## Features

- **Voice input:** speak your question; it is transcribed with Gnani Speech-to-Text (Hindi).
- **AI answers:** Google Gemini answers your questions.
- **Voice output:** replies are spoken with Gnani Text-to-Speech.
- **Document Q&A:** upload a PDF, TXT or MD file (up to 10 MB) and ask questions about it. If the answer is not in the document, SutrAI says so.
- **Smart answer length:** short replies for simple questions, detailed structured answers for summaries and exam preparation.
- **Chat history:** a "Recent Chats" sidebar lets you reopen or delete old conversations, including their documents.
- **Memory:** chat history is kept per conversation, and long-term facts about the user (name, interests, goals) are remembered across chats.
- **Suggestion cards** and a **New Conversation** button on the welcome screen.
- **Light and dark themes:** a sun/moon button in the top bar switches between a midnight-and-gold dark mode and an ivory-and-gold light mode. Your choice is remembered.

## How it works

```
Browser (HTML/CSS/JS)  --->  FastAPI backend  --->  Gemini (answers)
   mic / text / PDF            |                |-->  Gnani STT (speech to text)
                               |                |-->  Gnani TTS (text to speech)
                               '--> JSON files for chats, documents and memory
```

## Project structure

```
SutrAI/
├── main.py            # FastAPI backend (chat, STT, TTS, documents, history)
├── requirements.txt   # Python packages
├── .env               # your API keys (NOT committed)
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

Chat history, documents and memory are saved in a `sutrai_data` folder in your home directory (`~/sutrai_data`), outside the project folder.

## Setup

### 1. Requirements
- Python 3.10 or newer
- FFmpeg (needed to convert recorded audio)
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
- A Gemini API key and a Gnani AI API key

### 2. Install packages
```bash
git clone https://github.com/yuvraj-makani/SutrAI.git
cd SutrAI
pip install -r requirements.txt
```

### 3. Add your API keys
Create a file named `.env` in the project folder (next to `main.py`):
```
GEMINI_API_KEY=your_gemini_key_here
GNANI_API_KEY=your_gnani_key_here
```

### 4. Start the backend
```bash
uvicorn main:app --port 8000
```
Check it at http://127.0.0.1:8000 (you should see "Backend is running"). API docs are at http://127.0.0.1:8000/docs.

### 5. Start the frontend
Open a second terminal:
```bash
cd SutrAI/frontend
python3 -m http.server 5500
```
Then open **http://127.0.0.1:5500/index.html** in Chrome.

> Use a plain static server like the one above. Editors with auto-reload can refresh the page unexpectedly.

## How to use

1. Type a message, or click the mic, speak, and click again to stop. Your speech is transcribed and sent automatically.
2. Click the paperclip to upload a document, then ask about it, for example "Is document ka summary batao".
3. Long answers show in full on screen, and the voice reads the first part.
4. Use **New Conversation** to start fresh, and the sidebar to return to old chats.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/chat` | Send a message and get Gemini's reply |
| POST | `/api/transcribe` | Convert recorded audio to text (Gnani STT) |
| POST | `/api/tts` | Convert text to speech (Gnani TTS) |
| POST | `/api/upload-document` | Upload a PDF, TXT or MD file for a chat |
| GET / DELETE | `/api/document/{session_id}` | Check or remove a chat's document |
| GET | `/api/sessions` | List recent chats |
| GET / DELETE | `/api/sessions/{session_id}` | Open or delete a chat |
| GET | `/api/health` | Health check |

## Tech stack

Python, FastAPI, Uvicorn, Google Gemini, Gnani AI (STT and TTS), FFmpeg, pypdf, and HTML, CSS and JavaScript with the MediaRecorder API.

## Known limitations

- Scanned PDFs (pages that are only images) are not supported because there is no OCR yet.
- Very long documents are cut to the first 150,000 characters.
- Voice input and output are tuned for Hindi (`hi-IN`).
- Data is stored in local JSON files, which is fine for a demo but not for many users.
- The app is built to run locally and is not yet deployed.

## Future work

More Indian languages, OCR for scanned documents, page references for each answer, multi-document questions, and a proper database with user accounts.
