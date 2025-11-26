# Пакет исходного кода проекта: gemini-media-mcp

## `config/mcp_config.py`

```py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class MCPServerConfig(BaseModel):
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None

class MCPClientConfig(BaseModel):
    mcp_servers: Dict[str, MCPServerConfig] = Field(..., alias="mcpServers")

    class Config:
        allow_population_by_field_name = True

```

## `config.py`

```py
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

# Get project root directory (where config.py is located)
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_AUDIO_DIR = os.path.join(_PROJECT_ROOT, "output_audio")

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


# --- GIF Animation Analysis Configuration ---

GIF_QUALITY_PRESETS = {
    "uhd": None,  # Без ресайза (3840×2160) - максимум деталей
    "fhd": 1920,  # Full HD - текст 12pt+ читается отлично (DEFAULT)
    "hd": 1280,  # HD - текст 14pt+ читается хорошо
    "balanced": 960,  # Баланс - крупный текст читается
    "economy": 768,  # Экономия - только крупный текст
}

DEFAULT_GIF_QUALITY = "fhd"  # 1080p по умолчанию
DEFAULT_GIF_MODEL = "gemini-2.5-flash"  # Flash 2.5 по умолчанию

DEFAULT_GIF_ANALYSIS_SYSTEM_PROMPT: str = """
You are analyzing an animated sequence extracted from a GIF file.

You are viewing multiple frames that represent key moments from this animation.
Your task is to analyze these frames not just as individual images, but as parts of a cohesive narrative.

Focus on:
1. **Individual Frame Content**: What is shown in each frame (UI elements, text, actions, cursor positions)
2. **Sequential Flow**: How frames connect to tell a story or demonstrate a process
3. **Overall Purpose**: What the author of this animation is trying to communicate or demonstrate
4. **Key Changes**: What changes between frames and what these changes signify

Remember: You're analyzing a continuous process, not separate images. Look for:
- Step-by-step progressions
- Cause-and-effect relationships between frames
- The intended learning outcome or message

Provide your analysis in a clear, structured format that helps understand both the details and the big picture.
"""

GIF_USER_GUIDELINES: str = """
# GIF Animation Analysis Guidelines

## Best Practices

### 1. Frame Count Selection
- **5 frames**: Short tutorials (10-30 seconds), quick demos
- **10 frames**: Medium tutorials (30-90 seconds), detailed workflows
- **15+ frames**: Long sessions (2+ minutes), complex processes

### 2. Quality Presets for Different Use Cases

**For UI/Software Tutorials (DEFAULT):**
- Quality: `fhd` (1920px) - ensures text readability
- Mode: `total` - evenly distributed key moments

**For General Animations:**
- Quality: `hd` (1280px) - balanced quality/cost
- Mode: `total` or `fps`

**For Long Sessions (budget-conscious):**
- Quality: `balanced` (960px) - economy mode
- Frame count: 10-15 max

### 3. Adding Context to Your Prompt

The default prompt understands this is an animation, but you can enhance results by adding specific context:

**Examples:**
- "This is a VS Code feature demonstration..."
- "This shows a chatbot conversation workflow..."
- "This demonstrates terminal commands execution..."
- "This is a design tool tutorial showing..."

### 4. Cost Estimation

**1080p (FHD) frames:**
- Each frame ≈ 1,500 tokens
- 5 frames ≈ 7,500 tokens
- 10 frames ≈ 15,000 tokens

**Balanced (960px) frames:**
- Each frame ≈ 1,500 tokens
- 10 frames ≈ 15,000 tokens

## Recommended Workflows

### Quick Overview
```
mode: 'total'
frame_count: 5
quality: 'fhd'
```

### Detailed Analysis
```
mode: 'total'
frame_count: 10
quality: 'fhd'
```

### Budget-Friendly
```
mode: 'total'
frame_count: 8
quality: 'balanced'
```
"""


# --- Video Analysis Configuration ---

# Video quality presets (max_dimension values)
VIDEO_QUALITY_PRESETS = {
    "uhd": 3840,  # 4K UHD
    "fhd": 1920,  # 1080p Full HD (default)
    "hd": 1280,  # 720p HD
    "sd": 720,  # SD quality
    "economy": 480,  # Low quality for economy
}

DEFAULT_VIDEO_QUALITY = "fhd"  # 1080p по умолчанию
DEFAULT_VIDEO_MODEL = "gemini-2.5-flash"  # Flash 2.5 по умолчанию

# Supported video formats (common video containers)
SUPPORTED_VIDEO_FORMATS = {
    "video/mp4": "MP4",
    "video/mpeg": "MPEG",
    "video/quicktime": "MOV",
    "video/x-msvideo": "AVI",
    "video/x-matroska": "MKV",
    "video/webm": "WEBM",
}

# Audio bitrate presets for video (kbps)
VIDEO_AUDIO_BITRATES = {
    "high": 64,  # Best quality for speech + music
    "medium": 32,  # Good for speech (default)
    "low": 24,  # Acceptable for speech only
}

DEFAULT_VIDEO_AUDIO_BITRATE = 64  # kbps

```

## `models/__init__.py`

```py
"""Data models for structured responses.

This package contains Pydantic models for image analysis responses,
audio analysis responses, and error handling.
"""

from models.analysis import AudioAnalysisResponse, ErrorResponse, ImageAnalysisResponse

__all__ = ["ImageAnalysisResponse", "ErrorResponse", "AudioAnalysisResponse"]

```

## `models/analysis.py`

```py
"""Pydantic models for structured image analysis responses.

This module defines the data models used for image analysis responses
and error handling in the Gemini Media MCP server.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ImageAnalysisResponse(BaseModel):
    """Structured response from Gemini image analysis.

    Attributes:
        alt_text: Brief description suitable for accessibility alt-text.
        detailed_analysis: Comprehensive description of image content and features.
        summary: Optional brief summary or conclusion about the image.
    """

    alt_text: str = Field(
        ..., description="Brief image description suitable for alt-text."
    )
    detailed_analysis: str = Field(
        ..., description="Detailed description of image content and features."
    )
    summary: Optional[str] = Field(
        default=None,
        description="Optional brief summary or conclusion.",
    )


class ErrorResponse(BaseModel):
    """Structured error response for API failures.

    Attributes:
        error: Human-readable error description.
        details: Additional error details if available.
        raw_response: Raw model response if format was unexpected.
    """

    error: str = Field(..., description="Error description.")
    details: Optional[str] = Field(
        default=None, description="Additional error details."
    )
    raw_response: Optional[str] = Field(
        default=None,
        description="Raw model response if format mismatch occurred.",
    )


class AudioAnalysisResponse(BaseModel):
    """Structured response from Gemini audio analysis."""

    title: Optional[str] = Field(
        default=None, description="Suggested title for the audio."
    )
    summary: Optional[str] = Field(
        default=None, description="Brief summary of the audio content."
    )
    transcription: Optional[str] = Field(
        default=None, description="Full transcription of the audio."
    )
    participants: Optional[list[str]] = Field(
        default=None, description="List of identified participants."
    )
    hashtags: Optional[list[str]] = Field(
        default=None, description="Keywords or topics as hashtags."
    )
    action_items: Optional[list[str]] = Field(
        default=None, description="List of action items mentioned."
    )
    raw_text: str = Field(..., description="Raw text response from the model.")


class VideoAnalysisResponse(BaseModel):
    """Structured response from video analysis (frames + audio)."""

    visual_summary: str = Field(
        ...,
        description="Summary of visual content across all analyzed frames.",
    )
    audio_transcription: Optional[str] = Field(
        default=None,
        description="Full transcription of speech from audio track.",
    )
    audio_description: Optional[str] = Field(
        default=None,
        description="Description of non-speech audio: music, sound effects, ambient sounds.",
    )
    combined_narrative: str = Field(
        ...,
        description="Unified narrative combining visual and audio analysis into coherent story.",
    )
    key_moments: Optional[list[str]] = Field(
        default=None,
        description="List of important events, timestamps, or turning points in the video.",
    )
    raw_text: str = Field(
        ...,
        description="Raw text response from the model.",
    )

```

## `README.MD`

```md
﻿<div align="center">

# Gemini Media MCP

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**MCP server for analyzing multimedia content using Google Gemini AI**

[English](#english)  [Русский](#русский)

</div>

---

## English

### About

Model Context Protocol (MCP) server for analyzing images, audio, and video using Google Gemini AI. Built with modular architecture for easy functionality extension.

### Current Features

- **Image Analysis** - AI-powered image descriptions
- **GIF Animation Analysis** - Frame-by-frame analysis of animated GIFs with intelligent sampling
- **Audio Analysis** - Recognition and transcription of audio files
- **Image Generation** - Create images from text and reference images
- **Audio Generation** - Multi-speaker audio from YAML scripts
- **Flexible Prompts** - Custom system prompts
- **Multiple Models** - Gemini 2.5 Flash, Pro, Flash Lite, and Image Preview
- **Privacy First** - Runs locally with your API key

### Documentation

**Getting Started:**

- [Installation Guide](docs/en/installation.md)
- [Configuration](docs/en/configuration.md)
- [Quick Start](docs/en/quick-start.md)

**Usage:**

- [Basic Usage](docs/en/usage.md)
- [Troubleshooting](docs/en/troubleshooting.md)
- [Common Issues](docs/en/common-issues.md)

---

## Русский

### О проекте

MCP (Model Context Protocol) сервер для анализа изображений, аудио и видео с помощью Google Gemini AI. Модульная архитектура для лёгкого расширения функциональности.

### Текущие возможности

- **Анализ изображений** - ИИ описания изображений
- **Анализ GIF-анимаций** - Покадровый анализ анимированных GIF с умной выборкой кадров
- **Анализ аудио** - Распознавание и транскрипция аудиофайлов
- **Генерация изображений** - Создание изображений по тексту и референсам
- **Генерация аудио** - Многоголосое аудио из YAML сценариев
- **Гибкие промпты** - Настраиваемые системные промпты
- **Несколько моделей** - Gemini 2.5 Flash, Pro и новая Flash Lite
- **Конфиденциальность** - Работает локально с вашим ключом

### Документация

**Начало работы:**

- [Установка](docs/ru/installation.md)
- [Настройка](docs/ru/configuration.md)
- [Быстрый старт](docs/ru/quick-start.md)

**Использование:**

- [Базовое использование](docs/ru/usage.md)
- [Решение проблем](docs/ru/troubleshooting.md)
- [Частые ошибки](docs/ru/common-issues.md)

---

## Quick Start / Быстрый старт

### Using Installer (Recommended)

1. **Install the package with CLI dependencies:**

    ```bash
    pip install .[cli]
    ```

2. **Run the installer:**

    ```bash
    install-gemini-mcp --gemini-api-key "your_gemini_api_key"
    ```

### Manual Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/VladimirMonin/gemini-media-mcp.git
    cd gemini-media-mcp
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure your MCP client** to pass the `GEMINI_API_KEY` environment variable. See [Client Configuration Examples](docs/en/client_examples.md).
4. **Run the server:**

    ```bash
    python server.py
    ```

---

## Project Structure

```
gemini-media-mcp/
 README.md
 docs/
    en/
    ru/
 server.py
 config.py
 models/
 modules/
 utils/
```

---

## Future Plans

- Video analysis (frame-by-frame)
- Advanced GIF processing features
- Batch media processing

---

## License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**Made with  for the MCP community**

[Report Bug](https://github.com/your-username/gemini-media-mcp/issues)  [Documentation](docs/en/)

</div>

```

## `requirements.txt`

```txt
# Core dependencies
mcp>=1.0.0
google-genai>=1.0.0
pillow>=10.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
PyYAML>=6.0.0

# Video and audio processing
imageio>=2.0.0
imageio-ffmpeg>=0.5.0
pydub>=0.25.1
audioop-lts>=0.2.1  # Required for pydub on Python 3.13+

# Testing dependencies
pytest>=7.0.0
pytest-asyncio>=0.23.0

```

## `scripts/install_server.py`

```py
import typer
from pathlib import Path
import json

app = typer.Typer()

@app.command()
def main(
    gemini_api_key: str = typer.Option(..., "--gemini-api-key", "-k", help="Gemini API Key"),
    config_path: Path = typer.Option("~/.mcp/servers_config.json", "--config-path", "-c", help="Path to MCP servers_config.json"),
):
    """
    Installs the Gemini Media MCP server configuration.
    """
    config_path = config_path.expanduser()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {"mcpServers": {}}

    server_config = {
        "command": "python",
        "args": ["-m", "server"],
        "env": {
            "GEMINI_API_KEY": gemini_api_key
        }
    }

    config["mcpServers"]["gemini-media-analyzer"] = server_config

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Gemini Media MCP server configured in {config_path}")

if __name__ == "__main__":
    app()

```

## `server.py`

```py
import logging
import os
import sys

# 1. Фикс кодировки для Windows (критично для эмодзи и кириллицы)
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# 2. НАСТРОЙКА ЛОГГЕРА: СТРОГО В STDERR
# Это самое важное изменение. Теперь все print/info летят в поток ошибок,
# оставляя основной канал чистым для JSON-сообщений протокола MCP.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # <--- Направляем логи в stderr [cite: 23]
)
logger = logging.getLogger("gemini-media-mcp")

logger.info("Starting server initialization...")

# Импорт MCP (для версии пакета mcp >= 1.0.0)
try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    logger.error(f"Critical MCP import error: {e}")
    sys.exit(1)

# Импорт инструментов
try:
    from tools.image_analyzer import analyze_image
    from tools.audio_analyzer import analyze_audio
    from tools.image_generator import generate_image
    from tools.audio_generator import (
        generate_audio_from_yaml,
        get_audio_generation_guide,
    )
    from tools.gif_analyzer import analyze_gif, get_gif_guidelines
    from tools.video_analyzer import analyze_video
except ImportError as e:
    logger.error(f"Failed to import tools: {e}")
    sys.exit(1)

# Инициализация сервера
# dependencies=["httpx"] помогает, если fastmcp пытается сам что-то догрузить
mcp = FastMCP("gemini-media-analyzer", dependencies=["httpx"])

# Регистрация инструментов
mcp.tool()(analyze_image)
logger.info(f"Tool '{analyze_image.__name__}' registered.")

mcp.tool()(analyze_audio)
mcp.tool()(generate_image)
mcp.tool()(generate_audio_from_yaml)
mcp.tool()(get_audio_generation_guide)
mcp.tool()(analyze_gif)
mcp.tool()(get_gif_guidelines)
mcp.tool()(analyze_video)

if __name__ == "__main__":
    try:
        # 3. Явный запуск транспорта stdio
        # Это стандарт для локальных CLI инструментов [cite: 30]
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Critical error during server startup: {e}")
        sys.exit(1)

```

## `tests/test_gemini_analyzer.py`

```py
import pytest
import os
import sys
import time
from pathlib import Path

# Константа таймаута между вызовами API для предотвращения rate limiting
API_CALL_TIMEOUT = 10  # секунд

# Добавляем корневую директорию проекта в sys.path, чтобы можно было импортировать модули
# Это нужно, если pytest запускается не из корня проекта
# или если структура пакетов не позволяет прямое импортирование
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Попробуем импортировать, но обернем в pytest.importorskip, если что-то пойдет не так
try:
    from config import (
        GEMINI_API_KEY,
        DEFAULT_GEMINI_MODEL,
        AVAILABLE_IMAGE_ANALYSIS_PROMPTS,
    )
    from modules.image_analysis import ImageAnalysisModule
    from utils.gemini_client import GeminiClient
    from utils.file_utils import (
        get_file_mime_type,
        is_image_valid,
        SUPPORTED_IMAGE_MIME_TYPES,
    )
except ImportError as e:
    # Если не удалось импортировать, пропустим эти тесты с сообщением об ошибке
    pytest.importorskip(
        "gemini_image_mcp_modules", reason=f"Не удалось импортировать модули: {e}"
    )


# --- Тесты для утилит ---
class TestFileUtils:
    """Тесты для утилит работы с файлами."""

    def test_get_file_mime_type_jpg(self):
        """Проверка определения MIME типа для JPG."""
        # Создаем временный файл
        temp_jpg = Path("temp_test.jpg")
        temp_jpg.write_bytes(
            b"fake jpg content"
        )  # minimal jpg header would be better for real test
        mime_type = get_file_mime_type(str(temp_jpg))
        assert mime_type == "image/jpeg"
        temp_jpg.unlink()  # Удаляем временный файл

    def test_get_file_mime_type_png(self):
        """Проверка определения MIME типа для PNG."""
        temp_png = Path("temp_test.png")
        temp_png.write_bytes(b"fake png content")
        mime_type = get_file_mime_type(str(temp_png))
        assert mime_type == "image/png"
        temp_png.unlink()

    def test_get_file_mime_type_unknown(self):
        """Проверка определения MIME типа для неизвестного файла."""
        temp_unknown = Path("temp_test.xyz")
        temp_unknown.write_text("some content")
        mime_type = get_file_mime_type(str(temp_unknown))
        assert mime_type == "application/octet-stream"
        temp_unknown.unlink()

    def test_is_image_valid_valid_jpg(self, tmp_path):
        """Проверка валидации корректного JPG файла."""
        img_file = tmp_path / "valid.jpg"
        img_file.write_bytes(b"fake jpg content")
        assert is_image_valid(str(img_file)) is True

    def test_is_image_valid_valid_png(self, tmp_path):
        """Проверка валидации корректного PNG файла."""
        img_file = tmp_path / "valid.png"
        img_file.write_bytes(b"fake png content")
        assert is_image_valid(str(img_file)) is True

    def test_is_image_valid_non_existent(self):
        """Проверка валидации несуществующего файла."""
        assert is_image_valid("non_existent_file.jpg") is False

    def test_is_image_valid_not_an_image(self, tmp_path):
        """Проверка валидации файла, не являющегося изображением."""
        text_file = tmp_path / "not_an_image.txt"
        text_file.write_text("This is not an image.")
        assert is_image_valid(str(text_file)) is False

    def test_supported_image_mime_types(self):
        """Проверка списка поддерживаемых MIME типов."""
        assert "image/jpeg" in SUPPORTED_IMAGE_MIME_TYPES
        assert "image/png" in SUPPORTED_IMAGE_MIME_TYPES
        assert "text/plain" not in SUPPORTED_IMAGE_MIME_TYPES


# --- Тесты для ImageAnalysisModule и GeminiClient (интеграционные) ---
@pytest.fixture(scope="session")
def image_analyzer():
    """Фикстура для создания экземпляра ImageAnalysisModule."""
    if not GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY не установлен. Пропускаем интеграционные тесты.")
    try:
        analyzer = ImageAnalysisModule(model_name=DEFAULT_GEMINI_MODEL)
        return analyzer
    except ValueError as e:
        pytest.skip(f"Не удалось инициализировать ImageAnalysisModule: {e}")


@pytest.fixture
def test_image_path():
    """Фикстура с путем к тестовому изображению котика."""
    # Путь относительно корня проекта
    return str(PROJECT_ROOT / "tests" / "cat.jpg")


class TestImageAnalysis:
    """Тесты для модуля анализа изображений."""

    def test_image_analyzer_initialization(self, image_analyzer):
        """Проверка инициализации ImageAnalysisModule."""
        assert image_analyzer is not None
        assert image_analyzer.model_name == DEFAULT_GEMINI_MODEL

    def test_gemini_client_initialization(self, image_analyzer):
        """Проверка инициализации GeminiClient внутри модуля."""
        assert image_analyzer.gemini_client is not None
        assert image_analyzer.gemini_client.model_name == DEFAULT_GEMINI_MODEL

    @pytest.mark.dependency(depends=["test_image_analyzer_initialization"])
    def test_analyze_image_basic(self, image_analyzer, test_image_path):
        """Базовый тест анализа изображения. Проверяем, что не возникает ошибок."""
        if not os.path.exists(test_image_path):
            pytest.skip(f"Тестовое изображение {test_image_path} не найдено.")

        time.sleep(API_CALL_TIMEOUT)  # Ждём перед вызовом API

        result = image_analyzer.analyze(
            image_path=test_image_path,
            user_prompt="Опиши, что на этом изображении.",
            system_instruction_name="default",
        )
        assert (
            "error" not in result
        ), f"Анализ изображения завершился ошибкой: {result.get('error')}"
        assert "raw_response" in result or isinstance(
            result, dict
        ), "Ответ должен быть словарем или содержать raw_response"

    @pytest.mark.dependency(depends=["test_analyze_image_basic"])
    def test_analyze_image_english_prompt(self, image_analyzer, test_image_path):
        """Тест анализа с английским промтом и проверкой 'cat'."""
        if not os.path.exists(test_image_path):
            pytest.skip(f"Тестовое изображение {test_image_path} не найдено.")

        time.sleep(API_CALL_TIMEOUT)  # Ждём перед вызовом API

        result = image_analyzer.analyze(
            image_path=test_image_path,
            user_prompt="What animal is this? Describe it briefly.",
            system_instruction_name="default",  # или "technical" если он лучше подходит
        )
        assert (
            "error" not in result
        ), f"Анализ изображения завершился ошибкой: {result.get('error')}"

        # Извлекаем текст из полей alt_text и detailed_analysis
        alt_text = result.get("alt_text", "")
        detailed_analysis = result.get("detailed_analysis", "")
        full_response_text = f"{alt_text} {detailed_analysis}".lower()

        # Проверяем наличие слова "cat" ИЛИ "кот" (модель может ответить на разных языках)
        assert (
            "cat" in full_response_text
            or "кот" in full_response_text
            or "котенок" in full_response_text
        ), f"В ответе не найдено слово 'cat' или 'кот'. Ответ: {result}"

    @pytest.mark.dependency(depends=["test_analyze_image_basic"])
    def test_analyze_image_russian_prompt(self, image_analyzer, test_image_path):
        """Тест анализа с русским промтом и проверкой 'кот'."""
        if not os.path.exists(test_image_path):
            pytest.skip(f"Тестовое изображение {test_image_path} не найдено.")

        time.sleep(API_CALL_TIMEOUT)  # Ждём перед вызовом API

        result = image_analyzer.analyze(
            image_path=test_image_path,
            user_prompt="Какое животное на этом фото? Кратко опиши.",
            system_instruction_name="default",
        )
        assert (
            "error" not in result
        ), f"Анализ изображения завершился ошибкой: {result.get('error')}"

        # Извлекаем текст из полей alt_text и detailed_analysis
        alt_text = result.get("alt_text", "")
        detailed_analysis = result.get("detailed_analysis", "")
        full_response_text = f"{alt_text} {detailed_analysis}".lower()

        # Проверяем наличие слова "кот" ИЛИ "котенок" (модель должна определить животное)
        assert (
            "кот" in full_response_text or "котенок" in full_response_text
        ), f"В ответе не найдено слово 'кот' или 'котенок'. Ответ: {result}"

    def test_analyze_image_custom_system_instruction(
        self, image_analyzer, test_image_path
    ):
        """Тест анализа с кастомной системной инструкцией."""
        if not os.path.exists(test_image_path):
            pytest.skip(f"Тестовое изображение {test_image_path} не найдено.")

        time.sleep(API_CALL_TIMEOUT)  # Ждём перед вызовом API

        custom_system_prompt = (
            "Ты — ветеринар. Опиши породу животного и его возможные болезни."
        )
        result = image_analyzer.analyze(
            image_path=test_image_path,
            user_prompt="Что это за животное?",
            system_instruction_override=custom_system_prompt,
        )
        assert (
            "error" not in result
        ), f"Анализ изображения завершился ошибкой: {result.get('error')}"

        # Извлекаем текст из полей alt_text, detailed_analysis и raw_response
        alt_text = result.get("alt_text", "")
        detailed_analysis = result.get("detailed_analysis", "")
        raw_response = result.get("raw_response", "")
        full_response_text = f"{alt_text} {detailed_analysis} {raw_response}".lower()

        # Проверим, что модель отреагировала на кастомную инструкцию
        # Ищем хотя бы одно ключевое слово из тематики ветеринарии
        # Учитываем варианты написания с "е" и "ё"
        keywords = [
            "порода",
            "болезн",
            "ветеринар",
            "здоровье",
            "кошк",
            "котен",
            "котён",
            "мейн",
        ]
        assert any(
            keyword in full_response_text for keyword in keywords
        ), f"Кастомная системная инструкция не повлияла на ответ. Ответ: {result}"


# Запуск тестов:
# В терминале, находясь в корневой директории проекта (c:\PY\gemini_image_mcp):
# pytest
# Или с более подробным выводом:
# pytest -v
# Или запустить только тесты для утилит:
# pytest tests/test_gemini_analyzer.py::TestFileUtils -v

```

## `tools/__init__.py`

```py
"""Tools for the Gemini Media MCP server."""

from .image_analyzer import analyze_image

__all__ = ["analyze_image"]

```

## `tools/audio_analyzer.py`

```py
"""Audio analysis tool for the Gemini Media MCP server."""

import json
import os

from config import (
    AVAILABLE_AUDIO_ANALYSIS_PROMPTS,
    DEFAULT_GEMINI_MODEL,
    GEMINI_MODELS,
    MAX_FILE_SIZE_MB,
    SUPPORTED_AUDIO_FORMATS,
)
from models.analysis import AudioAnalysisResponse, ErrorResponse
from utils.gemini_client import GeminiClient
from utils.logger import get_logger

logger = get_logger(__name__)


def get_system_instruction(
    name: str = "default",
    override: str | None = None,
    file_path: str | None = None,
    prompts_dict: dict = AVAILABLE_AUDIO_ANALYSIS_PROMPTS,
) -> str | None:
    """Get system instruction with priority handling.

    Priority order:
    1. File path (highest priority)
    2. Custom override
    3. Predefined instruction by name

    Args:
        name: Name of predefined system instruction.
        override: Custom system instruction string.
        file_path: Path to file with system instruction.
        prompts_dict: Dictionary containing predefined prompts.

    Returns:
        System instruction string or None if not found.

    Raises:
        FileNotFoundError: If system instruction file not found.
        IOError: If error reading system instruction file.
    """
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    if override:
        return override
    return prompts_dict.get(name)


def analyze_audio(
    audio_path: str,
    user_prompt: str = "",
    model_name: str | None = None,
    system_instruction_name: str = "default",
    system_instruction_override: str | None = None,
    system_instruction_file_path: str | None = None,
) -> AudioAnalysisResponse | ErrorResponse:
    """Analyzes an audio file using the Gemini API.

    Returns structured analysis response with title, summary, transcription,
    participants, hashtags, and action items.

    Args:
        audio_path: Absolute path to the audio file on local machine.
        user_prompt: Custom analysis request (optional).
        model_name: The Gemini model to use (e.g., "gemini-2.5-flash").
                    Defaults to the one specified in config.py.
        system_instruction_name: Name of predefined system instruction.
        system_instruction_override: Custom system instruction (overrides system_instruction_name).
        system_instruction_file_path: Path to file with system instruction (highest priority).

    Returns:
        Structured analysis response or error response.

    Raises:
        ValueError: If audio file is invalid or system instruction not found.
        FileNotFoundError: If audio file or system instruction file not found.
        IOError: If error reading files.
    """
    logger.info("=" * 80)
    logger.info(f"🎵 AUDIO ANALYSIS STARTED: {audio_path}")

    # Validate audio file exists
    if not os.path.exists(audio_path):
        logger.error(f"❌ Audio file not found: {audio_path}")
        raise FileNotFoundError(f"Audio file not found at {audio_path}")

    # Validate file size
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    logger.info(f"📁 File size: {file_size_mb:.2f} MB")
    if file_size_mb > MAX_FILE_SIZE_MB:
        logger.error(
            f"❌ File size exceeds limit: {file_size_mb:.2f} MB > {MAX_FILE_SIZE_MB} MB"
        )
        raise ValueError(
            f"File size ({file_size_mb:.2f} MB) exceeds the limit of {MAX_FILE_SIZE_MB} MB."
        )

    # Validate audio format
    import mimetypes

    mime_type, _ = mimetypes.guess_type(audio_path)
    logger.info(f"🎧 Format: {mime_type}")
    if mime_type not in SUPPORTED_AUDIO_FORMATS:
        logger.error(f"❌ Unsupported format: {mime_type}")
        raise ValueError(
            f"Unsupported audio format: {mime_type}. "
            f"Supported formats: {list(SUPPORTED_AUDIO_FORMATS.keys())}"
        )

    # Get system instruction
    try:
        system_instruction = get_system_instruction(
            name=system_instruction_name,
            override=system_instruction_override,
            file_path=system_instruction_file_path,
            prompts_dict=AVAILABLE_AUDIO_ANALYSIS_PROMPTS,
        )
    except FileNotFoundError as e:
        logger.error(f"System instruction file not found: {e}")
        raise
    except IOError as e:
        logger.error(f"Error reading system instruction file: {e}")
        raise

    # Check if system instruction exists
    if system_instruction is None and system_instruction_name:
        available = list(AVAILABLE_AUDIO_ANALYSIS_PROMPTS.keys())
        raise ValueError(
            f"Prompt '{system_instruction_name}' not found. Available: {available}"
        )

    # Select and validate model
    final_model_name = model_name or DEFAULT_GEMINI_MODEL
    if final_model_name not in GEMINI_MODELS:
        raise ValueError(
            f"Model '{final_model_name}' is not supported. "
            f"Available models: {GEMINI_MODELS}"
        )

    logger.info(
        f"📊 Parameters: model={final_model_name}, system_instruction={system_instruction_name}"
    )

    # Initialize client and perform analysis
    try:
        logger.info(
            f"🚀 Sending {file_size_mb:.2f} MB audio to Gemini ({final_model_name})..."
        )
        gemini_client = GeminiClient(model_name=final_model_name)

        # Read audio file as bytes
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        response_text = gemini_client.generate_content(
            prompt=user_prompt,
            media_bytes=audio_bytes,
            mime_type=mime_type,
            system_instruction=system_instruction,
            response_schema=AudioAnalysisResponse,
        )

        # Parse and validate response using Pydantic
        try:
            result_dict = json.loads(response_text)
            result = AudioAnalysisResponse(**result_dict)
            logger.info(f"✅ Audio analysis completed successfully for {audio_path}")
            logger.info(
                f"📈 Summary: {file_size_mb:.2f} MB audio processed with {final_model_name}"
            )
            logger.info("=" * 80)
            return result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error("=" * 80)
            return ErrorResponse(
                error="JSON parsing error",
                details=str(e),
                raw_response=response_text,
            )

    except Exception as e:
        logger.exception(
            f"❌ Failed to analyze audio with model {final_model_name}: {e}"
        )
        logger.error("=" * 80)
        return ErrorResponse(
            error="Audio analysis failed",
            details=str(e),
        )

```

## `tools/audio_generator.py`

```py
import os
import yaml
import wave
from typing import List, Dict, Any, Tuple, Optional
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_VOICES_DATA, DEFAULT_VOICE, OUTPUT_AUDIO_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"


def save_wave_file(
    filename: str,
    pcm_data: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2,
) -> None:
    """Saves PCM data to a WAV file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def _load_yaml_script(yaml_path: str) -> Dict[str, Any]:
    """Loads and validates the YAML script file."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"File not found at {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data.get("cast"):
        raise ValueError("YAML must contain a 'cast' section.")
    if not data.get("script"):
        raise ValueError("YAML must contain a 'script' section.")

    return data


def _resolve_voice_name(voice_input: str) -> str:
    """Resolves voice name to the capitalized format required by API."""
    voice_key = voice_input.lower()
    if voice_key in GEMINI_VOICES_DATA:
        return voice_key.capitalize()

    # Strict validation: Raise error if voice is not found
    raise ValueError(
        f"Voice '{voice_input}' is not a valid Gemini voice. Please check 'voices.md' for the list of available voices."
    )


def _prepare_speaker_config(
    cast: List[Dict[str, str]],
) -> Tuple[Dict[str, str], List[types.SpeakerVoiceConfig]]:
    """Prepares speaker mapping and configuration objects."""
    speaker_map = {}
    speaker_configs = []

    for actor in cast:
        name = actor.get("name")
        voice_input = actor.get("voice", DEFAULT_VOICE)
        voice_name = _resolve_voice_name(voice_input)

        speaker_map[name] = voice_name

        speaker_configs.append(
            types.SpeakerVoiceConfig(
                speaker=name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                ),
            )
        )

    return speaker_map, speaker_configs


def _generate_content_request(
    client: genai.Client,
    model: str,
    prompt: str,
    speaker_configs: List[types.SpeakerVoiceConfig],
    is_multi_speaker: bool,
) -> Any:
    """Sends the generation request to Gemini API."""

    speech_config = (
        types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_configs
            )
        )
        if is_multi_speaker
        else types.SpeechConfig(voice_config=speaker_configs[0].voice_config)
    )

    return client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=speech_config,
        ),
    )


def get_audio_generation_guide() -> str:
    """
    Returns comprehensive guide for audio generation including voice catalog and YAML examples.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)

    voices_file_path = os.path.join(base_dir, "docs", "gem", "voices.md")
    example_file_path = os.path.join(
        base_dir, "docs", "examples", "audio_script_example.yaml"
    )

    guide_content = ["# Audio Generation Guide\n"]

    if os.path.exists(voices_file_path):
        try:
            with open(voices_file_path, "r", encoding="utf-8") as f:
                voices_content = f.read()
            guide_content.append("## Voice Catalog\n")
            guide_content.append(voices_content)
            guide_content.append("\n")
        except Exception as e:
            guide_content.append(f"Error reading voices file: {e}\n")
    else:
        guide_content.append(f"Voices file not found at: {voices_file_path}\n")

    if os.path.exists(example_file_path):
        try:
            with open(example_file_path, "r", encoding="utf-8") as f:
                example_content = f.read()
            guide_content.append("## YAML Script Example\n")
            guide_content.append("Use this structure for your requests:\n")
            guide_content.append("```yaml\n")
            guide_content.append(example_content)
            guide_content.append("\n```\n")
        except Exception as e:
            guide_content.append(f"Error reading example file: {e}\n")
    else:
        guide_content.append(f"Example file not found at: {example_file_path}\n")

    return "\n".join(guide_content)


def generate_audio_from_yaml(
    yaml_path: str, model: str = DEFAULT_TTS_MODEL, output_path: Optional[str] = None
) -> str:
    """
    Generates audio from a local YAML script file using Gemini TTS.

    Args:
        yaml_path: Absolute path to the YAML file.
        model: Gemini TTS model to use.
               Default: 'gemini-2.5-flash-preview-tts' (faster, cheaper).
               Alternative: 'gemini-2.5-pro-preview-tts' (higher quality, more expensive).
               You must explicitly specify the Pro model if needed.
        output_path: Absolute path where to save the output WAV file.
                     If not provided, saves to output_audio/<script_name>.wav in project root.
    """
    try:
        # 1. Load and Validate
        data = _load_yaml_script(yaml_path)
        cast = data.get("cast", [])
        script = data.get("script", [])
        style_prompt = data.get("style_prompt", "")  # Optional style instruction

        if len(cast) > 2:
            return "Error: Gemini TTS currently supports a maximum of 2 speakers."

        if len(cast) == 0:
            return "Error: At least one speaker must be defined in 'cast'."

        # 2. Prepare Configuration
        speaker_map, speaker_configs = _prepare_speaker_config(cast)

        # 3. Prepare Prompt
        is_multi_speaker = len(cast) > 1

        if is_multi_speaker:
            # Build dialogue in format: "Speaker: text"
            # For multi-speaker, we MUST include speaker names in a conversational format
            speaker_names = " and ".join([actor.get("name") for actor in cast])

            prompt_text = f"TTS the following conversation between {speaker_names}"

            if style_prompt:
                # Add style instruction after the TTS prefix
                prompt_text += f" ({style_prompt})"

            prompt_text += ":\n\n"

            for line in script:
                sp = line.get("speaker")
                txt = line.get("text")
                if sp not in speaker_map:
                    return f"Error: Speaker '{sp}' in script is not defined in 'cast'."
                prompt_text += f"{sp}: {txt}\n"
        else:
            # Single speaker
            if style_prompt:
                # For single speaker, style prompt can be an instruction like "Say in a whisper:"
                prompt_text = f"{style_prompt}\n"
                prompt_text += " ".join([line.get("text", "") for line in script])
            else:
                prompt_text = " ".join([line.get("text", "") for line in script])

        logger.info(
            f"Generating audio. Model: {model}, Speakers: {len(cast)}, Multi-speaker: {is_multi_speaker}"
        )

        # 4. Call API
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = _generate_content_request(
            client, model, prompt_text, speaker_configs, is_multi_speaker
        )

        # 5. Save Output
        if not response.candidates:
            return "Error: No candidates returned from Gemini API."

        part = response.candidates[0].content.parts[0]
        if not part.inline_data:
            return "Error: No audio data received."

        # Determine output path
        if output_path:
            # User provided absolute path
            final_output_path = output_path
            # Ensure .wav extension
            if not final_output_path.lower().endswith(".wav"):
                final_output_path += ".wav"
            # Create directory if needed
            output_dir = os.path.dirname(final_output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
        else:
            # Default: save to project's output_audio folder
            os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(yaml_path))[0]
            final_output_path = os.path.join(OUTPUT_AUDIO_DIR, f"{base_name}.wav")

        save_wave_file(final_output_path, part.inline_data.data)

        return f"Audio generated successfully: {os.path.abspath(final_output_path)}"

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return f"Critical error: {str(e)}"

```

## `tools/gif_analyzer.py`

```py
"""GIF animation analysis tool using Google Gemini API."""

from typing import Literal, Optional
from PIL import Image

from config import (
    GIF_QUALITY_PRESETS,
    DEFAULT_GIF_QUALITY,
    DEFAULT_GIF_MODEL,
    DEFAULT_GIF_ANALYSIS_SYSTEM_PROMPT,
    GIF_USER_GUIDELINES,
)
from utils.gif_processor import (
    extract_gif_frames,
    resize_image,
    create_animation_prompt,
)
from utils.image_tokens import calculate_images_tokens, estimate_cost
from utils.gemini_client import GeminiClient
from utils.logger import get_logger

logger = get_logger(__name__)


async def analyze_gif(
    image_path: str,
    prompt: str = "Analyze this animation and describe what it demonstrates",
    mode: Literal["fps", "total", "interval"] = "total",
    gif_fps: Optional[float] = None,
    frame_count: int = 5,
    interval_sec: Optional[float] = None,
    quality: Literal["uhd", "fhd", "hd", "balanced", "economy"] = DEFAULT_GIF_QUALITY,
    model: str = DEFAULT_GIF_MODEL,
) -> dict:
    """Analyze GIF animation using Gemini AI.

    This tool extracts key frames from GIF animations and analyzes them as a cohesive sequence,
    understanding both individual frames and the overall narrative/purpose of the animation.

    Args:
        image_path: Path to GIF file (local path or URL)
        prompt: Your specific question or analysis request. The default system prompt already
                explains this is an animation, so add context like:
                - "This is a VS Code tutorial showing..."
                - "This demonstrates a chatbot conversation..."
                - "This shows terminal commands..."
        mode: Extraction strategy:
              - 'total' (RECOMMENDED): Extract fixed number of evenly distributed frames
              - 'fps': Extract frames at specified rate (frames per second)
              - 'interval': Extract frames at fixed time intervals
        gif_fps: Frames per second to extract (for 'fps' mode, e.g., 1.0 = 1 frame/sec)
        frame_count: Number of frames to extract (for 'total' mode, default: 5)
                    - 5 frames: Quick demos (10-30s)
                    - 10 frames: Detailed tutorials (30-90s)
                    - 15+ frames: Long sessions (2+ min)
        interval_sec: Time interval in seconds (for 'interval' mode, e.g., 5.0 = every 5 sec)
        quality: Image quality preset (default: 'fhd' for 1080p):
                - 'fhd' (1920px): Best for UI tutorials with text (RECOMMENDED)
                - 'hd' (1280px): Good balance for general animations
                - 'balanced' (960px): Budget-friendly for long sessions
                - 'economy' (768px): Minimal quality, lowest cost
                - 'uhd' (original): Maximum detail, highest cost
        model: Gemini model to use (default: 'gemini-2.5-flash')

    Returns:
        dict: {
            "analysis": str,           # AI analysis of the animation
            "metadata": {
                "frame_count": int,    # Number of frames analyzed
                "mode": str,           # Extraction mode used
                "quality": str,        # Quality preset used
                "estimated_tokens": int, # Approximate token usage
                "model": str,          # Model used
                "extraction_params": dict
            }
        }

    Examples:
        # Quick UI tutorial analysis (RECOMMENDED)
        result = await analyze_gif(
            "tutorial.gif",
            prompt="This is a VS Code feature demo. Describe each step.",
            frame_count=5,
            quality='fhd'
        )

        # Detailed workflow analysis
        result = await analyze_gif(
            "workflow.gif",
            prompt="Explain this design process",
            frame_count=10,
            quality='fhd'
        )

        # Budget-friendly long session
        result = await analyze_gif(
            "long_session.gif",
            prompt="Summarize this terminal session",
            frame_count=10,
            quality='balanced'
        )

        # FPS mode for time-sensitive analysis
        result = await analyze_gif(
            "animation.gif",
            mode='fps',
            gif_fps=1.0,
            quality='hd'
        )
    """
    try:
        logger.info("=" * 80)
        logger.info(f"🎬 GIF ANALYSIS STARTED: {image_path}")
        logger.info(f"📊 Parameters: mode={mode}, quality={quality}, model={model}")
        logger.info(
            f"🔧 Extraction: frame_count={frame_count}, gif_fps={gif_fps}, interval_sec={interval_sec}"
        )

        # Load GIF
        image = Image.open(image_path)

        if not getattr(image, "is_animated", False):
            logger.warning(f"❌ File is not animated: {image_path}")
            return {
                "error": "File is not an animated GIF",
                "suggestion": "Use 'analyze_image' tool for static images",
            }

        # Extract frames
        frames = extract_gif_frames(
            image,
            mode=mode,
            gif_fps=gif_fps,
            frame_count=frame_count,
            interval_sec=interval_sec,
        )

        logger.info(f"✅ Extracted {len(frames)} frames from animation")

        # Resize frames based on quality preset
        max_dimension = GIF_QUALITY_PRESETS.get(quality, 1920)
        processed_frames = [resize_image(f, max_dimension) for f in frames]

        # Calculate tokens using centralized module
        token_info = calculate_images_tokens(processed_frames)
        logger.info(f"💰 Token calculation:\n{token_info['breakdown']}")

        # Estimate cost
        cost_info = estimate_cost(token_info["total_tokens"], model)
        logger.info(
            f"💵 Estimated cost: ${cost_info['estimated_input_cost_usd']:.6f} USD "
            f"({token_info['total_tokens']:,} tokens @ {model})"
        )

        # Create extraction info for prompt
        if mode == "fps":
            fps_value = gif_fps if gif_fps else 1.0
            extraction_info = f"Extracted at {fps_value} FPS (1 frame every {1.0 / fps_value:.1f} seconds)"
        elif mode == "total":
            extraction_info = (
                f"{len(frames)} frames evenly distributed across the entire animation"
            )
        else:  # interval
            extraction_info = f"Frames extracted every {interval_sec} seconds"

        # Create enhanced prompt with system prompt
        enhanced_prompt = create_animation_prompt(
            prompt,
            len(processed_frames),
            extraction_info,
            DEFAULT_GIF_ANALYSIS_SYSTEM_PROMPT,
        )

        # Call Gemini API with multi-image method
        logger.info(f"🚀 Sending {len(processed_frames)} frames to Gemini ({model})...")
        client = GeminiClient(model_name=model)

        response_text = client.generate_content_multi_image(
            prompt=enhanced_prompt,
            images=processed_frames,  # List of PIL Images
            temperature=0.7,
        )

        logger.info(f"✅ Analysis completed successfully for {image_path}")
        logger.info(
            f"📈 Summary: {len(frames)} frames, {token_info['total_tokens']:,} tokens, "
            f"${cost_info['estimated_input_cost_usd']:.6f} USD"
        )
        logger.info("=" * 80)

        return {
            "analysis": response_text,
            "metadata": {
                "frame_count": len(frames),
                "mode": mode,
                "quality": quality,
                "tokens": token_info,
                "estimated_cost": cost_info,
                "model": model,
                "extraction_params": {
                    "gif_fps": gif_fps,
                    "frame_count": frame_count,
                    "interval_sec": interval_sec,
                },
            },
        }

    except FileNotFoundError:
        logger.error(f"❌ File not found: {image_path}")
        return {
            "error": "File not found",
            "path": image_path,
        }
    except Exception as e:
        logger.exception("GIF analysis failed")
        return {
            "error": "GIF analysis failed",
            "details": str(e),
        }


async def get_gif_guidelines() -> str:
    """Get comprehensive guidelines for GIF animation analysis.

    Returns best practices, quality recommendations, cost estimates,
    and example workflows for analyzing GIF animations.

    Returns:
        str: Formatted guidelines text
    """
    return GIF_USER_GUIDELINES

```

## `tools/image_analyzer.py`

```py
"""Image analysis tool for the Gemini Media MCP server."""

import json
from PIL import Image
from config import (
    AVAILABLE_IMAGE_ANALYSIS_PROMPTS,
    DEFAULT_GEMINI_MODEL,
    GEMINI_MODELS,
)
from models.analysis import ErrorResponse, ImageAnalysisResponse
from utils.file_utils import is_image_valid
from utils.gemini_client import GeminiClient
from utils.logger import get_logger
from utils.image_tokens import calculate_image_tokens, estimate_cost

logger = get_logger(__name__)


def get_system_instruction(
    name: str = "default", override: str | None = None, file_path: str | None = None
) -> str | None:
    """Get system instruction with priority handling.

    Priority order:
    1. File path (highest priority)
    2. Custom override
    3. Predefined instruction by name

    Args:
        name: Name of predefined system instruction.
        override: Custom system instruction string.
        file_path: Path to file with system instruction.

    Returns:
        System instruction string or None if not found.

    Raises:
        FileNotFoundError: If system instruction file not found.
        IOError: If error reading system instruction file.
    """
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    if override:
        return override
    return AVAILABLE_IMAGE_ANALYSIS_PROMPTS.get(name)


def analyze_image(
    image_path: str,
    user_prompt: str = "",
    model_name: str | None = None,
    system_instruction_name: str = "default",
    system_instruction_override: str | None = None,
    system_instruction_file_path: str | None = None,
) -> ImageAnalysisResponse | ErrorResponse:
    """Analyze images using Google Gemini API.

    Returns structured result with alt-text and detailed analysis.
    Supported formats: JPEG, PNG, GIF, WEBP, HEIC, HEIF

    Args:
        image_path: Absolute path to the image file on local machine.
        user_prompt: Custom analysis request (optional).
        model_name: The Gemini model to use (e.g., "gemini-2.5-flash").
                    Defaults to the one specified in config.py.
        system_instruction_name: Name of predefined system instruction.
        system_instruction_override: Custom system instruction (overrides system_instruction_name).
        system_instruction_file_path: Path to file with system instruction (highest priority).

    Returns:
        Structured analysis response with alt-text and detailed analysis.

    Raises:
        ValueError: If image is invalid or system instruction not found.
        FileNotFoundError: If image file or system instruction file not found.
        IOError: If error reading files.
    """
    logger.info("=" * 80)
    logger.info(f"🖼️  IMAGE ANALYSIS STARTED: {image_path}")

    # Валидация изображения
    if not is_image_valid(image_path):
        logger.error(f"❌ Invalid image format: {image_path}")
        raise ValueError(f"File is not a supported image: {image_path}")

    # Получение системной инструкции
    try:
        system_instruction = get_system_instruction(
            name=system_instruction_name,
            override=system_instruction_override,
            file_path=system_instruction_file_path,
        )
    except FileNotFoundError as e:
        logger.error(f"System instruction file not found: {e}")
        raise
    except IOError as e:
        logger.error(f"Error reading system instruction file: {e}")
        raise

    # Проверка наличия системной инструкции
    if system_instruction is None and system_instruction_name:
        available = list(AVAILABLE_IMAGE_ANALYSIS_PROMPTS.keys())
        raise ValueError(
            f"Prompt '{system_instruction_name}' not found. Available: {available}"
        )

    # Выбор и валидация модели
    final_model_name = model_name or DEFAULT_GEMINI_MODEL
    if final_model_name not in GEMINI_MODELS:
        raise ValueError(
            f"Model '{final_model_name}' is not supported. "
            f"Available models: {GEMINI_MODELS}"
        )

    logger.info(
        f"📊 Parameters: model={final_model_name}, system_instruction={system_instruction_name}"
    )

    # Calculate tokens for image
    try:
        image = Image.open(image_path)
        tokens = calculate_image_tokens(image)
        cost_info = estimate_cost(tokens, final_model_name)
        logger.info(f"💰 Token estimate: {tokens:,} tokens")
        logger.info(
            f"💵 Estimated cost: ${cost_info['estimated_input_cost_usd']:.6f} USD"
        )
    except Exception as e:
        logger.warning(f"⚠️  Could not calculate tokens: {e}")
        tokens = None
        cost_info = None

    # Инициализация клиента и анализ
    try:
        logger.info(f"🚀 Sending request to Gemini ({final_model_name})...")
        gemini_client = GeminiClient(model_name=final_model_name)
        response_text = gemini_client.generate_content(
            prompt=user_prompt,
            image_path=image_path,
            system_instruction=system_instruction,
            response_schema=ImageAnalysisResponse,
        )

        try:
            result_dict = json.loads(response_text)
            result = ImageAnalysisResponse(**result_dict)
            logger.info(f"✅ Analysis completed successfully for {image_path}")
            if tokens and cost_info:
                logger.info(
                    f"📈 Summary: {tokens:,} tokens, ${cost_info['estimated_input_cost_usd']:.6f} USD"
                )
            logger.info("=" * 80)
            return result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error("=" * 80)
            return ErrorResponse(
                error="JSON parsing error",
                details=str(e),
                raw_response=response_text,
            )

    except Exception as e:
        logger.exception(
            f"❌ Failed to analyze image with model {final_model_name}: {e}"
        )
        logger.error("=" * 80)
        return ErrorResponse(
            error="Image analysis failed",
            details=str(e),
        )

```

## `tools/image_generator.py`

```py
"""Image generation tool for the Gemini Media MCP server."""

import os
from typing import List, Optional
from PIL import Image
from io import BytesIO
from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_image(
    user_prompt: str,
    image_paths: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate image based on text prompt and optional reference images.

    Args:
        user_prompt (str): Text description for generation.
        image_paths (Optional[List[str]]): List of ABSOLUTE paths to reference images.
        output_path (Optional[str]): ABSOLUTE path for saving the generated image.

    Returns:
        str: Absolute path to the saved image.

    Raises:
        ValueError: If image generation failed.
        FileNotFoundError: If reference image file not found.
        IOError: If error saving image.
    """
    logger.info(f"Starting image generation with prompt: {user_prompt[:50]}...")
    
    # Use image generation model
    model_name = "gemini-2.5-flash-image-preview"
    
    # Create content for request
    contents = [user_prompt]
    
    # Add reference images if provided
    if image_paths:
        for image_path in image_paths:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found at path: {image_path}")
            
            try:
                img = Image.open(image_path)
                contents.append(img)
                logger.debug(f"Added reference image: {image_path}")
            except Exception as e:
                raise IOError(f"Error opening image {image_path}: {e}")

    # Initialize client and generate content
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Call generate_content and get full response object
        response = client.models.generate_content(
            model=model_name,
            contents=contents
        )
        
        # Extract image data from response
        image_part = None
        if (response.candidates and len(response.candidates) > 0 and 
            hasattr(response.candidates[0], 'content') and response.candidates[0].content and
            hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts):
            for part in response.candidates[0].content.parts:
                if (hasattr(part, 'inline_data') and part.inline_data and 
                    hasattr(part.inline_data, 'data') and part.inline_data.data):
                    image_part = part
                    break
        
        if not image_part:
            raise ValueError("Could not generate image. The API did not return image data.")
        
        # Get binary image data
        image_bytes = image_part.inline_data.data
        
        if not image_bytes:
            raise ValueError("Could not generate image. The API returned empty image data.")
        
        # Determine save path
        if output_path:
            final_path = output_path
        else:
            # If path not specified, save to current directory with default name
            final_path = "generated_image.png"
        
        # Save image
        with open(final_path, "wb") as f:
            f.write(image_bytes)
        
        absolute_path = os.path.abspath(final_path)
        logger.info(f"Image successfully generated and saved to: {absolute_path}")
        
        return absolute_path
        
    except Exception as e:
        logger.exception(f"Failed to generate image: {e}")
        raise

```

## `tools/video_analyzer.py`

```py
"""Video analysis tool for the Gemini Media MCP server.

This tool analyzes videos by extracting frames and audio, then sending
them together to Gemini API in a single multimodal request for comprehensive
analysis combining visual and audio information.
"""

import json
import os
from typing import Optional, Literal

from google import genai
from google.genai import types

from config import (
    DEFAULT_GEMINI_MODEL,
    GEMINI_API_KEY,
)
from models.analysis import VideoAnalysisResponse, ErrorResponse
from utils.media_frame_extractor import extract_frames
from utils.audio_extractor import extract_audio_from_video, estimate_audio_size
from utils.logger import get_logger

logger = get_logger(__name__)

# Gemini API inline limit (20MB for all content)
GEMINI_INLINE_LIMIT_MB = 20.0

# Default system prompt for video analysis
DEFAULT_VIDEO_SYSTEM_PROMPT = """You are analyzing a video by examining extracted frames and audio track.

**Your Task:**
1. **Visual Analysis**: Examine the sequence of frames to understand what's happening visually
2. **Audio Analysis**: Transcribe speech and describe non-speech sounds (music, effects, ambient)
3. **Combined Narrative**: Create a coherent story that integrates both visual and audio information

**Important Guidelines:**
- Frames are extracted at intervals, so consider the flow and progression between them
- Look for cause-and-effect relationships between visual and audio elements
- Identify key moments where visual and audio reinforce each other
- Note any discrepancies or interesting contrasts between what's seen and heard

Provide your analysis in a structured format that separates visual, audio, and combined insights."""


def analyze_video(
    video_path: str,
    prompt: str = "Analyze this video content, describing what you see and hear.",
    # Frame extraction modes
    frame_mode: Literal["fps", "total", "interval"] = "total",
    frame_count: Optional[int] = 10,
    fps: Optional[float] = None,
    interval_sec: Optional[float] = None,
    # Frame quality
    max_dimension: int = 1920,
    image_format: Literal["webp", "jpeg"] = "webp",
    image_quality: int = 80,
    # Audio options
    include_audio: bool = True,
    audio_bitrate: Literal[64, 32, 24] = 64,
    # Utility
    dry_run: bool = False,
    # Model selection
    model_name: str = DEFAULT_GEMINI_MODEL,
) -> str:
    """Analyze video as frames + audio in one multimodal request.

    Extracts video frames and audio track, optimizes them, and sends to Gemini API
    for comprehensive analysis. Supports dry-run mode to estimate request size
    before processing.

    Args:
        video_path: Absolute path to video file
        prompt: Analysis request prompt (default: general analysis)
        frame_mode: Frame extraction mode ('total', 'fps', 'interval')
        frame_count: Number of frames for 'total' mode (default: 10)
        fps: Frames per second for 'fps' mode (e.g., 0.5 = 1 frame every 2 sec)
        interval_sec: Interval in seconds for 'interval' mode
        max_dimension: Max dimension for frame resize (default: 1920 for 1080p)
        image_format: Frame format ('webp' or 'jpeg', default: 'webp')
        image_quality: Compression quality 1-100 (default: 80)
        include_audio: Whether to extract and analyze audio (default: True)
        audio_bitrate: Audio bitrate in kbps (64/32/24, default: 64)
        dry_run: If True, only estimate size without processing (default: False)
        model_name: Gemini model to use (default from config)

    Returns:
        JSON string with VideoAnalysisResponse or dry-run estimation

    Raises:
        FileNotFoundError: If video file not found
        ValueError: If parameters invalid or request too large
        RuntimeError: If analysis fails

    Examples:
        # Basic analysis with 30 frames
        result = analyze_video("lecture.mp4", frame_count=30)

        # Extract at 0.5 FPS (1 frame every 2 seconds)
        result = analyze_video("video.mp4", frame_mode="fps", fps=0.5)

        # Extract frame every 10 seconds, low audio bitrate
        result = analyze_video(
            "long_video.mp4",
            frame_mode="interval",
            interval_sec=10,
            audio_bitrate=32
        )

        # Dry run to check size before processing
        estimate = analyze_video("large.mp4", dry_run=True)
        # Returns: {"estimated_size_mb": 18.5, "fits_in_limit": true, ...}
    """
    logger.info("=" * 80)
    logger.info(f"🎬 VIDEO ANALYSIS STARTED: {video_path}")
    logger.info(f"Mode: {frame_mode}, Audio: {include_audio}, Dry run: {dry_run}")

    # Validate video file
    if not os.path.exists(video_path):
        logger.error(f"❌ Video file not found: {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # DRY RUN MODE: Quick estimation
    if dry_run:
        logger.info("🔍 DRY RUN: Estimating request size...")
        return _estimate_request_size(
            video_path=video_path,
            frame_mode=frame_mode,
            frame_count=frame_count,
            fps=fps,
            interval_sec=interval_sec,
            max_dimension=max_dimension,
            image_format=image_format,
            image_quality=image_quality,
            include_audio=include_audio,
            audio_bitrate=audio_bitrate,
        )

    # NORMAL MODE: Extract and analyze
    try:
        # Step 1: Extract frames
        logger.info(f"📸 Extracting frames (mode={frame_mode})...")
        frames_b64, frames_meta = extract_frames(
            source=video_path,
            mode=frame_mode,
            frame_count=frame_count,
            fps=fps,
            interval_sec=interval_sec,
            max_dimension=max_dimension,
            output_format=image_format,
            quality=image_quality,
        )

        total_size_mb = frames_meta["total_size_mb"]
        logger.info(
            f"✅ Frames: {frames_meta['frame_count']} @ {frames_meta['resolution']}, "
            f"size: {total_size_mb:.2f} MB"
        )

        # Step 2: Extract audio (if requested)
        audio_data = None
        if include_audio:
            logger.info(f"🎵 Extracting audio (bitrate={audio_bitrate} kbps)...")
            audio_data = extract_audio_from_video(
                video_path=video_path, bitrate=audio_bitrate, dry_run=False
            )
            audio_size_mb = audio_data["size_mb"]
            total_size_mb += audio_size_mb
            logger.info(
                f"✅ Audio: {audio_data['duration_sec']}s, size: {audio_size_mb:.2f} MB"
            )
        else:
            logger.info("⏭️  Skipping audio extraction (include_audio=False)")

        # Step 3: Check total size
        logger.info(f"📊 Total request size: {total_size_mb:.2f} MB")
        if total_size_mb > GEMINI_INLINE_LIMIT_MB:
            logger.error(
                f"❌ Request too large: {total_size_mb:.2f} MB > {GEMINI_INLINE_LIMIT_MB} MB"
            )
            raise ValueError(
                f"Request size ({total_size_mb:.2f} MB) exceeds Gemini inline limit "
                f"({GEMINI_INLINE_LIMIT_MB} MB). Try reducing frame_count, using lower "
                f"audio_bitrate, or smaller max_dimension."
            )

        usage_percent = (total_size_mb / GEMINI_INLINE_LIMIT_MB) * 100
        logger.info(f"✅ Size check passed ({usage_percent:.1f}% of limit)")

        # Step 4: Build multimodal request
        logger.info("🔨 Building multimodal request...")
        contents = _build_multimodal_contents(
            prompt=prompt,
            frames_b64=frames_b64,
            image_format=image_format,
            audio_data=audio_data,
        )

        # Step 5: Send to Gemini API
        logger.info(f"🚀 Sending to Gemini API (model={model_name})...")
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=DEFAULT_VIDEO_SYSTEM_PROMPT,
                temperature=0.4,
                response_mime_type="application/json",
                response_schema=VideoAnalysisResponse,
            ),
        )

        # Step 6: Parse response
        raw_text = response.text
        logger.info(f"📥 Received response ({len(raw_text)} chars)")

        try:
            parsed = json.loads(raw_text)
            # Add raw_text to response
            parsed["raw_text"] = raw_text

            # Validate with Pydantic
            validated_response = VideoAnalysisResponse(**parsed)
            result_json = validated_response.model_dump_json(indent=2)

            logger.info("✅ VIDEO ANALYSIS COMPLETE")
            logger.info("=" * 80)

            return result_json

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            error_response = ErrorResponse(
                error="Invalid JSON response from Gemini API",
                details=str(e),
                raw_response=raw_text,
            )
            return error_response.model_dump_json(indent=2)

        except Exception as e:
            logger.error(f"Failed to validate response: {e}")
            error_response = ErrorResponse(
                error="Response validation failed",
                details=str(e),
                raw_response=raw_text,
            )
            return error_response.model_dump_json(indent=2)

    except (FileNotFoundError, ValueError):
        raise
    except Exception as e:
        logger.exception(f"Video analysis failed: {e}")
        raise RuntimeError(f"Video analysis failed: {e}")


def _estimate_request_size(
    video_path: str,
    frame_mode: str,
    frame_count: Optional[int],
    fps: Optional[float],
    interval_sec: Optional[float],
    max_dimension: int,
    image_format: str,
    image_quality: int,
    include_audio: bool,
    audio_bitrate: int,
) -> str:
    """Estimate request size without processing (dry-run mode).

    Returns JSON with size estimation and recommendations.
    """
    # Get audio metadata for duration
    from utils.audio_extractor import get_audio_metadata

    try:
        audio_meta = get_audio_metadata(video_path)
        duration_sec = audio_meta["duration_sec"]
    except Exception as e:
        logger.warning(f"Could not get audio metadata: {e}")
        duration_sec = 0.0

    # Estimate frames size (rough calculation)
    # Average frame size depends on format and quality
    if image_format == "webp":
        if max_dimension >= 1920:  # 1080p
            avg_frame_kb = 100 if image_quality >= 80 else 70
        elif max_dimension >= 1280:  # 720p
            avg_frame_kb = 50 if image_quality >= 80 else 35
        else:  # 480p and below
            avg_frame_kb = 25 if image_quality >= 80 else 18
    else:  # JPEG
        if max_dimension >= 1920:
            avg_frame_kb = 130 if image_quality >= 80 else 90
        elif max_dimension >= 1280:
            avg_frame_kb = 65 if image_quality >= 80 else 45
        else:
            avg_frame_kb = 35 if image_quality >= 80 else 25

    # Calculate frame count based on mode
    if frame_mode == "total":
        est_frame_count = frame_count or 10
    elif frame_mode == "fps":
        est_frame_count = int(duration_sec * (fps or 1.0))
    elif frame_mode == "interval":
        est_frame_count = int(duration_sec / (interval_sec or 10.0))
    else:
        est_frame_count = 10

    frames_size_mb = (est_frame_count * avg_frame_kb) / 1024

    # Estimate audio size
    audio_size_mb = 0.0
    if include_audio and duration_sec > 0:
        audio_size_mb = estimate_audio_size(duration_sec, audio_bitrate)

    # Total size
    total_size_mb = frames_size_mb + audio_size_mb
    fits_in_limit = total_size_mb < GEMINI_INLINE_LIMIT_MB
    usage_percent = (total_size_mb / GEMINI_INLINE_LIMIT_MB) * 100

    # Build recommendation
    if fits_in_limit:
        if usage_percent < 50:
            recommendation = f"Safe to send ({usage_percent:.0f}% of {GEMINI_INLINE_LIMIT_MB} MB limit)"
        elif usage_percent < 75:
            recommendation = f"Good fit ({usage_percent:.0f}% of limit)"
        else:
            recommendation = (
                f"Close to limit ({usage_percent:.0f}%), consider optimizing"
            )
    else:
        exceed_mb = total_size_mb - GEMINI_INLINE_LIMIT_MB
        recommendation = f"❌ Exceeds limit by {exceed_mb:.1f} MB! Reduce frame_count or audio_bitrate"

    result = {
        "estimated_size_mb": round(total_size_mb, 2),
        "fits_in_limit": fits_in_limit,
        "usage_percent": round(usage_percent, 1),
        "frames": {
            "count": est_frame_count,
            "mode": frame_mode,
            "resolution": f"~{max_dimension}p",
            "format": image_format,
            "size_mb": round(frames_size_mb, 2),
        },
        "audio": {
            "duration_sec": round(duration_sec, 1),
            "bitrate_kbps": audio_bitrate if include_audio else 0,
            "size_mb": round(audio_size_mb, 2),
        }
        if include_audio
        else None,
        "recommendation": recommendation,
    }

    logger.info(f"📊 Dry-run estimation: {total_size_mb:.2f} MB ({recommendation})")

    return json.dumps(result, indent=2)


def _build_multimodal_contents(
    prompt: str,
    frames_b64: list[str],
    image_format: str,
    audio_data: Optional[dict],
) -> list:
    """Build multimodal contents array for Gemini API.

    Args:
        prompt: User prompt
        frames_b64: List of base64-encoded frames
        image_format: 'webp' or 'jpeg'
        audio_data: Audio data dict with 'base64' and 'mime_type' (or None)

    Returns:
        List of content parts for Gemini API
    """
    contents = []

    # Add text prompt first
    contents.append(prompt)

    # Add all frames
    mime_type = f"image/{image_format}"
    for i, frame_b64 in enumerate(frames_b64, 1):
        contents.append(types.Part.from_bytes(data=frame_b64, mime_type=mime_type))

    logger.info(f"Added {len(frames_b64)} frames to request")

    # Add audio if available
    if audio_data:
        audio_b64 = audio_data["base64"]
        audio_mime = audio_data["mime_type"]
        contents.append(types.Part.from_bytes(data=audio_b64, mime_type=audio_mime))
        logger.info(f"Added audio to request ({audio_data['duration_sec']}s)")

    return contents

```

## `utils/__init__.py`

```py
"""Utility modules for the MCP server.

This package contains utility modules for file handling, API clients,
and logging configuration.
"""

from utils.file_utils import (
    get_file_mime_type,
    is_image_valid,
    SUPPORTED_IMAGE_MIME_TYPES,
)
from utils.gemini_client import GeminiClient
from utils.logger import get_logger

__all__ = [
    "get_file_mime_type",
    "is_image_valid",
    "SUPPORTED_IMAGE_MIME_TYPES",
    "GeminiClient",
    "get_logger",
]

```

## `utils/audio_extractor.py`

```py
"""Audio extraction and conversion utilities for video analysis.

This module provides functionality to extract audio tracks from video files
and convert them to optimized Vorbis mono format with configurable bitrates.
All processing is done in-memory without creating temporary files.
"""

import base64
import io
import os
from typing import Optional, Literal
from pydub import AudioSegment
from utils.logger import get_logger

logger = get_logger(__name__)


def estimate_audio_size(duration_sec: float, bitrate: int = 64) -> float:
    """Calculate estimated audio file size without processing.

    Args:
        duration_sec: Audio duration in seconds
        bitrate: Bitrate in kbps (default: 64)

    Returns:
        Estimated size in MB

    Examples:
        >>> estimate_audio_size(600, 64)  # 10 minutes at 64 kbps
        4.8
        >>> estimate_audio_size(1800, 32)  # 30 minutes at 32 kbps
        7.2
        >>> estimate_audio_size(1800, 24)  # 30 minutes at 24 kbps
        5.4
    """
    # Formula: (duration_sec * bitrate_kbps * 1000 bits/kbit) / 8 bits/byte
    size_bytes = (duration_sec * bitrate * 1000) / 8
    size_mb = size_bytes / (1024 * 1024)
    return round(size_mb, 2)


def extract_audio_from_video(
    video_path: str,
    bitrate: Literal[64, 32, 24] = 64,
    max_duration_sec: Optional[int] = None,
    dry_run: bool = False,
) -> dict:
    """Extract and convert audio track from video file.

    Extracts audio in-memory and converts to mono Vorbis (OGG) format
    for optimal compression and Gemini API compatibility.

    Args:
        video_path: Path to video file
        bitrate: Output bitrate in kbps (64/32/24, default: 64)
        max_duration_sec: Maximum duration to extract (None = full audio)
        dry_run: If True, only calculate size without processing

    Returns:
        Dictionary with audio data:
        {
            'base64': str,           # Only if dry_run=False
            'mime_type': 'audio/ogg',
            'duration_sec': float,
            'size_mb': float,
            'bitrate': int,
            'channels': 1  # mono
        }

    Raises:
        FileNotFoundError: If video file not found
        RuntimeError: If audio extraction fails

    Examples:
        # Extract full audio at 64 kbps
        audio = extract_audio_from_video("video.mp4", bitrate=64)
        print(f"Size: {audio['size_mb']:.2f} MB")

        # Extract first 5 minutes at 32 kbps
        audio = extract_audio_from_video("lecture.mp4", bitrate=32, max_duration_sec=300)

        # Dry run to estimate size
        audio = extract_audio_from_video("long.mp4", dry_run=True)
        print(f"Estimated: {audio['size_mb']:.2f} MB")
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")

    logger.info(f"Extracting audio from video: {video_path}")
    logger.info(f"Settings: bitrate={bitrate} kbps, mono, Vorbis (OGG)")

    try:
        # Load audio from video using pydub
        # pydub will use ffmpeg under the hood (from imageio-ffmpeg)
        logger.info("Loading audio track from video...")
        audio = AudioSegment.from_file(video_path)

        # Get original duration
        duration_ms = len(audio)
        duration_sec = duration_ms / 1000.0
        logger.info(f"Original audio: {duration_sec:.1f}s, {audio.channels} channels")

        # Trim if needed
        if max_duration_sec and duration_sec > max_duration_sec:
            logger.info(f"Trimming audio to {max_duration_sec}s")
            audio = audio[: max_duration_sec * 1000]
            duration_sec = max_duration_sec

        # If dry run, just estimate size
        if dry_run:
            estimated_size = estimate_audio_size(duration_sec, bitrate)
            logger.info(f"🔍 Dry run: estimated size {estimated_size:.2f} MB")

            return {
                "mime_type": "audio/ogg",
                "duration_sec": round(duration_sec, 1),
                "size_mb": estimated_size,
                "bitrate": bitrate,
                "channels": 1,
            }

        # Convert to mono
        if audio.channels > 1:
            logger.info("Converting stereo to mono...")
            audio = audio.set_channels(1)

        # Export to Vorbis (OGG) format in-memory
        logger.info(f"Converting to Vorbis mono {bitrate} kbps...")
        buffer = io.BytesIO()

        audio.export(
            buffer,
            format="ogg",
            codec="libvorbis",
            bitrate=f"{bitrate}k",
            parameters=["-ac", "1"],  # Force mono
        )

        # Get size and base64
        buffer.seek(0)
        audio_bytes = buffer.getvalue()
        actual_size_mb = len(audio_bytes) / (1024 * 1024)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        logger.info(
            f"✅ Audio extracted: {duration_sec:.1f}s, "
            f"{actual_size_mb:.2f} MB, "
            f"{bitrate} kbps mono"
        )

        return {
            "base64": audio_b64,
            "mime_type": "audio/ogg",
            "duration_sec": round(duration_sec, 1),
            "size_mb": round(actual_size_mb, 3),
            "bitrate": bitrate,
            "channels": 1,
        }

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to extract audio: {e}")
        raise RuntimeError(f"Audio extraction failed: {e}")


def get_audio_metadata(video_path: str) -> dict:
    """Get audio metadata without extracting full audio.

    Fast metadata retrieval for planning purposes.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with metadata:
        {
            'duration_sec': float,
            'channels': int,
            'sample_rate': int,
            'has_audio': bool
        }

    Raises:
        FileNotFoundError: If video file not found
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    try:
        # Load just the first second to get metadata
        audio = AudioSegment.from_file(video_path, duration=1.0)

        # Get full file duration by loading without limit
        full_audio = AudioSegment.from_file(video_path)
        duration_sec = len(full_audio) / 1000.0

        return {
            "duration_sec": round(duration_sec, 1),
            "channels": audio.channels,
            "sample_rate": audio.frame_rate,
            "has_audio": True,
        }

    except Exception as e:
        logger.warning(f"Could not extract audio metadata: {e}")
        return {
            "duration_sec": 0.0,
            "channels": 0,
            "sample_rate": 0,
            "has_audio": False,
        }

```

## `utils/file_utils.py`

```py
"""File handling utilities for image validation and MIME type detection.

This module provides utilities for working with image files, including
MIME type detection, file validation, and binary file reading operations.
"""

import mimetypes
import os
from pathlib import Path
from typing import List

SUPPORTED_IMAGE_MIME_TYPES: List[str] = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
]


def get_file_mime_type(file_path: str) -> str | None:
    """Detect MIME type of a file.

    Attempts to determine MIME type using mimetypes library,
    with fallback to extension-based detection.

    Args:
        file_path: Path to the file to analyze.

    Returns:
        MIME type string, or 'application/octet-stream' for unknown types.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type

    file_extension = Path(file_path).suffix.lower()
    extension_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".heic": "image/heic",
        ".heif": "image/heif",
    }

    return extension_map.get(file_extension, "application/octet-stream")


def read_file_as_bytes(file_path: str) -> bytes:
    """Read file contents as bytes.

    Args:
        file_path: Path to the file to read.

    Returns:
        File contents as bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If an error occurs during file reading.
    """
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"File not found: {file_path}") from exc
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}") from e


def is_image_valid(file_path: str) -> bool:
    """Validate if a file is a supported image type.

    Args:
        file_path: Path to the file to validate.

    Returns:
        True if the file exists and is a supported image type, False otherwise.
    """
    if not os.path.exists(file_path):
        return False
    if not os.path.isfile(file_path):
        return False
    mime_type = get_file_mime_type(file_path)
    return mime_type in SUPPORTED_IMAGE_MIME_TYPES

```

## `utils/gemini_client.py`

```py
"""Google Gemini API client for image analysis.

This module provides a wrapper around the Google Gemini API for analyzing
images with custom prompts and system instructions.
"""

import json
from typing import Optional, Union, List

from PIL import Image
from google.genai import types, Client

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL
from models.analysis import ImageAnalysisResponse, ErrorResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Client wrapper for Google Gemini API interactions.

    Provides methods for analyzing images using Google's Gemini models
    with support for custom prompts and system instructions.

    Attributes:
        model_name: The name of the Gemini model to use.
        client: The configured Google Gemini API client.
    """

    def __init__(self, model_name: str = DEFAULT_GEMINI_MODEL):
        """Initialize the Gemini client.

        Args:
            model_name: Name of the Gemini model to use.
        """
        self.model_name = model_name
        self.client = Client(api_key=GEMINI_API_KEY)
        logger.info(f"Initialized GeminiClient with model: {model_name}")

    def generate_content(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        media_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        system_instruction: Optional[str] = None,
        response_schema=None,
    ) -> str:
        """Generate content with media using the Gemini API.

        Args:
            prompt: The text prompt for the model.
            image_path: Optional path to an image file.
            media_bytes: Optional media data in bytes.
            mime_type: The MIME type of the media_bytes.
            system_instruction: Optional system instruction for the model.
            response_schema: Optional Pydantic model for structured response.

        Returns:
            The raw text response from the model.
        """
        try:
            media_part = None
            if image_path:
                media_part = Image.open(image_path)
                logger.debug(f"Loaded image: {image_path}")
            elif media_bytes and mime_type:
                media_part = types.Part.from_bytes(
                    data=media_bytes, mime_type=mime_type
                )
                logger.debug(f"Loaded media bytes with MIME type: {mime_type}")

            contents = [prompt, media_part] if media_part else [prompt]

            config_params = {
                "temperature": 0.7,
                "max_output_tokens": 4096,
                "safety_settings": [
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                ],
            }

            if system_instruction:
                config_params["system_instruction"] = system_instruction
            if response_schema:
                config_params["response_mime_type"] = "application/json"
                # Pass Pydantic model directly - library handles conversion
                config_params["response_schema"] = response_schema

            config = types.GenerateContentConfig(**config_params)

            logger.info("Sending content generation request to Gemini.")
            response = self.client.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )

            if hasattr(response, "text"):
                return response.text or ""

            # Handle cases where the response might be blocked
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                feedback = response.prompt_feedback
                if hasattr(feedback, "block_reason") and feedback.block_reason:
                    logger.warning(f"Request blocked: {feedback.block_reason}")
                    raise ValueError(
                        f"Request blocked by safety filters: {feedback.block_reason}"
                    )

            raise ValueError("Failed to get a valid response from Gemini model.")

        except Exception as e:
            logger.exception(f"Unexpected error during content generation: {e}")
            raise

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text based on a prompt.

        Args:
            prompt: The text prompt for generation.
            **kwargs: Additional arguments for the API call.

        Returns:
            Generated text response.
        """
        logger.debug(f"Generating text for prompt: {prompt[:50]}...")
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt, **kwargs
        )
        return response.text or ""

    def generate_content_multi_image(
        self,
        prompt: str,
        images: List[Union[str, Image.Image, types.Part]],
        system_instruction: Optional[str] = None,
        response_schema=None,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
    ) -> str:
        """Generate content with multiple images using Gemini API.

        Supports mixing:
        - File paths (str)
        - PIL Image objects
        - types.Part objects (for File API references)

        Args:
            prompt: Text prompt for analysis
            images: List of images in various formats
            system_instruction: Optional system instruction
            response_schema: Optional Pydantic model for structured output
            temperature: Sampling temperature (0.0-2.0)
            max_output_tokens: Maximum tokens in response

        Returns:
            Text response from model

        Examples:
            # Mix of formats
            response = client.generate_content_multi_image(
                prompt="Compare these images",
                images=[
                    "path/to/image1.jpg",  # file path
                    pil_image,              # PIL Image
                    uploaded_file_part      # types.Part from File API
                ]
            )
        """
        try:
            # Convert all images to appropriate format
            content_parts = [prompt]

            for i, img in enumerate(images):
                if isinstance(img, str):
                    # File path - load as PIL Image
                    pil_img = Image.open(img)
                    content_parts.append(pil_img)
                    logger.debug(f"Image {i + 1}: Loaded from path {img}")

                elif isinstance(img, Image.Image):
                    # Already PIL Image
                    content_parts.append(img)
                    logger.debug(f"Image {i + 1}: PIL Image {img.size}")

                elif isinstance(img, types.Part):
                    # File API reference
                    content_parts.append(img)
                    logger.debug(f"Image {i + 1}: File API Part")

                else:
                    raise ValueError(f"Unsupported image type: {type(img)}")

            # Configure request
            config_params = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "safety_settings": [
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                ],
            }

            if system_instruction:
                config_params["system_instruction"] = system_instruction
            if response_schema:
                config_params["response_mime_type"] = "application/json"
                config_params["response_schema"] = response_schema

            config = types.GenerateContentConfig(**config_params)

            logger.info(f"Sending {len(images)} images to Gemini ({self.model_name})")
            response = self.client.models.generate_content(
                model=self.model_name, contents=content_parts, config=config
            )

            if hasattr(response, "text"):
                return response.text or ""

            # Handle blocked responses
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                feedback = response.prompt_feedback
                if hasattr(feedback, "block_reason") and feedback.block_reason:
                    logger.warning(f"Request blocked: {feedback.block_reason}")
                    raise ValueError(
                        f"Request blocked by safety filters: {feedback.block_reason}"
                    )

            raise ValueError("Failed to get a valid response from Gemini model.")

        except Exception as e:
            logger.exception(f"Error in multi-image content generation: {e}")
            raise

```

## `utils/gif_processor.py`

```py
"""GIF animation processing utilities for Gemini API."""

from typing import Optional, Literal
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_gif_frames(
    image: Image.Image,
    mode: Literal["fps", "total", "interval"] = "total",
    gif_fps: Optional[float] = None,
    frame_count: Optional[int] = None,
    interval_sec: Optional[float] = None,
) -> list[Image.Image]:
    """Extract frames from animated GIF using different strategies.

    Args:
        image: PIL Image object (animated GIF)
        mode: Extraction mode ('fps', 'total', 'interval')
        gif_fps: Frames per second to extract (for 'fps' mode)
        frame_count: Total number of frames to extract (for 'total' mode)
        interval_sec: Time interval in seconds (for 'interval' mode)

    Returns:
        List of extracted frames as PIL Images

    Raises:
        ValueError: If required parameters for mode are missing

    Examples:
        # Mode 1: Extract at 1 FPS
        frames = extract_gif_frames(gif, mode='fps', gif_fps=1.0)

        # Mode 2: Extract exactly 5 frames (evenly distributed)
        frames = extract_gif_frames(gif, mode='total', frame_count=5)

        # Mode 3: Extract frame every 5 seconds
        frames = extract_gif_frames(gif, mode='interval', interval_sec=5.0)
    """
    if not getattr(image, "is_animated", False):
        logger.info("Image is not animated, returning single frame")
        return [_convert_frame(image)]

    # Get GIF metadata
    gif_duration_ms = image.info.get("duration", 100)  # milliseconds per frame
    total_frames = getattr(image, "n_frames", 1)
    total_duration_sec = (gif_duration_ms * total_frames) / 1000.0
    native_fps = 1000.0 / gif_duration_ms

    logger.info(
        f"GIF info: {total_frames} frames, {total_duration_sec:.1f}s, {native_fps:.1f} fps"
    )

    # Determine frame indices based on mode
    if mode == "fps":
        if gif_fps is None:
            raise ValueError("Parameter 'gif_fps' required for mode 'fps'")
        frame_indices = _get_fps_indices(total_frames, native_fps, gif_fps)

    elif mode == "total":
        if frame_count is None:
            raise ValueError("Parameter 'frame_count' required for mode 'total'")
        frame_indices = _get_total_indices(total_frames, frame_count)

    elif mode == "interval":
        if interval_sec is None:
            raise ValueError("Parameter 'interval_sec' required for mode 'interval'")
        frame_indices = _get_interval_indices(
            total_frames, total_duration_sec, interval_sec
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

    logger.info(f"Extracting {len(frame_indices)} frames using mode '{mode}'")

    # Extract frames at calculated indices
    frames = []
    for idx in frame_indices:
        image.seek(idx)
        frame = image.copy()
        frames.append(_convert_frame(frame))

    return frames


def _get_fps_indices(
    total_frames: int, native_fps: float, target_fps: float
) -> list[int]:
    """Calculate frame indices for FPS mode.

    Args:
        total_frames: Total number of frames in GIF
        native_fps: GIF's native frame rate
        target_fps: Desired extraction rate

    Returns:
        List of frame indices to extract
    """
    frame_step = max(1, int(native_fps / target_fps))
    return list(range(0, total_frames, frame_step))


def _get_total_indices(total_frames: int, frame_count: int) -> list[int]:
    """Calculate evenly distributed frame indices for TOTAL mode.

    Args:
        total_frames: Total number of frames in GIF
        frame_count: Desired number of frames to extract

    Returns:
        List of evenly distributed frame indices

    Examples:
        # 30 frames, want 5
        _get_total_indices(30, 5)  # [0, 6, 12, 18, 24]

        # 180 frames (3 min at 1fps), want 5
        _get_total_indices(180, 5)  # [0, 36, 72, 108, 144]
    """
    if frame_count >= total_frames:
        return list(range(total_frames))

    # Evenly distribute frames
    step = total_frames / frame_count
    indices = [int(i * step) for i in range(frame_count)]

    return indices


def _get_interval_indices(
    total_frames: int, total_duration_sec: float, interval_sec: float
) -> list[int]:
    """Calculate frame indices for INTERVAL mode.

    Args:
        total_frames: Total number of frames in GIF
        total_duration_sec: Total duration in seconds
        interval_sec: Time interval in seconds

    Returns:
        List of frame indices at specified intervals
    """
    if total_duration_sec <= 0:
        return [0]

    frames_per_sec = total_frames / total_duration_sec
    frame_step = max(1, int(interval_sec * frames_per_sec))

    return list(range(0, total_frames, frame_step))


def _convert_frame(frame: Image.Image) -> Image.Image:
    """Convert frame to compatible mode for Gemini API.

    Args:
        frame: PIL Image frame

    Returns:
        Converted frame in compatible mode
    """
    # Convert palette mode (P) and other incompatible modes to RGB
    if frame.mode in ("P", "LA", "PA"):
        return frame.convert("RGB")
    elif frame.mode == "RGBA":
        return frame  # Keep RGBA - it's supported
    elif frame.mode not in ("RGB", "L"):
        return frame.convert("RGB")
    return frame


def resize_image(image: Image.Image, max_dimension: Optional[int]) -> Image.Image:
    """Resize image maintaining aspect ratio.

    Args:
        image: PIL Image object
        max_dimension: Maximum size for longest side (None = no resize)

    Returns:
        Resized image
    """
    if max_dimension is None:
        return image

    width, height = image.size
    max_current = max(width, height)

    if max_current <= max_dimension:
        return image

    scale = max_dimension / max_current
    new_width = int(width * scale)
    new_height = int(height * scale)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def create_animation_prompt(
    user_prompt: str, frame_count: int, extraction_info: str, system_prompt: str
) -> str:
    """Create context-aware prompt for GIF animation analysis.

    Args:
        user_prompt: User's original prompt
        frame_count: Number of extracted frames
        extraction_info: Description of extraction method
        system_prompt: System prompt explaining animation analysis approach

    Returns:
        Enhanced prompt with animation context
    """
    context_prompt = f"""{system_prompt}

**Animation Details:**
- Total frames analyzed: {frame_count}
- Extraction method: {extraction_info}

**User's Specific Request:**
{user_prompt}

Please provide your analysis based on the frames and the user's request above."""

    return context_prompt

```

## `utils/image_tokens.py`

```py
"""Token calculation utilities for Gemini API media processing.

Based on official Gemini documentation:
https://ai.google.dev/gemini-api/docs/image-understanding#token-calculation
"""

from typing import List
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_image_tokens(image: Image.Image) -> int:
    """Calculate token count for a single image.

    Token calculation logic based on Gemini documentation:
    - Images ≤384px (both dimensions): 258 tokens
    - Larger images: Tiled at 768×768px, each tile = 258 tokens

    Formula for tiles:
    1. crop_unit = floor(min(width, height) / 1.5)
    2. tiles = (width / crop_unit) × (height / crop_unit)

    Args:
        image: PIL Image object

    Returns:
        Estimated token count for this image

    Examples:
        >>> img = Image.open("small.jpg")  # 300×200
        >>> calculate_image_tokens(img)
        258

        >>> img = Image.open("large.jpg")  # 960×540
        >>> calculate_image_tokens(img)  # crop_unit=360, tiles=3×2=6
        1548  # 6 × 258
    """
    width, height = image.size

    # Small images (both dimensions ≤ 384px)
    if width <= 384 and height <= 384:
        logger.debug(f"Image {width}×{height} ≤ 384px: 258 tokens")
        return 258

    # Large images - tiled processing
    min_dim = min(width, height)
    crop_unit = int(min_dim / 1.5)

    tiles_w = (width + crop_unit - 1) // crop_unit  # ceiling division
    tiles_h = (height + crop_unit - 1) // crop_unit
    total_tiles = tiles_w * tiles_h

    tokens = total_tiles * 258

    logger.debug(
        f"Image {width}×{height}: crop_unit={crop_unit}, "
        f"tiles={tiles_w}×{tiles_h}={total_tiles}, tokens={tokens}"
    )

    return tokens


def calculate_images_tokens(images: List[Image.Image]) -> dict:
    """Calculate total tokens for multiple images.

    Args:
        images: List of PIL Image objects

    Returns:
        dict with breakdown:
        {
            'total_tokens': int,
            'image_count': int,
            'per_image': [int, ...],
            'breakdown': str
        }

    Example:
        >>> images = [img1, img2, img3]
        >>> result = calculate_images_tokens(images)
        >>> print(result['breakdown'])
        Image 1 (1920×1080): 1,548 tokens
        Image 2 (800×600): 258 tokens
        Image 3 (3840×2160): 6,192 tokens
        Total: 7,998 tokens
    """
    per_image_tokens = [calculate_image_tokens(img) for img in images]
    total = sum(per_image_tokens)

    # Create detailed breakdown
    breakdown_lines = []
    for i, (img, tokens) in enumerate(zip(images, per_image_tokens), 1):
        w, h = img.size
        breakdown_lines.append(f"Frame {i} ({w}×{h}): {tokens:,} tokens")

    breakdown_lines.append(f"Total: {total:,} tokens")
    breakdown = "\n".join(breakdown_lines)

    logger.info(f"Calculated tokens for {len(images)} images: {total:,} total")

    return {
        "total_tokens": total,
        "image_count": len(images),
        "per_image": per_image_tokens,
        "breakdown": breakdown,
    }


def estimate_cost(tokens: int, model: str = "gemini-2.5-flash") -> dict:
    """Estimate API cost based on token count.

    Pricing as of 2025 (check current rates at https://ai.google.dev/pricing):
    - Flash models: Lower cost per token
    - Pro models: Higher cost per token

    Args:
        tokens: Total token count
        model: Model name

    Returns:
        dict with cost estimates

    Example:
        >>> estimate_cost(7500, "gemini-2.5-flash")
        {
            'tokens': 7500,
            'model': 'gemini-2.5-flash',
            'estimated_input_cost_usd': 0.000141,
            'note': 'Output tokens charged separately...'
        }
    """
    # Pricing tiers (example - update with actual rates)
    # Free tier: 1,500 requests per day, 1 million tokens per minute
    pricing = {
        "gemini-2.5-flash-lite": {
            "input": 0.00001875,
            "output": 0.000075,
        },  # per 1K tokens
        "gemini-2.5-flash": {"input": 0.00001875, "output": 0.000075},
        "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-2.0-flash": {"input": 0.00001875, "output": 0.000075},
    }

    rates = pricing.get(model, pricing["gemini-2.5-flash"])
    input_cost = (tokens / 1000) * rates["input"]

    return {
        "tokens": tokens,
        "model": model,
        "estimated_input_cost_usd": round(input_cost, 6),
        "note": "Output tokens charged separately based on response length",
    }

```

## `utils/logger.py`

```py
"""Centralized logging configuration for the MCP server.

Provides a unified logger with file and console output, proper formatting,
and log rotation to prevent disk space issues.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ from the calling module).

    Returns:
        Configured logger instance with file and console handlers.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Use absolute path to ensure logs are created in the project directory
    project_root = Path(__file__).parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    # Formatter for all handlers
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
        errors="replace",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # File handler for errors only
    error_handler = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
        errors="replace",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)

    if hasattr(console_handler.stream, "reconfigure"):
        console_handler.stream.reconfigure(encoding="utf-8", errors="replace")

    # Add all handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    return logger

```

## `utils/media_frame_extractor.py`

```py
"""Universal media frame extraction for GIF and Video files.

This module provides unified frame extraction functionality for both
animated GIFs and video files, with three extraction modes and in-memory
WEBP conversion for optimal size/quality balance.
"""

import base64
import io
from typing import Optional, Literal, Union
from PIL import Image
import imageio.v3 as iio
from utils.logger import get_logger
from utils.gif_processor import (
    _get_fps_indices,
    _get_total_indices,
    _get_interval_indices,
    _convert_frame,
    resize_image,
)

logger = get_logger(__name__)


def extract_frames(
    source: Union[str, Image.Image],
    mode: Literal["fps", "total", "interval"] = "total",
    # Mode parameters
    frame_count: Optional[int] = 10,
    fps: Optional[float] = None,
    interval_sec: Optional[float] = None,
    # Quality parameters
    max_dimension: int = 1920,
    output_format: Literal["webp", "jpeg", "png"] = "webp",
    quality: int = 80,
) -> tuple[list[str], dict]:
    """Extract and optimize frames from video or GIF.

    Args:
        source: Video file path (str) or PIL Image (for GIF)
        mode: Extraction mode ('fps', 'total', 'interval')
        frame_count: Number of frames for 'total' mode (default: 10)
        fps: Frames per second for 'fps' mode
        interval_sec: Interval in seconds for 'interval' mode
        max_dimension: Max dimension for resizing (default: 1920 for 1080p)
        output_format: Output format ('webp', 'jpeg', 'png')
        quality: Compression quality (1-100, default: 80)

    Returns:
        Tuple of (frames_base64, metadata):
            frames_base64: List of base64-encoded frame strings
            metadata: Dict with frame_count, total_size_mb, avg_frame_size_kb, resolution

    Raises:
        ValueError: If invalid parameters or file format
        FileNotFoundError: If video file not found
        RuntimeError: If frame extraction fails

    Examples:
        # Extract 30 frames from video (evenly distributed)
        frames, meta = extract_frames("video.mp4", mode="total", frame_count=30)

        # Extract at 0.5 FPS (1 frame every 2 seconds)
        frames, meta = extract_frames("video.mp4", mode="fps", fps=0.5)

        # Extract frame every 10 seconds
        frames, meta = extract_frames("video.mp4", mode="interval", interval_sec=10)

        # Extract from GIF
        from PIL import Image
        gif = Image.open("animation.gif")
        frames, meta = extract_frames(gif, mode="total", frame_count=20)
    """
    # Determine if source is GIF or video
    is_gif = isinstance(source, Image.Image)

    if is_gif:
        logger.info("Extracting frames from GIF")
        pil_frames = _extract_gif_frames(source, mode, fps, frame_count, interval_sec)
    else:
        logger.info(f"Extracting frames from video: {source}")
        pil_frames = _extract_video_frames(source, mode, fps, frame_count, interval_sec)

    if not pil_frames:
        raise RuntimeError("No frames extracted from source")

    logger.info(f"Extracted {len(pil_frames)} frames, converting to {output_format}...")

    # Resize and convert frames to base64
    frames_base64 = []
    total_size_bytes = 0

    for i, frame in enumerate(pil_frames, 1):
        # Resize if needed
        resized_frame = resize_image(frame, max_dimension)

        # Convert to base64
        frame_b64, frame_size = _convert_to_base64(
            resized_frame, output_format, quality
        )
        frames_base64.append(frame_b64)
        total_size_bytes += frame_size

        if i == 1:
            # Log first frame info
            w, h = resized_frame.size
            logger.info(
                f"Frame 1: {w}×{h}, {frame_size / 1024:.1f} KB ({output_format} q={quality})"
            )

    # Calculate metadata
    total_size_mb = total_size_bytes / (1024 * 1024)
    avg_frame_size_kb = (total_size_bytes / len(pil_frames)) / 1024
    w, h = pil_frames[0].size
    resolution = f"{w}×{h}"

    metadata = {
        "frame_count": len(pil_frames),
        "total_size_mb": round(total_size_mb, 3),
        "avg_frame_size_kb": round(avg_frame_size_kb, 1),
        "resolution": resolution,
        "format": output_format,
        "quality": quality,
    }

    logger.info(
        f"✅ Extracted {metadata['frame_count']} frames, "
        f"total size: {metadata['total_size_mb']:.2f} MB, "
        f"avg: {metadata['avg_frame_size_kb']:.1f} KB/frame"
    )

    return frames_base64, metadata


def _extract_gif_frames(
    image: Image.Image,
    mode: Literal["fps", "total", "interval"],
    fps: Optional[float],
    frame_count: Optional[int],
    interval_sec: Optional[float],
) -> list[Image.Image]:
    """Extract frames from animated GIF.

    Uses logic from gif_processor.py for consistency.
    """
    if not getattr(image, "is_animated", False):
        logger.info("GIF is not animated, returning single frame")
        return [_convert_frame(image)]

    # Get GIF metadata
    gif_duration_ms = image.info.get("duration", 100)
    total_frames = getattr(image, "n_frames", 1)
    total_duration_sec = (gif_duration_ms * total_frames) / 1000.0
    native_fps = 1000.0 / gif_duration_ms

    logger.info(
        f"GIF: {total_frames} frames, {total_duration_sec:.1f}s, {native_fps:.1f} native fps"
    )

    # Calculate frame indices using gif_processor logic
    if mode == "fps":
        if fps is None:
            raise ValueError("Parameter 'fps' required for mode 'fps'")
        frame_indices = _get_fps_indices(total_frames, native_fps, fps)

    elif mode == "total":
        if frame_count is None:
            raise ValueError("Parameter 'frame_count' required for mode 'total'")
        frame_indices = _get_total_indices(total_frames, frame_count)

    elif mode == "interval":
        if interval_sec is None:
            raise ValueError("Parameter 'interval_sec' required for mode 'interval'")
        frame_indices = _get_interval_indices(
            total_frames, total_duration_sec, interval_sec
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

    logger.info(f"Selected {len(frame_indices)} frame indices using mode '{mode}'")

    # Extract frames at calculated indices
    frames = []
    for idx in frame_indices:
        image.seek(idx)
        frame = image.copy()
        frames.append(_convert_frame(frame))

    return frames


def _extract_video_frames(
    video_path: str,
    mode: Literal["fps", "total", "interval"],
    fps: Optional[float],
    frame_count: Optional[int],
    interval_sec: Optional[float],
) -> list[Image.Image]:
    """Extract frames from video file using imageio-ffmpeg.

    Args:
        video_path: Path to video file
        mode: Extraction mode
        fps: Target FPS for 'fps' mode
        frame_count: Number of frames for 'total' mode
        interval_sec: Interval for 'interval' mode

    Returns:
        List of PIL Image frames

    Raises:
        FileNotFoundError: If video file not found
        ValueError: If invalid parameters
    """
    # Get video metadata
    try:
        import math

        video_meta = iio.immeta(video_path)
        total_frames = video_meta.get("nframes", 0)
        native_fps = video_meta.get("fps", 30.0)
        duration = video_meta.get("duration", 0.0)

        # Handle inf/NaN values from metadata
        if isinstance(total_frames, (int, float)):
            if (
                total_frames == 0
                or math.isinf(total_frames)
                or math.isnan(total_frames)
            ):
                logger.warning(
                    f"Invalid frame count from metadata: {total_frames}, will read dynamically"
                )
                total_frames = None
            else:
                total_frames = int(total_frames)  # Convert to int if valid
        else:
            logger.warning(
                f"Unexpected frame count type: {type(total_frames)}, will read dynamically"
            )
            total_frames = None

        if duration == 0.0 or math.isinf(duration) or math.isnan(duration):
            if total_frames and total_frames > 0:
                duration = total_frames / native_fps
            else:
                duration = None

        if total_frames:
            logger.info(
                f"Video: {total_frames} frames, {duration:.1f}s, {native_fps:.1f} native fps"
            )
        else:
            logger.info(
                f"Video metadata incomplete, will read all frames (estimated {native_fps:.1f} fps)"
            )

    except Exception as e:
        logger.warning(f"Could not read video metadata: {e}")
        logger.info("Will extract frames and determine count dynamically")
        total_frames = None
        native_fps = 30.0  # fallback
        duration = None

    # Calculate frame indices
    if mode == "fps":
        if fps is None:
            raise ValueError("Parameter 'fps' required for mode 'fps'")

        # For FPS mode, we'll read every Nth frame
        if total_frames:
            frame_indices = _get_fps_indices(total_frames, native_fps, fps)
        else:
            # Read all frames and subsample
            frame_indices = None  # Will handle during reading

    elif mode == "total":
        if frame_count is None:
            raise ValueError("Parameter 'frame_count' required for mode 'total'")

        if total_frames:
            frame_indices = _get_total_indices(total_frames, frame_count)
        else:
            # Will need to read all frames first
            frame_indices = None

    elif mode == "interval":
        if interval_sec is None:
            raise ValueError("Parameter 'interval_sec' required for mode 'interval'")

        if total_frames and duration:
            frame_indices = _get_interval_indices(total_frames, duration, interval_sec)
        else:
            # Calculate based on assumed duration
            frame_indices = None

    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Extract frames
    frames = []

    if frame_indices is not None:
        # We know exact indices to extract
        logger.info(f"Extracting {len(frame_indices)} frames at specific indices...")

        try:
            # Read video and extract specific frames
            for frame_idx, frame_array in enumerate(iio.imiter(video_path)):
                if frame_idx in frame_indices:
                    # Convert numpy array to PIL Image
                    pil_frame = Image.fromarray(frame_array)
                    pil_frame = _convert_frame(pil_frame)
                    frames.append(pil_frame)

                    # Stop if we have all needed frames
                    if len(frames) == len(frame_indices):
                        break

        except Exception as e:
            logger.error(f"Error reading video frames: {e}")
            raise RuntimeError(f"Failed to extract frames from video: {e}")

    else:
        # Need to read all frames first, then subsample
        logger.info("Reading all video frames for dynamic extraction...")

        try:
            all_frames = []
            for frame_array in iio.imiter(video_path):
                pil_frame = Image.fromarray(frame_array)
                pil_frame = _convert_frame(pil_frame)
                all_frames.append(pil_frame)

            total_frames = len(all_frames)
            logger.info(f"Read {total_frames} total frames")

            # Now calculate indices
            if mode == "fps":
                # Assume 30 fps if not known
                if fps is None:
                    raise ValueError("Parameter 'fps' required for mode 'fps'")
                frame_indices = _get_fps_indices(total_frames, native_fps, fps)
            elif mode == "total":
                if frame_count is None:
                    raise ValueError(
                        "Parameter 'frame_count' required for mode 'total'"
                    )
                frame_indices = _get_total_indices(total_frames, frame_count)
            elif mode == "interval":
                if interval_sec is None:
                    raise ValueError(
                        "Parameter 'interval_sec' required for mode 'interval'"
                    )
                # Calculate duration from frame count
                calc_duration = total_frames / native_fps
                frame_indices = _get_interval_indices(
                    total_frames, calc_duration, interval_sec
                )

            # Extract selected frames
            frames = [all_frames[i] for i in frame_indices if i < len(all_frames)]

        except Exception as e:
            logger.error(f"Error reading video frames: {e}")
            raise RuntimeError(f"Failed to extract frames from video: {e}")

    if not frames:
        raise RuntimeError("No frames were extracted from video")

    logger.info(f"Successfully extracted {len(frames)} frames from video")
    return frames


def _convert_to_base64(
    image: Image.Image, output_format: str, quality: int
) -> tuple[str, int]:
    """Convert PIL Image to base64-encoded string.

    Args:
        image: PIL Image
        output_format: 'webp', 'jpeg', or 'png'
        quality: Compression quality (1-100)

    Returns:
        Tuple of (base64_string, size_in_bytes)
    """
    buffer = io.BytesIO()

    # Convert format name to PIL format
    if output_format == "webp":
        image.save(buffer, format="WEBP", quality=quality, method=6)
    elif output_format == "jpeg":
        # Convert RGBA to RGB for JPEG
        if image.mode == "RGBA":
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
    elif output_format == "png":
        image.save(buffer, format="PNG", optimize=True)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

    # Get size and base64
    buffer.seek(0)
    image_bytes = buffer.getvalue()
    size = len(image_bytes)
    b64_string = base64.b64encode(image_bytes).decode("utf-8")

    return b64_string, size

```

