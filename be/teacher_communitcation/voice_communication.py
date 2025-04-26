import os
import sys

from openai import OpenAI
from elevenlabs import ElevenLabs



if sys.platform == "darwin" and os.getenv("CUSTOM_SSL") == "true":
    os.environ["REQUESTS_CA_BUNDLE"] = "/opt/homebrew/etc/openssl@3/cert.pem"
    os.environ["SSL_CERT_FILE"] = "/opt/homebrew/etc/openssl@3/cert.pem"


class VoiceCommunication:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self._elevenlabs_client = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
        )

    def transcribe_audio(self, audio_bytes: bytes, audio_format: str) -> str | None:
        """
        Transcribes audio data provided as bytes.

        Args:
            audio_bytes: The audio data as bytes.
            audio_format: The format of the audio (e.g., "mp3", "wav", "m4a").

        Returns:
            The transcribed text, or None if an error occurred.
        """
        try:
            # The API expects a file-like object or a tuple (filename, file_content)
            # Providing a filename with the correct extension helps the API determine the format.
            audio_file = (f"audio.{audio_format}", audio_bytes)
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            return transcription.text
        except Exception as e:
            print(f"An error occurred during transcription: {e}")
            return None

    def synthesize_speech(self, text_input: str) -> bytes | None:
        """
        Synthesizes speech from text input.

        Args:
            text_input: The text to synthesize.
            output_file_path: Optional path to save the synthesized audio.

        Returns:
            The synthesized audio as bytes, or None if an error occurred.
        """
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model=os.getenv("TTS_OPENAI_MODEL", "gpt-4o-mini-tts"),
                voice="verse",
                input=text_input
            ) as response:
                return response.read()
                    
        except Exception as e:
            print(f"An error occurred during speech synthesis: {e}")
            return None
        

    def synthesize_speech_elevenlabs(self, text_input: str) -> bytes | None:
        response = self._elevenlabs_client.text_to_speech.convert(
            voice_id="28FSZXcnS3rglIbvrhwd",
            output_format="mp3_44100_128",
            text=text_input,
            model_id="eleven_multilingual_v2",
        )

        audio_bytes = b""
        for chunk in response:
            audio_bytes += chunk

        return audio_bytes
