"""Модели данных для структурированных ответов анализа.

Классы:
    ImageAnalysisResponse
        Структурированный ответ анализа изображения.
    ErrorResponse
        Структурированный ответ с ошибкой.
    AudioAnalysisResponse
        Структурированный ответ анализа аудио.
    VideoAnalysisResponse
        Структурированный ответ анализа видео.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ImageAnalysisResponse(BaseModel):
    """Структурированный ответ анализа изображения.

    Attributes:
        alt_text: Краткое описание для accessibility.
        detailed_analysis: Детальное описание содержимого изображения.
        summary: Краткое резюме.
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
    """Структурированный ответ с ошибкой.

    Attributes:
        error: Описание ошибки.
        details: Дополнительные детали.
        raw_response: Сырой ответ модели.
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
    """Структурированный ответ анализа аудио.

    Attributes:
        title: Предлагаемый заголовок.
        summary: Краткое содержание.
        transcription: Полная транскрипция.
        participants: Список участников.
        hashtags: Ключевые слова.
        action_items: Список задач.
        raw_text: Сырой текст ответа модели.
    """

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
    """Структурированный ответ анализа видео.

    Attributes:
        visual_summary: Сводка визуального содержимого.
        audio_transcription: Транскрипция аудиодорожки.
        audio_description: Описание неречевого аудио.
        combined_narrative: Объединённый нарратив.
        key_moments: Ключевые моменты.
        raw_text: Сырой текст ответа модели.
    """

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
