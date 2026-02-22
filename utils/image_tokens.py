"""Утилиты расчёта токенов для обработки медиа Gemini API.

Функции:
    calculate_image_tokens(image: Image.Image) -> int
        Рассчитывает количество токенов для изображения.
    calculate_images_tokens(images: List[Image.Image]) -> dict
        Рассчитывает общее количество токенов для списка изображений.
    estimate_cost(tokens: int, model: str) -> dict
        Оценивает стоимость API на основе количества токенов.
"""

from typing import List
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_image_tokens(image: Image.Image) -> int:
    """Рассчитывает количество токенов для изображения.

    Args:
        image: PIL Image объект.

    Returns:
        Ожидаемое количество токенов.
    """
    width, height = image.size

    # Small images (both dimensions ≤ 384px)
    if width <= 384 and height <= 384:
        logger.debug(f"Image {width}×{height} ≤ 384px: 258 tokens")
        return 258

    # Large images - tiled processing
    min_dim = min(width, height)
    crop_unit = int(min_dim / 1.5)

    tiles_w = (width + crop_unit - 1) // crop_unit  # ceiling division
    tiles_h = (height + crop_unit - 1) // crop_unit
    total_tiles = tiles_w * tiles_h

    tokens = total_tiles * 258

    logger.debug(
        f"Image {width}×{height}: crop_unit={crop_unit}, "
        f"tiles={tiles_w}×{tiles_h}={total_tiles}, tokens={tokens}"
    )

    return tokens


def calculate_images_tokens(images: List[Image.Image]) -> dict:
    """Рассчитывает общее количество токенов для списка изображений.

    Args:
        images: Список PIL Image объектов.

    Returns:
        Словарь с разбивкой по изображениям.
    """
    per_image_tokens = [calculate_image_tokens(img) for img in images]
    total = sum(per_image_tokens)

    # Create detailed breakdown
    breakdown_lines = []
    for i, (img, tokens) in enumerate(zip(images, per_image_tokens), 1):
        w, h = img.size
        breakdown_lines.append(f"Frame {i} ({w}×{h}): {tokens:,} tokens")

    breakdown_lines.append(f"Total: {total:,} tokens")
    breakdown = "\n".join(breakdown_lines)

    logger.info(f"💰 Рассчитаны токены для {len(images)} изображений: {total:,}")

    return {
        "total_tokens": total,
        "image_count": len(images),
        "per_image": per_image_tokens,
        "breakdown": breakdown,
    }


def estimate_cost(tokens: int, model: str = "gemini-3-flash-preview") -> dict:
    """Оценивает стоимость API на основе количества токенов.

    Args:
        tokens: Общее количество токенов.
        model: Название модели.

    Returns:
        Словарь с оценкой стоимости.
    """
    # Цены за 1K токенов (input/output).
    # Gemini 3 preview — бесплатно на данный момент, указаны ожидаемые тарифы.
    # Источник: https://ai.google.dev/pricing
    pricing = {
        "gemini-3.1-pro-preview": {"input": 0.00125, "output": 0.005},
        "gemini-3-flash-preview": {"input": 0.00001875, "output": 0.000075},
        "gemini-3-pro-preview": {"input": 0.00125, "output": 0.005},
        "gemini-2.5-flash-lite": {"input": 0.00001875, "output": 0.000075},
        "gemini-2.5-flash": {"input": 0.00001875, "output": 0.000075},
        "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-2.0-flash": {"input": 0.00001875, "output": 0.000075},
    }

    rates = pricing.get(model, pricing["gemini-3-flash-preview"])
    input_cost = (tokens / 1000) * rates["input"]

    return {
        "tokens": tokens,
        "model": model,
        "estimated_input_cost_usd": round(input_cost, 6),
        "note": "Output tokens charged separately based on response length",
    }
