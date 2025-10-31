"""Tool for analyzing audio files using Google Gemini API."""

import json
import mimetypes
import os
from typing import Optional

from config import (
    DEFAULT_GEMINI_MODEL,
    MAX_FILE_SIZE_MB,
    SUPPORTED_AUDIO_FORMATS,
)
from models.analysis import AudioAnalysisResponse, ErrorResponse
from utils.gemini_client import GeminiClient


def analyze_audio(
    audio_path: str,
    user_prompt: str,
    analysis_type: str = "summary",
    model_name: Optional[str] = None,
    output_path: Optional[str] = None,
) -> AudioAnalysisResponse | ErrorResponse:
    """Analyzes an audio file using the Gemini API.

    Args:
        audio_path: Absolute path to the audio file.
        user_prompt: Custom analysis request.
        analysis_type: The type of analysis to perform (e.g., 'summary', 'transcription').
        model_name: The name of the Gemini model to use.
        output_path: Optional path to save the analysis result as a JSON file.

    Returns:
        A structured analysis response or an error response.
    """
    if not os.path.exists(audio_path):
        return ErrorResponse(error=f"File not found at {audio_path}")

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return ErrorResponse(
            error=f"File size ({file_size_mb:.2f} MB) exceeds the limit of {MAX_FILE_SIZE_MB} MB."
        )

    mime_type, _ = mimetypes.guess_type(audio_path)
    if mime_type not in SUPPORTED_AUDIO_FORMATS.keys():
        return ErrorResponse(
            error=f"Unsupported audio format: {mime_type}. Supported formats are: {list(SUPPORTED_AUDIO_FORMATS.keys())}"
        )

    final_model_name = model_name or DEFAULT_GEMINI_MODEL
    gemini_client = GeminiClient(model_name=final_model_name)

    try:
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        # This is a placeholder for where the system prompt will be generated based on analysis_type
        system_prompt = f"Perform the following analysis on the audio: {analysis_type}"

        response_text = gemini_client.generate_content(
            prompt=user_prompt,
            media_bytes=audio_bytes,
            mime_type=mime_type,
            system_instruction=system_prompt,
        )

        # Placeholder for parsing logic
        try:
            response_data = json.loads(response_text)
            analysis_response = AudioAnalysisResponse(**response_data, raw_text=response_text)
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, return the raw text in the designated field
            analysis_response = AudioAnalysisResponse(raw_text=response_text)


        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(analysis_response.model_dump_json(indent=2))
            return AudioAnalysisResponse(raw_text=f"Analysis saved to {output_path}")

        return analysis_response

    except Exception as e:
        return ErrorResponse(error="Failed to analyze audio.", details=str(e))
