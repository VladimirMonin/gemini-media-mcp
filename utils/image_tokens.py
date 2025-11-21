"""Token calculation utilities for Gemini API media processing.

Based on official Gemini documentation:
https://ai.google.dev/gemini-api/docs/image-understanding#token-calculation
"""

from typing import List
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_image_tokens(image: Image.Image) -> int:
    """Calculate token count for a single image.

    Token calculation logic based on Gemini documentation:
    - Images ≤384px (both dimensions): 258 tokens
    - Larger images: Tiled at 768×768px, each tile = 258 tokens

    Formula for tiles:
    1. crop_unit = floor(min(width, height) / 1.5)
    2. tiles = (width / crop_unit) × (height / crop_unit)

    Args:
        image: PIL Image object

    Returns:
        Estimated token count for this image

    Examples:
        >>> img = Image.open("small.jpg")  # 300×200
        >>> calculate_image_tokens(img)
        258

        >>> img = Image.open("large.jpg")  # 960×540
        >>> calculate_image_tokens(img)  # crop_unit=360, tiles=3×2=6
        1548  # 6 × 258
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
    """Calculate total tokens for multiple images.

    Args:
        images: List of PIL Image objects

    Returns:
        dict with breakdown:
        {
            'total_tokens': int,
            'image_count': int,
            'per_image': [int, ...],
            'breakdown': str
        }

    Example:
        >>> images = [img1, img2, img3]
        >>> result = calculate_images_tokens(images)
        >>> print(result['breakdown'])
        Image 1 (1920×1080): 1,548 tokens
        Image 2 (800×600): 258 tokens
        Image 3 (3840×2160): 6,192 tokens
        Total: 7,998 tokens
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

    logger.info(f"Calculated tokens for {len(images)} images: {total:,} total")

    return {
        "total_tokens": total,
        "image_count": len(images),
        "per_image": per_image_tokens,
        "breakdown": breakdown,
    }


def estimate_cost(tokens: int, model: str = "gemini-2.5-flash") -> dict:
    """Estimate API cost based on token count.

    Pricing as of 2025 (check current rates at https://ai.google.dev/pricing):
    - Flash models: Lower cost per token
    - Pro models: Higher cost per token

    Args:
        tokens: Total token count
        model: Model name

    Returns:
        dict with cost estimates

    Example:
        >>> estimate_cost(7500, "gemini-2.5-flash")
        {
            'tokens': 7500,
            'model': 'gemini-2.5-flash',
            'estimated_input_cost_usd': 0.000141,
            'note': 'Output tokens charged separately...'
        }
    """
    # Pricing tiers (example - update with actual rates)
    # Free tier: 1,500 requests per day, 1 million tokens per minute
    pricing = {
        "gemini-2.5-flash-lite": {
            "input": 0.00001875,
            "output": 0.000075,
        },  # per 1K tokens
        "gemini-2.5-flash": {"input": 0.00001875, "output": 0.000075},
        "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-2.0-flash": {"input": 0.00001875, "output": 0.000075},
    }

    rates = pricing.get(model, pricing["gemini-2.5-flash"])
    input_cost = (tokens / 1000) * rates["input"]

    return {
        "tokens": tokens,
        "model": model,
        "estimated_input_cost_usd": round(input_cost, 6),
        "note": "Output tokens charged separately based on response length",
    }
