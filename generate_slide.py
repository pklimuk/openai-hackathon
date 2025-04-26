import base64
import os
import sys

from openai import OpenAI


if sys.platform == "darwin" and os.getenv("CUSTOM_SSL") == "true":
    os.environ["REQUESTS_CA_BUNDLE"] = "/opt/homebrew/etc/openssl@3/cert.pem"
    os.environ["SSL_CERT_FILE"] = "/opt/homebrew/etc/openssl@3/cert.pem"


if __name__ == "__main__":
    client = OpenAI()

    img = client.images.generate(
        model="gpt-image-1",
        prompt="Slide for a presentation about the theory of special relativity, which shows the formula E=mc^2, and a diagram of a clock",
        n=1,
        size="1024x1024"
    )

    image_bytes = base64.b64decode(img.data[0].b64_json)
    with open("output.png", "wb") as f:
        f.write(image_bytes)