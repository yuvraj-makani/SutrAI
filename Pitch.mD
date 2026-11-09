# SutrAI: Understand Any Document by Talking to It

**Gnani AI Internship Challenge** | Team: Yuvraj Makani, Aanya Aggarwal

## The problem
Learners often have to read long, dense PDFs and notes, usually in English. Reading is slow and tiring, and many people are more comfortable speaking in Hindi or Hinglish than reading technical English. Typing questions into a text-only chatbot adds more friction.

## Our solution
**SutrAI is a voice-first AI assistant that helps people understand documents through natural conversation.** Upload a PDF or text file, then ask questions by speaking or typing. SutrAI answers in your language (Hindi, Hinglish or English) and reads the answer back to you.

A student can upload class notes, say "Is document ka summary batao, 30 marks ke exam ke liye", and get a structured, exam-ready answer that is also read aloud.

## How it works
1. **Speak:** the browser records your voice and sends it to Gnani's Speech-to-Text API (Hindi).
2. **Understand:** the question and the uploaded document go to Google Gemini, which answers only from the document and says so when the answer is not there.
3. **Listen:** Gnani's Text-to-Speech API turns the reply into natural Hindi speech.

## What makes it useful
- **Voice in, voice out:** a complete hands-free loop built on Gnani STT and TTS.
- **Document grounded:** answers come from your file, and SutrAI admits when it doesn't know.
- **Right-sized answers:** short replies for simple questions, detailed structured answers for summaries and exam prep.
- **Memory:** it remembers long-term facts such as your name and goals, and keeps every conversation.
- **Chat history:** past chats and their documents can be reopened or deleted from a sidebar.

## Technology
Python and FastAPI backend, Google Gemini for reasoning, Gnani AI for speech (STT and TTS), FFmpeg for audio conversion, and a lightweight HTML, CSS and JavaScript frontend using the browser's MediaRecorder API.

## Impact and next steps
SutrAI lowers the barrier to understanding study material and official documents for people who think and speak in Indian languages. Next we plan to support more Indian languages, scanned documents through OCR, quoting the exact page behind each answer, and multi-document questions.
