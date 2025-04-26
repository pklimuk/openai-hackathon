import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from teacher_communitcation.voice_communication import VoiceCommunication
from teacher_communitcation.text_communication import TextCommunication
import base64

app = FastAPI()

# Allow all CORS (not secure, but as requested)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the voice communication client
voice_client = VoiceCommunication()


class TextToSpeechRequest(BaseModel):
    context: str
    question: str


@app.post("/synthesize-speech")
def synthesize_speech(request: TextToSpeechRequest):
    """Convert text to speech and return both answer and audio bytes (base64)"""

    print(request)

    text_client = TextCommunication(system_prompt=request.context)
    answer = text_client.send_message(request.question)
    try:
        audio_bytes = voice_client.synthesize_speech_elevenlabs(answer)
        if audio_bytes is None:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech")
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return JSONResponse(content={
            "answer": answer,
            "audio_base64": audio_base64
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/")
def root():
    return {"message": "Text-to-Speech API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
