"""Configuration module for Gemini Media MCP server.

This module loads environment variables and defines default prompts
and model configurations for the image analysis service.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in environment variables. "
        "Please create a .env file with GEMINI_API_KEY='your_key'"
    )

GEMINI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]
DEFAULT_GEMINI_MODEL: str = GEMINI_MODELS[0]

DEFAULT_IMAGE_ANALYSIS_SYSTEM_PROMPT: str = """
You are an expert image analyst. Your task is to provide accurate and detailed image descriptions based on user requests.

You must respond in the following JSON format:
```json
{
  "alt_text": "Brief, informative image description suitable for accessibility alt-text.",
  "detailed_analysis": "Comprehensive image analysis based on the user's request. Describe all significant elements, colors, composition, objects, and actions in the image."
}
```

Ensure your response is valid JSON.
"""

TECHNICAL_IMAGE_ANALYSIS_SYSTEM_PROMPT: str = """
You are a technical image analyst. Analyze the image from a technical perspective: composition, color usage, typography (if present), overall aesthetics, potential use cases, etc.

Respond in JSON format:
```json
{
  "alt_text": "Brief technical image description.",
  "detailed_analysis": "Detailed technical analysis including stylistic choices, potential creation tools, target audience."
}
```

Ensure your response is valid JSON.
"""

AVAILABLE_IMAGE_ANALYSIS_PROMPTS = {
    "default": DEFAULT_IMAGE_ANALYSIS_SYSTEM_PROMPT,
    "technical": TECHNICAL_IMAGE_ANALYSIS_SYSTEM_PROMPT,
}

# --- Audio Analysis Configuration ---

SUPPORTED_AUDIO_FORMATS = {
    "audio/mpeg": "MP3",
    "audio/mp3": "MP3",
    "audio/wav": "WAV",
    "audio/x-wav": "WAV",
    "audio/aiff": "AIFF",
    "audio/x-aiff": "AIFF",
    "audio/aac": "AAC",
    "audio/aacp": "AAC",
    "audio/ogg": "OGG",
    "application/ogg": "OGG",
    "audio/flac": "FLAC",
    "audio/x-flac": "FLAC",
}

MAX_FILE_SIZE_MB = 19.5
