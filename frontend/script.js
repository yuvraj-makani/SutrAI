const API_BASE = "http://127.0.0.1:8000";
let chatHistory = [];
let sessionId = localStorage.getItem("sutrai_session_id");

if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem("sutrai_session_id", sessionId);
}
// DOM Elements
const chatArea = document.getElementById("chatArea");
const welcomeScreen = document.getElementById("welcomeScreen");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const recordingStatus = document.getElementById("recordingStatus");
const audioPlayer = document.getElementById("audioPlayer");
const newChatBtn = document.getElementById("newChatBtn");

let mediaRecorder = null;
let audioChunks = [];
let mediaStream = null;
let isRecording = false;
let isBusy = false;


// Add a message to the chat
function addMessage(text, sender) {
    if (welcomeScreen) {
        welcomeScreen.style.display = "none";
    }

    const message = document.createElement("div");
    message.className = `message ${sender}`;

    if (sender === "assistant") {
        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = "S";
        message.appendChild(avatar);
    }

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;

    message.appendChild(content);
    chatArea.appendChild(message);

    chatArea.scrollTop = chatArea.scrollHeight;

    return message;
}


// Show temporary status message
function showStatus(message) {
    recordingStatus.textContent = message;
}


// Text to Speech
async function speakText(text) {
    if (!text.trim()) return;

    try {
        showStatus("Generating voice...");

        const response = await fetch(`${API_BASE}/api/tts`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: text,
                language: "hi-IN"
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "TTS API failed");
        }

        const audioBlob = await response.blob();

        if (audioPlayer.src) {
            URL.revokeObjectURL(audioPlayer.src);
        }

        audioPlayer.src = URL.createObjectURL(audioBlob);
        audioPlayer.hidden = false;

        await audioPlayer.play();

        showStatus("Voice ready");

    } catch (error) {
        console.error("TTS Error:", error);
        showStatus("Voice generation failed");
        addMessage("Voice generation failed: " + error.message, "assistant");
    }
}


// Send text message to AI
async function sendMessage() {
    const text = messageInput.value.trim();

    if (!text || isBusy) return;

    isBusy = true;
    sendBtn.disabled = true;

    addMessage(text, "user");
    chatHistory.push({
    role: "user",
    parts: [{ text: text }]
    });

    messageInput.value = "";
    messageInput.style.height = "28px";

    const loadingMessage = addMessage(
        "SutrAI soch raha hai...",
        "assistant"
    );

    try {
        showStatus("Thinking...");

        const response = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                session_id: sessionId
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "AI API failed");
        }

        const result = await response.json();

        if (!result.reply) {
            throw new Error("No AI response received");
        }

        // Replace loading message with actual AI reply
        loadingMessage.querySelector(".message-content").textContent =
            result.reply;
        chatHistory.push({
            role: "model",
            parts: [{ text: result.reply }]
        });

        // Convert AI response into voice
        await speakText(result.reply);

    } catch (error) {
        console.error("AI Chat Error:", error);

        loadingMessage.querySelector(".message-content").textContent =
            "SutrAI error: " + error.message;

        showStatus("AI response failed");

    } finally {
        isBusy = false;
        sendBtn.disabled = false;
    }
}


// Speech to Text
async function transcribeAudio(audioBlob) {
    try {
        showStatus("Transcribing audio...");

        const formData = new FormData();

        formData.append("audio_file", audioBlob, "recording.webm");

        const response = await fetch(`${API_BASE}/api/transcribe`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "STT API failed");
        }

        const result = await response.json();

        if (!result.transcript) {
            throw new Error("No transcript received");
        }

        messageInput.value = result.transcript;
        messageInput.focus();

        showStatus("Voice Input");

        messageInput.dispatchEvent(new Event("input"));
        sendMessage();

    } catch (error) {
        console.error("STT Error:", error);
        showStatus("Transcription failed");
        addMessage("Speech-to-text failed: " + error.message, "assistant");
    }
}


// Start / Stop microphone recording
async function toggleRecording() {
    if (isRecording) {
        mediaRecorder.stop();
        return;
    }

    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        audioChunks = [];

        let mimeType = "audio/webm";

        if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
            mimeType = "audio/webm;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
            mimeType = "audio/mp4";
        }

        mediaRecorder = new MediaRecorder(mediaStream, {
            mimeType: mimeType
        });

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, {
                type: mediaRecorder.mimeType
            });

            mediaStream.getTracks().forEach(track => track.stop());

            micBtn.classList.remove("recording");
            micBtn.textContent = "🎙️";

            isRecording = false;

            await transcribeAudio(audioBlob);
        };

        mediaRecorder.start();

        isRecording = true;

        micBtn.classList.add("recording");
        micBtn.textContent = "⏹";

        showStatus("Recording... Click to stop");

    } catch (error) {
        console.error("Microphone Error:", error);

        showStatus("Microphone access denied");

        addMessage(
            "Microphone access nahi mil raha. Browser permissions check karo.",
            "assistant"
        );
    }
}


// New Conversation
function newConversation() {
    chatArea.innerHTML = "";
    chatHistory = [];
    sessionId = crypto.randomUUID();
    localStorage.setItem("sutrai_session_id", sessionId);

    if (welcomeScreen) {
        chatArea.appendChild(welcomeScreen);
        welcomeScreen.style.display = "flex";
    }

    messageInput.value = "";
    audioPlayer.pause();
    audioPlayer.hidden = true;
    audioPlayer.removeAttribute("src");
}


// Event Listeners
sendBtn.addEventListener("click", (event) => {
    event.preventDefault();
    sendMessage();
});

micBtn.addEventListener("click", toggleRecording);

newChatBtn.addEventListener("click", newConversation);


// Enter to send, Shift + Enter for new line
messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});


// Auto resize textarea
messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";

    messageInput.style.height =
        Math.min(messageInput.scrollHeight, 150) + "px";
});


// Suggestion Cards
document.querySelectorAll(".suggestion-card").forEach(card => {
    card.addEventListener("click", () => {
        messageInput.value = card.dataset.prompt || "";
        messageInput.focus();
        messageInput.dispatchEvent(new Event("input"));
    });
});


// Initial status
showStatus("Voice Input");