import os
import sys
import time
import threading
import pyaudio
import wave
import io
from typing import Optional, List
from pydub import AudioSegment
from pydub.playback import play

from teacher_communitcation.text_communication import TextCommunication
from teacher_communitcation.voice_communication import VoiceCommunication


class Teacher:
    def __init__(
        self,
        system_prompt: str,
        api_key: Optional[str] = None,
        input_device_index: Optional[int] = None,
        rate: int = 16000,
        channels: int = 1,
        chunk: int = 1024,
        format_type: int = pyaudio.paInt16,
        threshold: float = 0.03,
        silence_timeout: float = 2.0
    ):
        self.text_communication = TextCommunication(system_prompt=system_prompt, api_key=api_key)
        self.voice_communication = VoiceCommunication(api_key=api_key)
        self.system_prompt = system_prompt
        
        # Audio recording parameters
        self.input_device_index = input_device_index
        self.rate = rate
        self.channels = channels
        self.chunk = chunk
        self.format_type = format_type
        self.threshold = threshold
        self.silence_timeout = silence_timeout
        
        self.is_recording = False
        self.audio_frames: List[bytes] = []
        self.p = pyaudio.PyAudio()
        
    def _is_silent(self, data, threshold):
        return max(abs(int.from_bytes(data[i:i+2], byteorder="little", signed=True)) 
                  for i in range(0, len(data), 2)) < threshold * 32767
    
    def _record_audio(self):
        stream = self.p.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.rate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=self.chunk
        )
        
        print("Listening... (Speak now)")
        
        self.audio_frames = []
        self.is_recording = True
        silence_start = None
        
        # Wait for sound to start
        while self.is_recording:
            try:
                data = stream.read(self.chunk, exception_on_overflow=False)
                if not self._is_silent(data, self.threshold):
                    break
                time.sleep(0.1)
            except IOError as e:
                print(f"Warning: {e}")
                continue
        
        # Record until silence for silence_timeout seconds
        while self.is_recording:
            try:
                data = stream.read(self.chunk, exception_on_overflow=False)
                self.audio_frames.append(data)
                
                if self._is_silent(data, self.threshold):
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > self.silence_timeout:
                        break
                else:
                    silence_start = None
            except IOError as e:
                print(f"Warning: {e}")
                continue
        
        stream.stop_stream()
        stream.close()
        
        print("Recording stopped")
        
        # Convert frames to bytes
        audio_data = b"".join(self.audio_frames)
        return audio_data
    
    def _save_audio_to_wav(self, audio_data, filename="temp_recording.wav"):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format_type))
            wf.setframerate(self.rate)
            wf.writeframes(audio_data)
        return filename
    
    def _play_audio(self, audio_data):
        if audio_data:
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            play(audio)
    
    def process_user_input(self):
        audio_data = self._record_audio()
        
        # Save audio temporarily for transcription
        temp_filename = self._save_audio_to_wav(audio_data)
        
        # Read the file for transcription
        with open(temp_filename, "rb") as f:
            audio_bytes = f.read()
        
        # Clean up temporary file
        try:
            os.remove(temp_filename)
        except:
            pass
        
        # Transcribe audio
        transcribed_text = self.voice_communication.transcribe_audio(audio_bytes, "wav")
        
        if transcribed_text:
            print(f"You said: {transcribed_text}")
            return transcribed_text
        else:
            print("Sorry, I couldn't understand what you said.")
            return None
    
    def respond_to_user(self, user_text):
        if not user_text:
            return
        
        # Get response from LLM
        response_text = self.text_communication.send_message(user_text)
        
        # Convert to speech
        speech_audio = self.voice_communication.synthesize_speech(response_text)
        
        if speech_audio:
            # Play the response
            self._play_audio(speech_audio)
        else:
            print("Error generating speech response")
    
    def _start_with_introduction(self):
        response_text = self.text_communication.run_initial_message()
        print(f"Teacher: {response_text}")
        
        speech_audio = self.voice_communication.synthesize_speech(response_text)
        
        if speech_audio:
            # Play the response
            self._play_audio(speech_audio)
        else:
            print("Error generating speech response")
    
    def run(self):
        try:
            # Start with an introduction based on the system prompt
            self._start_with_introduction()
            
            while True:
                user_text = self.process_user_input()
                
                if user_text and user_text.lower().strip() in ["exit", "quit", "bye"]:
                    print("Ending session. Goodbye!")
                    break
                
                if user_text:
                    self.respond_to_user(user_text)
                
        except KeyboardInterrupt:
            print("\nSession interrupted by user.")
        finally:
            self.p.terminate()
