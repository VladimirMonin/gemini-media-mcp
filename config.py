"""Configuration module for Gemini Media MCP server.

This module loads environment variables and defines default prompts
and model configurations for the image analysis service.
"""

import os


def get_api_key() -> str:
    """
    Получает API-ключ Gemini из переменных окружения или файла .env.

    Приоритет:
    1. Переменная окружения `GEMINI_API_KEY`.
    2. Файл `.env` в корневом каталоге проекта (для локальной разработки).

    Returns:
        str: Найденный API-ключ.

    Raises:
        ValueError: Если API-ключ не найден ни в одном из источников.
    """
    # 1. Проверяем переменные окружения (высший приоритет)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    # 2. Пытаемся загрузить из .env (для удобства локальной разработки)
    try:
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            return api_key
    except ImportError:
        # Если dotenv не установлен, просто пропускаем этот шаг
        pass

    # 3. Если ключ не найден, вызываем ошибку
    raise ValueError(
        "Ключ GEMINI_API_KEY не найден. "
        "Пожалуйста, установите его как переменную окружения или "
        "передайте через конфигурацию клиента MCP."
    )


GEMINI_API_KEY = get_api_key()

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

# --- Audio Analysis Prompts ---

DEFAULT_AUDIO_ANALYSIS_SYSTEM_PROMPT: str = """
You are an expert audio analyst. Analyze the provided audio file and generate a structured JSON response based on the following schema.

Your response MUST be a valid JSON object that conforms to this Pydantic model:

class AudioAnalysisResponse(BaseModel):
    title: Optional[str] = "Suggested title for the audio."
    summary: Optional[str] = "Brief summary of the audio content."
    transcription: Optional[str] = "Full transcription of the audio."
    participants: Optional[list[str]] = "List of identified participants."
    hashtags: Optional[list[str]] = "Keywords or topics as hashtags."
    action_items: Optional[list[str]] = "List of action items mentioned."

- For 'title', create a concise and relevant title.
- For 'summary', provide a short overview of the main points.
- For 'transcription', provide a full and accurate text version of the speech.
- For 'participants', list the names of speakers if they can be identified.
- For 'hashtags', extract key topics as a list of strings.
- For 'action_items', list any tasks or follow-ups mentioned.

Do not include any text or explanations outside of the JSON object.
"""

AVAILABLE_AUDIO_ANALYSIS_PROMPTS = {
    "default": DEFAULT_AUDIO_ANALYSIS_SYSTEM_PROMPT,
}

# --- Audio Generation Configuration ---

OUTPUT_AUDIO_DIR = "output_audio"

# Полный каталог голосов с метаданными для выбора ИИ
GEMINI_VOICES_DATA = {
    "achernar": {"gender": "Male", "desc": "Clean, friendly, engaging, mid-range."},
    "achird": {"gender": "Female", "desc": "Young, high-pitched, breathy, friendly."},
    "algenib": {
        "gender": "Female",
        "desc": "Warm, confident, mid-range, authoritative.",
    },
    "alnilam": {"gender": "Male", "desc": "Energetic, low-mid, enthusiastic, ad-like."},
    "aoede": {
        "gender": "Female",
        "desc": "Clean, conversational, thoughtful, intelligent.",
    },
    "autonoe": {
        "gender": "Female",
        "desc": "Bright, mature, resonant, wise, audiobook style.",
    },
    "callirrhoe": {
        "gender": "Female",
        "desc": "Confident, clear, professional, energetic.",
    },
    "charon": {
        "gender": "Male",
        "desc": "Smooth, conversational, low-mid, trustworthy.",
    },
    "despina": {
        "gender": "Female",
        "desc": "Warm, approachable, clear, lifestyle ad style.",
    },
    "enceladus": {
        "gender": "Male",
        "desc": "Breathy, energetic, enthusiastic, promo style.",
    },
    "erinome": {
        "gender": "Female",
        "desc": "Professional, articulate, lower-mid, sophisticated.",
    },
    "fenrir": {"gender": "Male", "desc": "Friendly, clear, conversational, natural."},
    "gacrux": {
        "gender": "Female",
        "desc": "Smooth, confident, low-mid, authoritative.",
    },
    "iapetus": {"gender": "Male", "desc": "Friendly, mid-tone, casual, 'everyman'."},
    "kore": {
        "gender": "Female",
        "desc": "Energetic, young, high-mid, confident, bright.",
    },
    "laomedeia": {
        "gender": "Female",
        "desc": "Clear, conversational, engaging, inquisitive.",
    },
    "leda": {
        "gender": "Female",
        "desc": "Composed, professional, lower resonance, authoritative.",
    },
    "orus": {"gender": "Male", "desc": "Mature, deep, resonant, thoughtful, wise."},
    "puck": {"gender": "Male", "desc": "Clear, direct, mid-range, 'guy next door'."},
    "pulcherrima": {
        "gender": "Female",
        "desc": "Direct, bright, energetic, high-mid, youthful.",
    },
    "rasalgethi": {
        "gender": "Male",
        "desc": "Informative, conversational, inquisitive, eccentric.",
    },
    "sadachbia": {
        "gender": "Male",
        "desc": "Lively, deep, textured, cool, rebellious.",
    },
    "sadaltager": {
        "gender": "Male",
        "desc": "Knowledgeable, friendly, enthusiastic, professional.",
    },
    "schedar": {
        "gender": "Male",
        "desc": "Even, friendly, mid-tone, casual, grounded.",
    },
    "sulafat": {
        "gender": "Female",
        "desc": "Warm, confident, clear, persuasive, intelligent.",
    },
    "umbriel": {
        "gender": "Male",
        "desc": "Calm, smooth, low-mid, authoritative yet friendly.",
    },
    "vindemiatrix": {
        "gender": "Female",
        "desc": "Gentle, calm, thoughtful, low-mid, mature.",
    },
    "zephyr": {
        "gender": "Female",
        "desc": "Bright, energetic, light, youthful, positive.",
    },
    "zubenelgenubi": {
        "gender": "Male",
        "desc": "Laid-back, deep, resonant, authoritative, epic.",
    },
    "algieba": {"gender": "Male", "desc": "Calm."},
}

DEFAULT_VOICE = "Kore"
