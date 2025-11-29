"""Утилиты MCP сервера.

Функции:
    get_file_mime_type(file_path: str) -> str | None
        Определяет MIME-тип файла.
    is_image_valid(file_path: str) -> bool
        Проверяет, является ли файл поддерживаемым изображением.
    get_logger(name: str) -> logging.Logger
        Получает настроенный экземпляр логгера.

Классы:
    GeminiClient
        Клиент для работы с Gemini API.
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
