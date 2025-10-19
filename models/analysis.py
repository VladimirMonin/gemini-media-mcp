"""Простые Pydantic модели для структурированных ответов анализа изображений."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ImageAnalysisResponse(BaseModel):
    """Минимально необходимый структурированный ответ от Gemini."""

    alt_text: str = Field(
        ..., description="Короткое описание изображения, подходящее для alt-текста."
    )
    detailed_analysis: str = Field(
        ..., description="Развернутое описание содержимого и особенностей изображения."
    )
    summary: Optional[str] = Field(
        default=None,
        description="Необязательное краткое резюме или вывод по изображению.",
    )


class ErrorResponse(BaseModel):
    """Структура для передачи информации об ошибке."""

    error: str = Field(..., description="Текстовое описание ошибки.")
    details: Optional[str] = Field(
        default=None, description="Дополнительные сведения об ошибке, если доступны."
    )
    raw_response: Optional[str] = Field(
        default=None,
        description="Исходный ответ модели, если он не соответствует ожидаемому формату.",
    )
