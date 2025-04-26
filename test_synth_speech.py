from teacher_communitcation.voice_communication import VoiceCommunication
from pydub import AudioSegment
from pydub.playback import play
import io

from dotenv import load_dotenv

load_dotenv(override=True)


if __name__ == "__main__":
    voice_communication = VoiceCommunication()
    text = """
My young friends, allow me to guide you through the ideas I uncovered. I discovered that what we call gravity is not really a force pulling at a distance, but the very shape of space and time being curved by matter. Observe the two illustrations at the right: one suggests a tunnel through spacetime—what some call a “wormhole”—and the other shows how a heavy mass sinks into a stretchy sheet, drawing nearby objects inward. In my 1905 paper, I showed how moving clocks slow down and rulers contract; ten years later, I extended these ideas to include gravity itself. By picturing spacetime as a flexible fabric, we can explain why GPS satellites must adjust their clocks and how black holes trap even light. Welcome to the wondrous geometry of our universe!
"""
    audio_bytes = voice_communication.synthesize_speech_elevenlabs(text)

    with open("test_synth_speech.mp3", "wb") as f:
        f.write(audio_bytes)
    
    # if audio_bytes:
    #     # Convert bytes to AudioSegment
    #     audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    #     # Play the audio
    #     play(audio)
    # else:
    #     print("Failed to synthesize speech")
