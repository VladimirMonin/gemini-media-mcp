"""Модели данных для структурированных ответов.

Классы:
    ImageAnalysisResponse
        Модель ответа анализа изображения.
    AudioAnalysisResponse
        Модель ответа анализа аудио.
    ErrorResponse
        Модель ответа с ошибкой.
"""

from models.analysis import AudioAnalysisResponse, ErrorResponse, ImageAnalysisResponse

__all__ = ["ImageAnalysisResponse", "ErrorResponse", "AudioAnalysisResponse"]
