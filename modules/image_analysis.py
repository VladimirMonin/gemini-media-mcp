"""Image analysis module using Google Gemini API.

This module provides high-level image analysis functionality with support
for custom system instructions and predefined analysis prompts.
"""

from typing import Any, Dict, Optional

from config import (
    AVAILABLE_IMAGE_ANALYSIS_PROMPTS,
    DEFAULT_GEMINI_MODEL,
    GEMINI_MODELS,
)
from models.analysis import ErrorResponse, ImageAnalysisResponse
from utils.gemini_client import GeminiClient
from utils.logger import get_logger

logger = get_logger(__name__)


class ImageAnalysisModule:
    """High-level image analysis module using Gemini API.

    Provides convenient methods for analyzing images with predefined or
    custom system instructions.

    Attributes:
        model_name: The Gemini model being used.
        gemini_client: The underlying Gemini API client.
    """

    def __init__(self, model_name: str = DEFAULT_GEMINI_MODEL):
        """Initialize the image analysis module.

        Args:
            model_name: Name of the Gemini model to use.

        Raises:
            ValueError: If the specified model is not supported.
        """
        if model_name not in GEMINI_MODELS:
            logger.error(f"Unsupported model: {model_name}")
            raise ValueError(
                f"Model {model_name} is not supported. Available: {GEMINI_MODELS}"
            )
        self.model_name = model_name
        self.gemini_client = GeminiClient(model_name=model_name)
        logger.info(f"ImageAnalysisModule initialized with model: {model_name}")

    def analyze(
        self,
        image_path: str,
        user_prompt: str = "",
        system_instruction_name: Optional[str] = "default",
        system_instruction_override: Optional[str] = None,
        system_instruction_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze an image with configurable system instructions.

        Args:
            image_path: Path to the image file.
            user_prompt: User's analysis prompt.
            system_instruction_name: Name of predefined prompt from config.
            system_instruction_override: Custom system instruction string.
            system_instruction_file_path: Path to file with system instruction.

        Returns:
            Dictionary with analysis results or error information.
        """
        final_system_instruction = None

        if system_instruction_file_path:
            try:
                with open(system_instruction_file_path, "r", encoding="utf-8") as f:
                    final_system_instruction = f.read()
                logger.debug(
                    f"Loaded system instruction from file: {system_instruction_file_path}"
                )
            except FileNotFoundError:
                logger.error(
                    f"System instruction file not found: {system_instruction_file_path}"
                )
                return {
                    "error": f"System instruction file not found: {system_instruction_file_path}"
                }
            except IOError as e:
                logger.error(f"Error reading system instruction file: {e}")
                return {"error": f"Error reading system instruction file: {e}"}
        elif system_instruction_override:
            final_system_instruction = system_instruction_override
            logger.debug("Using custom system instruction override")
        elif system_instruction_name:
            if system_instruction_name in AVAILABLE_IMAGE_ANALYSIS_PROMPTS:
                final_system_instruction = AVAILABLE_IMAGE_ANALYSIS_PROMPTS[
                    system_instruction_name
                ]
                logger.debug(f"Using predefined prompt: {system_instruction_name}")
            else:
                available = list(AVAILABLE_IMAGE_ANALYSIS_PROMPTS.keys())
                logger.error(f"Unknown prompt name: {system_instruction_name}")
                return {
                    "error": f"Prompt '{system_instruction_name}' not found. Available: {available}"
                }

        result = self.gemini_client.analyze_image(
            image_path=image_path,
            user_prompt=user_prompt,
            system_instruction_override=final_system_instruction,
        )

        if isinstance(result, ImageAnalysisResponse):
            return result.model_dump()
        if isinstance(result, ErrorResponse):
            return result.model_dump()

        logger.error("Unexpected response format from Gemini")
        return {"error": "Unexpected response format from Gemini"}
