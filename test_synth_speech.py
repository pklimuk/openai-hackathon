from teacher_communitcation.voice_communication import VoiceCommunication
from pydub import AudioSegment
from pydub.playback import play
import io


if __name__ == "__main__":
    voice_communication = VoiceCommunication()
    audio_bytes = voice_communication.synthesize_speech("Hello, how are you?")
    
    if audio_bytes:
        # Convert bytes to AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        # Play the audio
        play(audio)
    else:
        print("Failed to synthesize speech")
