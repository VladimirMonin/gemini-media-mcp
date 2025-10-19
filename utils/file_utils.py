# Утилиты для работы с файлами

import mimetypes
import os
from pathlib import Path
from typing import List

# Поддерживаемые MIME типы изображений для анализа
SUPPORTED_IMAGE_MIME_TYPES: List[str] = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    # Добавить другие форматы по необходимости, которые поддерживает генеративная модель
]

def get_file_mime_type(file_path: str) -> str | None:
    """
    Определяет MIME тип файла.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    
    # Fallback для неизвестных типов, предполагаем binary
    # Или можно попробовать определить по расширению более явно
    file_extension = Path(file_path).suffix.lower()
    if file_extension == ".jpg" or file_extension == ".jpeg":
        return "image/jpeg"
    elif file_extension == ".png":
        return "image/png"
    elif file_extension == ".gif":
        return "image/gif"
    elif file_extension == ".webp":
        return "image/webp"
    # Добавить другие форматы по необходимости
    
    return "application/octet-stream" # Тип по умолчанию для binary

def read_file_as_bytes(file_path: str) -> bytes:
    """
    Читает файл и возвращает его содержимое в виде байтов.
    """
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    except IOError as e:
        raise IOError(f"Ошибка при чтении файла {file_path}: {e}")

def is_image_valid(file_path: str) -> bool:
    """
    Проверяет, является ли файл изображением и поддерживается ли его тип.
    """
    if not os.path.exists(file_path):
        return False
    if not os.path.isfile(file_path):
        return False
    mime_type = get_file_mime_type(file_path)
    return mime_type in SUPPORTED_IMAGE_MIME_TYPES
