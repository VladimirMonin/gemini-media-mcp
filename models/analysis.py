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

    title: Optional[str] = Field(default=None, description="Suggested title for the audio.")
    summary: Optional[str] = Field(default=None, description="Brief summary of the audio content.")
    transcription: Optional[str] = Field(default=None, description="Full transcription of the audio.")
    participants: Optional[list[str]] = Field(default=None, description="List of identified participants.")
    hashtags: Optional[list[str]] = Field(default=None, description="Keywords or topics as hashtags.")
    action_items: Optional[list[str]] = Field(default=None, description="List of action items mentioned.")
    raw_text: str = Field(..., description="Raw text response from the model.")
