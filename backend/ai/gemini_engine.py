import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


# ============================================================
# LOAD PERSONADNA ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not configured."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# GEMINI GENERATION
# ============================================================

def generate_with_gemini(
    prompt: str,
) -> str:

    if not prompt or not prompt.strip():
        raise ValueError(
            "Gemini prompt cannot be empty."
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return response.text.strip()