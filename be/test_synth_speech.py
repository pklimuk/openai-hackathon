from teacher_communitcation.voice_communication import VoiceCommunication
from pydub import AudioSegment
from pydub.playback import play
import io

from dotenv import load_dotenv

load_dotenv(override=True)


if __name__ == "__main__":
    voice_communication = VoiceCommunication()


    texts = [
        "Thanks for beeing such a great audience, I am eagerly waiting for our next lecture!",
    ]

    for i, text in enumerate(texts):
        audio_bytes = voice_communication.synthesize_speech_elevenlabs(text)

        with open(f"final_{i}.mp3", "wb") as f:
            f.write(audio_bytes)
    
    # if audio_bytes:
    #     # Convert bytes to AudioSegment
    #     audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    #     # Play the audio
    #     play(audio)
    # else:
    #     print("Failed to synthesize speech")
