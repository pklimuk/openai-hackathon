import threading
import pyaudio
import queue
import base64
import json
import os
import time
import sys
from websocket import create_connection, WebSocketConnectionClosedException
from dotenv import load_dotenv
import logging
from llama_index.core.tools import FunctionTool, adapt_to_async_tool, ToolSelection

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

CHUNK_SIZE = 1024
RATE = 24000
FORMAT = pyaudio.paInt16
REENGAGE_DELAY_MS = 500


INSTRUCTIONS = """
You are Einstein, the most famous physicist of all time.
You are doing a lecture on the theory of relativity. 
You are also a great teacher and can explain complex concepts in an easy to understand way.
Start your lecture with "Hello, I'm Einstein, the most famous physicist of all time!"
Render any LaTeX formulas in the text as LaTeX, and show them using the render_latex_formula tool.

Start with super short intro, then show formula E=mc^2 using the render_latex_formula tool.
"""


def render_latex_formula(formula: str) -> None:
    """
    Function that should be called any time you want to show a main latex formula.
    Use it only for main formulas, not for the explanations of this formula.
    """

    print(f"LaTeX Formula: {formula}")

tools = [adapt_to_async_tool(FunctionTool.from_defaults(fn=render_latex_formula))]

print(tools)

# exit()


class Socket:
    def __init__(self, api_key, ws_url):
        self.api_key = api_key
        self.ws_url = ws_url
        self.ws = None
        self.on_msg = None
        self._stop_event = threading.Event()
        self.recv_thread = None
        self.lock = threading.Lock()

    def connect(self):
        self.ws = create_connection(self.ws_url, header=[f"Authorization: Bearer {self.api_key}", "OpenAI-Beta: realtime=v1"])
        # logging.info("Connected to WebSocket.")
        self.recv_thread = threading.Thread(target=self._receive_messages)
        self.recv_thread.start()

    def _receive_messages(self):
        while not self._stop_event.is_set():
            try:
                if not self.ws:
                    # logging.warning("WebSocket is None, cannot receive.")
                    time.sleep(0.1)
                    continue
                message = self.ws.recv()
                if message and self.on_msg:
                    self.on_msg(json.loads(message))
            except WebSocketConnectionClosedException:
                # logging.error("WebSocket connection closed.")
                break
            except Exception as e:
                # logging.error(f"Error receiving message: {e}")
                # Attempt to reconnect or handle error appropriately
                break # Exit loop on other errors for now
        # logging.info("Exiting WebSocket receiving thread.")

    def send(self, data):
        try:
            with self.lock:
                if self.ws:
                    self.ws.send(json.dumps(data))
        except WebSocketConnectionClosedException:
            # logging.error("WebSocket connection closed.")
            pass
        except Exception as e:
            # logging.error(f"Error sending message: {e}")
            pass

    def kill(self):
        self._stop_event.set()
        if self.ws:
            try:
                # Ensure ws is not None before attempting operations
                self.ws.send_close()
                self.ws.close()
                # logging.info("WebSocket connection closed.")
            except WebSocketConnectionClosedException:
                 # logging.info("WebSocket already closed.")
                 pass
            except Exception as e:
                # logging.error(f"Error closing WebSocket: {e}")
                pass
            finally:
                self.ws = None # Ensure ws is set to None after closing attempt
        if self.recv_thread:
            self.recv_thread.join()

class AudioIO:
    def __init__(self, chunk_size=CHUNK_SIZE, rate=RATE, format=FORMAT):
        self.chunk_size = chunk_size
        self.rate = rate
        self.format = format
        self.audio_buffer = bytearray()
        self.mic_queue = queue.Queue()
        self.mic_on_at = 0
        self.mic_active = None
        self._stop_event = threading.Event()
        self.p = pyaudio.PyAudio()
        self.mic_stream = None
        self.spkr_stream = None

    def _mic_callback(self, in_data, frame_count, time_info, status):
        if time.time() > self.mic_on_at:
            if self.mic_active is not True: # Check for None or False
                # logging.info("🎙️🟢 Mic active")
                self.mic_active = True
            self.mic_queue.put(in_data)
        else:
            if self.mic_active is not False: # Check for None or True
                # logging.info("🎙️🔴 Mic suppressed")
                self.mic_active = False
        return (None, pyaudio.paContinue)

    def _spkr_callback(self, in_data, frame_count, time_info, status):
        bytes_needed = frame_count * self.p.get_sample_size(self.format) # Correct calculation
        current_buffer_size = len(self.audio_buffer)

        if current_buffer_size >= bytes_needed:
            audio_chunk = bytes(self.audio_buffer[:bytes_needed])
            self.audio_buffer = self.audio_buffer[bytes_needed:]
            self.mic_on_at = time.time() + REENGAGE_DELAY_MS / 1000
        else:
            # Pad with silence if buffer underruns
            audio_chunk = bytes(self.audio_buffer) + b"\x00" * (bytes_needed - current_buffer_size)
            self.audio_buffer.clear()

        return (audio_chunk, pyaudio.paContinue)

    def start_streams(self):
        self.mic_stream = self.p.open(
            format=self.format,
            channels=1,
            rate=self.rate,
            input=True,
            stream_callback=self._mic_callback,
            frames_per_buffer=self.chunk_size
        )
        self.spkr_stream = self.p.open(
            format=self.format,
            channels=1,
            rate=self.rate,
            output=True,
            stream_callback=self._spkr_callback,
            frames_per_buffer=self.chunk_size
        )
        self.mic_stream.start_stream()
        self.spkr_stream.start_stream()
        # logging.info("Audio streams started.")

    def stop_streams(self):
        self._stop_event.set() # Signal sending thread to stop
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            self.mic_stream = None
        if self.spkr_stream:
            self.spkr_stream.stop_stream()
            self.spkr_stream.close()
            self.spkr_stream = None
        self.p.terminate()
        # logging.info("Audio streams stopped and terminated.")

    def send_mic_audio(self, socket):
        while not self._stop_event.is_set():
            try:
                mic_chunk = self.mic_queue.get(timeout=0.1) # Add timeout to prevent blocking indefinitely
                # logging.info(f"🎤 Sending {len(mic_chunk)} bytes of audio data.")
                encoded_chunk = base64.b64encode(mic_chunk).decode("utf-8")
                socket.send({"type": "input_audio_buffer.append", "audio": encoded_chunk})
            except queue.Empty:
                continue # No data, loop again
            except Exception as e:
                # logging.error(f"Error in send_mic_audio: {e}")
                break # Exit on error
        # logging.info("Exiting microphone audio sending thread.")


    def receive_audio(self, audio_chunk):
        self.audio_buffer.extend(audio_chunk)


class Realtime:
    def __init__(self, api_key, ws_url):
        self.socket = Socket(api_key, ws_url)
        self.audio_io = AudioIO()
        self.audio_send_thread = None

    def start(self):
        self.socket.on_msg = self.handle_message
        self.socket.connect()

        # Wait briefly for connection to establish before sending
        time.sleep(1)

        self.socket.send({
            "type": "response.create",
            "response": {
                "modalities": ["audio", "text"],
                "instructions": INSTRUCTIONS,
                "tools": tools,
                "tool_choice": "auto",
            }
        })

        self.audio_send_thread = threading.Thread(target=self.audio_io.send_mic_audio, args=(self.socket,))
        self.audio_send_thread.start()

        self.audio_io.start_streams()

    def handle_message(self, message):
        event_type = message.get("type")
        logging.info(f"Received message type: {event_type}") # Can be noisy

        if event_type == "response.audio.delta":
            audio_content = base64.b64decode(message["delta"])
            self.audio_io.receive_audio(audio_content)
            # logging.info(f"Received {len(audio_content)} bytes of audio data.") # Can be noisy

        elif event_type == "response.audio_transcript.delta":
            text_delta = message.get("delta", "")
            # print(message.keys())
            # print(text_delta, end="", flush=True) # Print text delta as it arrives
            # exit() # Commenting out the exit call as it might be unintended
        elif event_type == "response.function_call_arguments.done":
            self.call_tool(message["call_id"], message['name'], json.loads(message['arguments']))


        elif event_type == "response.audio.done":
            print("AI finished speaking.")

        elif event_type == "error":
            # logging.error(f"Received error from server: {message.get('message')}")
            pass

    def call_tool(self, call_id, tool_name, tool_arguments):
        tool_selection = ToolSelection(
            tool_id="tool_id",
            tool_name=tool_name,
            tool_kwargs=tool_arguments
        )

        # avoid blocking the event loop with sync tools
        # by using asyncio.to_thread
        tool_result = await asyncio.to_thread(
            call_tool_with_selection,
            tool_selection, 
            self.tools, 
            verbose=True
        )
        await self.send_function_result(call_id, str(tool_result))


    def stop(self):
        # logging.info("Shutting down Realtime session.")
        self.audio_io.stop_streams() # Stops streams and signals send_mic_audio thread
        self.socket.kill() # Stops receiving thread and closes socket
        if self.audio_send_thread:
            self.audio_send_thread.join() # Wait for sending thread to finish


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    ws_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

    if not api_key:
        # logging.error("OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    realtime = Realtime(api_key, ws_url)

    try:
        realtime.start()
        # Keep main thread alive while other threads run
        while realtime.socket.recv_thread and realtime.socket.recv_thread.is_alive():
             time.sleep(0.1)
    except KeyboardInterrupt:
        # logging.info("KeyboardInterrupt received, shutting down...")
        pass
    except Exception as e:
        # logging.error(f"An unexpected error occurred: {e}")
        pass
    finally:
        realtime.stop()
        # logging.info("Shutdown complete.")


if __name__ == "__main__":
    main()