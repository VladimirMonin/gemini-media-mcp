"""Google Gemini API client for image analysis.

This module provides a wrapper around the Google Gemini API for analyzing
images with custom prompts and system instructions.
"""

import json
from typing import Optional, Union, List

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

    def generate_content(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        media_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        system_instruction: Optional[str] = None,
        response_schema=None,
    ) -> str:
        """Generate content with media using the Gemini API.

        Args:
            prompt: The text prompt for the model.
            image_path: Optional path to an image file.
            media_bytes: Optional media data in bytes.
            mime_type: The MIME type of the media_bytes.
            system_instruction: Optional system instruction for the model.
            response_schema: Optional Pydantic model for structured response.

        Returns:
            The raw text response from the model.
        """
        try:
            media_part = None
            if image_path:
                media_part = Image.open(image_path)
                logger.debug(f"Loaded image: {image_path}")
            elif media_bytes and mime_type:
                media_part = types.Part.from_bytes(
                    data=media_bytes, mime_type=mime_type
                )
                logger.debug(f"Loaded media bytes with MIME type: {mime_type}")

            contents = [prompt, media_part] if media_part else [prompt]

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
            }

            if system_instruction:
                config_params["system_instruction"] = system_instruction
            if response_schema:
                config_params["response_mime_type"] = "application/json"
                # Pass Pydantic model directly - library handles conversion
                config_params["response_schema"] = response_schema

            config = types.GenerateContentConfig(**config_params)

            logger.info("Sending content generation request to Gemini.")
            response = self.client.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )

            if hasattr(response, "text"):
                return response.text or ""

            # Handle cases where the response might be blocked
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                feedback = response.prompt_feedback
                if hasattr(feedback, "block_reason") and feedback.block_reason:
                    logger.warning(f"Request blocked: {feedback.block_reason}")
                    raise ValueError(
                        f"Request blocked by safety filters: {feedback.block_reason}"
                    )

            raise ValueError("Failed to get a valid response from Gemini model.")

        except Exception as e:
            logger.exception(f"Unexpected error during content generation: {e}")
            raise

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

    def generate_content_multi_image(
        self,
        prompt: str,
        images: List[Union[str, Image.Image, types.Part]],
        system_instruction: Optional[str] = None,
        response_schema=None,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
    ) -> str:
        """Generate content with multiple images using Gemini API.

        Supports mixing:
        - File paths (str)
        - PIL Image objects
        - types.Part objects (for File API references)

        Args:
            prompt: Text prompt for analysis
            images: List of images in various formats
            system_instruction: Optional system instruction
            response_schema: Optional Pydantic model for structured output
            temperature: Sampling temperature (0.0-2.0)
            max_output_tokens: Maximum tokens in response

        Returns:
            Text response from model

        Examples:
            # Mix of formats
            response = client.generate_content_multi_image(
                prompt="Compare these images",
                images=[
                    "path/to/image1.jpg",  # file path
                    pil_image,              # PIL Image
                    uploaded_file_part      # types.Part from File API
                ]
            )
        """
        try:
            # Convert all images to appropriate format
            content_parts = [prompt]

            for i, img in enumerate(images):
                if isinstance(img, str):
                    # File path - load as PIL Image
                    pil_img = Image.open(img)
                    content_parts.append(pil_img)
                    logger.debug(f"Image {i + 1}: Loaded from path {img}")

                elif isinstance(img, Image.Image):
                    # Already PIL Image
                    content_parts.append(img)
                    logger.debug(f"Image {i + 1}: PIL Image {img.size}")

                elif isinstance(img, types.Part):
                    # File API reference
                    content_parts.append(img)
                    logger.debug(f"Image {i + 1}: File API Part")

                else:
                    raise ValueError(f"Unsupported image type: {type(img)}")

            # Configure request
            config_params = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
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
            }

            if system_instruction:
                config_params["system_instruction"] = system_instruction
            if response_schema:
                config_params["response_mime_type"] = "application/json"
                config_params["response_schema"] = response_schema

            config = types.GenerateContentConfig(**config_params)

            logger.info(f"Sending {len(images)} images to Gemini ({self.model_name})")
            response = self.client.models.generate_content(
                model=self.model_name, contents=content_parts, config=config
            )

            if hasattr(response, "text"):
                return response.text or ""

            # Handle blocked responses
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                feedback = response.prompt_feedback
                if hasattr(feedback, "block_reason") and feedback.block_reason:
                    logger.warning(f"Request blocked: {feedback.block_reason}")
                    raise ValueError(
                        f"Request blocked by safety filters: {feedback.block_reason}"
                    )

            raise ValueError("Failed to get a valid response from Gemini model.")

        except Exception as e:
            logger.exception(f"Error in multi-image content generation: {e}")
            raise
