"""Data models for structured responses.

This package contains Pydantic models for image analysis responses
and error handling.
"""

from models.analysis import ImageAnalysisResponse, ErrorResponse

__all__ = ["ImageAnalysisResponse", "ErrorResponse"]
