"""Google Gemini API client for image analysis.

This module provides a wrapper around the Google Gemini API for analyzing
images with custom prompts and system instructions.
"""

import json
from typing import Optional, Union

from PIL import Image
from google.genai import types, Client

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL
from models.analysis import ImageAnalysisResponse, ErrorResponse
from utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Client wrapper for Google Gemini API interactions.

    Provides methods for analyzing images using Google's Gemini models
    with support for custom prompts and system instructions.

    Attributes:
        model_name: The name of the Gemini model to use.
        client: The configured Google Gemini API client.
    """

    def __init__(self, model_name: str = DEFAULT_GEMINI_MODEL):
        """Initialize the Gemini client.

        Args:
            model_name: Name of the Gemini model to use.
        """
        self.model_name = model_name
        self.client = Client(api_key=GEMINI_API_KEY)
        logger.info(f"Initialized GeminiClient with model: {model_name}")

    def analyze_image(
        self,
        image_path: str,
        user_prompt: str,
        system_instruction_override: Optional[str] = None,
        system_instruction_file_path: Optional[str] = None,
    ) -> Union[ImageAnalysisResponse, ErrorResponse]:
        """Analyze an image using the Gemini API.

        Args:
            image_path: Path to the image file.
            user_prompt: User's analysis prompt.
            system_instruction_override: Custom system instruction to override defaults.
            system_instruction_file_path: Path to file containing system instruction.

        Returns:
            ImageAnalysisResponse on success, ErrorResponse on failure.
        """
        try:
            final_system_instruction = None

            if system_instruction_file_path:
                try:
                    with open(system_instruction_file_path, "r", encoding="utf-8") as f:
                        final_system_instruction = f.read()
                    logger.debug(
                        f"Loaded system instruction from: {system_instruction_file_path}"
                    )
                except FileNotFoundError:
                    logger.error(
                        f"System instruction file not found: {system_instruction_file_path}"
                    )
                    return ErrorResponse(
                        error="System instruction file not found",
                        details=system_instruction_file_path,
                    )
                except IOError as e:
                    logger.error(f"Failed to read system instruction file: {e}")
                    return ErrorResponse(
                        error="Error reading system instruction file",
                        details=str(e),
                    )
            elif system_instruction_override:
                final_system_instruction = system_instruction_override
                logger.debug("Using custom system instruction override")

            try:
                image = Image.open(image_path)
                logger.debug(f"Loaded image: {image_path}")
            except FileNotFoundError:
                logger.error(f"Image file not found: {image_path}")
                return ErrorResponse(
                    error="Image file not found",
                    details=image_path,
                )
            except IOError as e:
                logger.error(f"Failed to read image file: {e}")
                return ErrorResponse(
                    error="Error reading image file",
                    details=str(e),
                )

            prompt_content = user_prompt if user_prompt else "Analyze this image."
            contents = [prompt_content, image]

            config_params = {
                "temperature": 0.7,
                "max_output_tokens": 4096,
                "safety_settings": [
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                ],
                "response_mime_type": "application/json",
                "response_schema": ImageAnalysisResponse,
            }

            if final_system_instruction:
                config_params["system_instruction"] = final_system_instruction

            config = types.GenerateContentConfig(**config_params)

            logger.info(f"Sending analysis request for: {image_path}")
            response = self.client.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )

            if hasattr(response, "candidates") and response.candidates:
                response_text = (response.text or "").strip()

                try:
                    result_dict = json.loads(response_text)
                    logger.info("Successfully analyzed image")
                    return ImageAnalysisResponse(**result_dict)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}")
                    return ErrorResponse(
                        error="JSON parsing error",
                        details=str(e),
                        raw_response=response_text,
                    )
            else:
                if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                    feedback = response.prompt_feedback
                    if hasattr(feedback, "block_reason") and feedback.block_reason:
                        logger.warning(f"Request blocked: {feedback.block_reason}")
                        return ErrorResponse(
                            error="Request blocked by safety filters",
                            details=str(feedback.block_reason),
                        )
                logger.error("No response from Gemini model")
                return ErrorResponse(error="Failed to get response from Gemini model")

        except Exception as e:
            logger.exception(f"Unexpected error during image analysis: {e}")
            return ErrorResponse(
                error="Unexpected error during image analysis",
                details=str(e),
            )

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text based on a prompt.

        Args:
            prompt: The text prompt for generation.
            **kwargs: Additional arguments for the API call.

        Returns:
            Generated text response.
        """
        logger.debug(f"Generating text for prompt: {prompt[:50]}...")
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt, **kwargs
        )
        return response.text or ""
