"""Клиент Google Gemini API для анализа медиа-контента.

Классы:
    GeminiClient
        Клиент для работы с Gemini API.

        Методы:
            generate_content(prompt: str, ...) -> str
                Генерирует контент с медиа.
            generate_text(prompt: str) -> str
                Генерирует текст по промпту.
            generate_content_multi_image(prompt: str, images: Sequence) -> str
                Генерирует контент с несколькими изображениями.
"""

import json
from typing import Optional, Union, List, Sequence

from PIL import Image
from google.genai import types, Client

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

# Маппинг строковых значений media_resolution на enum Google API
_MEDIA_RESOLUTION_MAP = {
    "low": types.MediaResolution.MEDIA_RESOLUTION_LOW,
    "medium": types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
    "high": types.MediaResolution.MEDIA_RESOLUTION_HIGH,
}


class GeminiClient:
    """Клиент для работы с Google Gemini API.

    Attributes:
        model_name: Имя модели Gemini.
        client: Настроенный клиент Google Gemini API.
    """

    def __init__(self, model_name: str = DEFAULT_GEMINI_MODEL):
        """Инициализирует клиент Gemini."""
        self.model_name = model_name
        self.client = Client(api_key=GEMINI_API_KEY)
        logger.info(f"🔧 Инициализирован GeminiClient: {model_name}")

    @staticmethod
    def _resolve_media_resolution(
        value: Optional[str],
    ) -> Optional[types.MediaResolution]:
        """Преобразует строковое значение media_resolution в enum Google API.

        Args:
            value: Строковое значение ('low', 'medium', 'high') или None.

        Returns:
            Enum types.MediaResolution или None.

        Raises:
            ValueError: Если передано неизвестное значение.
        """
        if value is None:
            return None
        resolved = _MEDIA_RESOLUTION_MAP.get(value.lower())
        if resolved is None:
            raise ValueError(
                f"Unknown media_resolution '{value}'. "
                f"Available: {list(_MEDIA_RESOLUTION_MAP.keys())}"
            )
        return resolved

    def generate_content(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        media_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        system_instruction: Optional[str] = None,
        response_schema=None,
        media_resolution: Optional[str] = None,
    ) -> str:
        """Генерирует контент с медиа через Gemini API.

        Args:
            prompt: Текстовый промпт.
            image_path: Путь к изображению.
            media_bytes: Медиа-данные в байтах.
            mime_type: MIME-тип медиа.
            system_instruction: Системная инструкция.
            response_schema: Pydantic модель для структурированного ответа.
            media_resolution: Разрешение обработки медиа ('low', 'medium', 'high').
                Влияет на количество токенов для изображений.
                'high' рекомендуется для скриншотов с мелким текстом.

        Returns:
            Текстовый ответ модели.
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

            resolved_resolution = self._resolve_media_resolution(media_resolution)
            if resolved_resolution:
                config_params["media_resolution"] = resolved_resolution
                logger.info(f"📐 Media resolution: {media_resolution}")

            config = types.GenerateContentConfig(**config_params)

            logger.info("🚀 Отправка запроса на генерацию в Gemini")
            response = self.client.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )

            if hasattr(response, "text"):
                return response.text or ""

            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                feedback = response.prompt_feedback
                if hasattr(feedback, "block_reason") and feedback.block_reason:
                    logger.warning(f"⚠️ Запрос заблокирован: {feedback.block_reason}")
                    raise ValueError(
                        f"Request blocked by safety filters: {feedback.block_reason}"
                    )

            raise ValueError("Failed to get a valid response from Gemini model.")

        except Exception as e:
            logger.exception(f"❌ Ошибка генерации контента: {e}")
            raise

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Генерирует текст на основе промпта."""
        logger.debug(f"Generating text for prompt: {prompt[:50]}...")
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt, **kwargs
        )
        return response.text or ""

    def generate_content_multi_image(
        self,
        prompt: str,
        images: Sequence[Union[str, Image.Image, types.Part]],
        system_instruction: Optional[str] = None,
        response_schema=None,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
        media_resolution: Optional[str] = None,
    ) -> str:
        """Генерирует контент с несколькими изображениями.

        Args:
            prompt: Текстовый промпт для анализа.
            images: Список изображений (пути, PIL Image или types.Part).
            system_instruction: Системная инструкция.
            response_schema: Pydantic модель для структурированного ответа.
            temperature: Температура генерации (0.0-2.0).
            max_output_tokens: Максимум токенов в ответе.
            media_resolution: Разрешение обработки медиа ('low', 'medium', 'high').

        Returns:
            Текстовый ответ модели.
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

            resolved_resolution = self._resolve_media_resolution(media_resolution)
            if resolved_resolution:
                config_params["media_resolution"] = resolved_resolution
                logger.info(f"📐 Media resolution: {media_resolution}")

            config = types.GenerateContentConfig(**config_params)

            logger.info(
                f"🚀 Отправка {len(images)} изображений в Gemini ({self.model_name})"
            )
            logger.info(f"📐 Медиа-разрешение: {media_resolution or 'default'}")
            response = self.client.models.generate_content(
                model=self.model_name, contents=content_parts, config=config
            )

            if hasattr(response, "text"):
                return response.text or ""

            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                feedback = response.prompt_feedback
                if hasattr(feedback, "block_reason") and feedback.block_reason:
                    logger.warning(f"⚠️ Запрос заблокирован: {feedback.block_reason}")
                    raise ValueError(
                        f"Request blocked by safety filters: {feedback.block_reason}"
                    )

            raise ValueError("Failed to get a valid response from Gemini model.")

        except Exception as e:
            logger.exception(f"❌ Ошибка генерации с изображениями: {e}")
            raise
