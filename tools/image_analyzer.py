"""Инструмент анализа изображений через Gemini API.

Функции:
    get_system_instruction(name: str, override: str, file_path: str) -> str | None
        Получает системную инструкцию с приоритетной обработкой.
    analyze_image(image_path: str, ...) -> ImageAnalysisResponse | ErrorResponse
        Анализирует изображение и возвращает структурированный результат.
"""

import json
from PIL import Image
from config import (
    AVAILABLE_IMAGE_ANALYSIS_PROMPTS,
    DEFAULT_GEMINI_MODEL,
    GEMINI_MODELS,
)
from models.analysis import ErrorResponse, ImageAnalysisResponse
from utils.file_utils import is_image_valid
from utils.gemini_client import GeminiClient
from utils.logger import get_logger
from utils.image_tokens import calculate_image_tokens, estimate_cost

logger = get_logger(__name__)


def get_system_instruction(
    name: str = "default", override: str | None = None, file_path: str | None = None
) -> str | None:
    """Получает системную инструкцию с приоритетной обработкой.

    Приоритет: file_path > override > name (из словаря).

    Args:
        name: Имя предопределённой инструкции.
        override: Пользовательская инструкция.
        file_path: Путь к файлу с инструкцией.

    Returns:
        Текст системной инструкции или None.

    Raises:
        FileNotFoundError: Если файл инструкции не найден.
        IOError: Ошибка чтения файла.
    """
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    if override:
        return override
    return AVAILABLE_IMAGE_ANALYSIS_PROMPTS.get(name)


def analyze_image(
    image_path: str,
    user_prompt: str = "",
    model_name: str | None = None,
    system_instruction_name: str = "default",
    system_instruction_override: str | None = None,
    system_instruction_file_path: str | None = None,
) -> ImageAnalysisResponse | ErrorResponse:
    """Анализирует изображение через Google Gemini API.

    Возвращает структурированный результат с alt-text и детальным анализом.
    Поддерживаемые форматы: JPEG, PNG, GIF, WEBP, HEIC, HEIF.

    Args:
        image_path: Абсолютный путь к файлу изображения.
        user_prompt: Пользовательский запрос на анализ.
        model_name: Модель Gemini (по умолчанию из config.py).
        system_instruction_name: Имя предопределённой инструкции.
        system_instruction_override: Пользовательская инструкция.
        system_instruction_file_path: Путь к файлу с инструкцией.

    Returns:
        Структурированный ответ анализа или ошибка.

    Raises:
        ValueError: Неверный формат изображения или инструкция не найдена.
        FileNotFoundError: Файл изображения или инструкции не найден.
    """
    logger.info("=" * 80)
    logger.info(f"🖼️  IMAGE ANALYSIS STARTED: {image_path}")

    # Валидация изображения
    if not is_image_valid(image_path):
        logger.error(f"❌ Invalid image format: {image_path}")
        raise ValueError(f"File is not a supported image: {image_path}")

    # Получение системной инструкции
    try:
        system_instruction = get_system_instruction(
            name=system_instruction_name,
            override=system_instruction_override,
            file_path=system_instruction_file_path,
        )
    except FileNotFoundError as e:
        logger.error(f"System instruction file not found: {e}")
        raise
    except IOError as e:
        logger.error(f"Error reading system instruction file: {e}")
        raise

    # Проверка наличия системной инструкции
    if system_instruction is None and system_instruction_name:
        available = list(AVAILABLE_IMAGE_ANALYSIS_PROMPTS.keys())
        raise ValueError(
            f"Prompt '{system_instruction_name}' not found. Available: {available}"
        )

    # Выбор и валидация модели
    final_model_name = model_name or DEFAULT_GEMINI_MODEL
    if final_model_name not in GEMINI_MODELS:
        raise ValueError(
            f"Model '{final_model_name}' is not supported. "
            f"Available models: {GEMINI_MODELS}"
        )

    logger.info(
        f"📊 Parameters: model={final_model_name}, system_instruction={system_instruction_name}"
    )

    # Calculate tokens for image
    try:
        image = Image.open(image_path)
        tokens = calculate_image_tokens(image)
        cost_info = estimate_cost(tokens, final_model_name)
        logger.info(f"💰 Token estimate: {tokens:,} tokens")
        logger.info(
            f"💵 Estimated cost: ${cost_info['estimated_input_cost_usd']:.6f} USD"
        )
    except Exception as e:
        logger.warning(f"⚠️  Could not calculate tokens: {e}")
        tokens = None
        cost_info = None

    # Инициализация клиента и анализ
    try:
        logger.info(f"🚀 Sending request to Gemini ({final_model_name})...")
        gemini_client = GeminiClient(model_name=final_model_name)
        response_text = gemini_client.generate_content(
            prompt=user_prompt,
            image_path=image_path,
            system_instruction=system_instruction,
            response_schema=ImageAnalysisResponse,
        )

        try:
            result_dict = json.loads(response_text)
            result = ImageAnalysisResponse(**result_dict)
            logger.info(f"✅ Analysis completed successfully for {image_path}")
            if tokens and cost_info:
                logger.info(
                    f"📈 Summary: {tokens:,} tokens, ${cost_info['estimated_input_cost_usd']:.6f} USD"
                )
            logger.info("=" * 80)
            return result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error("=" * 80)
            return ErrorResponse(
                error="JSON parsing error",
                details=str(e),
                raw_response=response_text,
            )

    except Exception as e:
        logger.exception(
            f"❌ Failed to analyze image with model {final_model_name}: {e}"
        )
        logger.error("=" * 80)
        return ErrorResponse(
            error="Image analysis failed",
            details=str(e),
        )
