"""Инструменты MCP сервера для работы с медиа.

Функции:
    analyze_image(image_path: str, ...) -> ImageAnalysisResponse | ErrorResponse
        Анализирует изображение через Gemini API.
    batch_generate_images(prompts: list, ...) -> dict
        Пакетная генерация изображений.
    queue_generate_audio(text: str, ...) -> dict
        Добавляет задачу генерации аудио в очередь.
    check_task_status(task_id: str) -> dict
        Проверяет статус задачи.
    check_batch_progress(batch_id: str) -> dict
        Проверяет прогресс batch-задачи.
"""

from .image_analyzer import analyze_image
from .batch_tools import (
    batch_generate_images,
    queue_generate_audio,
    check_task_status,
    check_batch_progress,
)

__all__ = [
    "analyze_image",
    "batch_generate_images",
    "queue_generate_audio",
    "check_task_status",
    "check_batch_progress",
]
