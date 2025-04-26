import os
import sys

from openai import OpenAI


if sys.platform == "darwin" and os.getenv("CUSTOM_SSL") == "true":
    os.environ["REQUESTS_CA_BUNDLE"] = "/opt/homebrew/etc/openssl@3/cert.pem"
    os.environ["SSL_CERT_FILE"] = "/opt/homebrew/etc/openssl@3/cert.pem"


class TextCommunication:
    def __init__(self, system_prompt: str, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.system_prompt = system_prompt
        self.history = [{"role": "system", "content": self.system_prompt}]

    def send_message(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
                messages=self.history
            )
            assistant_message = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            # Basic error handling, could be more sophisticated
            print(f"An error occurred: {e}")
            # Optionally remove the last user message if the API call failed
            # self.history.pop() 
            return "Sorry, I encountered an error trying to respond."
        
    def run_initial_message(self):
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
                messages=self.history
            )
            assistant_message = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            print(f"An error occurred: {e}")
            return "Sorry, I encountered an error trying to respond."
