"""Инструмент анализа GIF-анимаций через Gemini API.

Функции:
    analyze_gif(image_path: str, prompt: str, ...) -> dict
        Анализирует GIF-анимацию с извлечением ключевых кадров.
    get_gif_guidelines() -> str
        Возвращает руководство по анализу GIF.
"""

from typing import Literal, Optional
from PIL import Image

from config import (
    GIF_QUALITY_PRESETS,
    DEFAULT_GIF_QUALITY,
    DEFAULT_GIF_MODEL,
    DEFAULT_GIF_ANALYSIS_SYSTEM_PROMPT,
    GIF_USER_GUIDELINES,
)
from utils.gif_processor import (
    extract_gif_frames,
    resize_image,
    create_animation_prompt,
)
from utils.image_tokens import calculate_images_tokens, estimate_cost
from utils.gemini_client import GeminiClient
from utils.logger import get_logger

logger = get_logger(__name__)


async def analyze_gif(
    image_path: str,
    prompt: str = "Analyze this animation and describe what it demonstrates",
    mode: Literal["fps", "total", "interval"] = "total",
    gif_fps: Optional[float] = None,
    frame_count: int = 5,
    interval_sec: Optional[float] = None,
    quality: Literal["uhd", "fhd", "hd", "balanced", "economy"] = DEFAULT_GIF_QUALITY,
    model: str = DEFAULT_GIF_MODEL,
) -> dict:
    """Анализирует GIF-анимацию через Gemini AI.

    Извлекает ключевые кадры из анимации и анализирует их как последовательность,
    понимая как отдельные кадры, так и общий нарратив анимации.

    Args:
        image_path: Путь к GIF-файлу.
        prompt: Запрос на анализ.
        mode: Стратегия извлечения кадров ('total', 'fps', 'interval').
        gif_fps: Кадров в секунду для режима 'fps'.
        frame_count: Количество кадров для режима 'total'.
        interval_sec: Интервал в секундах для режима 'interval'.
        quality: Пресет качества ('uhd', 'fhd', 'hd', 'balanced', 'economy').
        model: Модель Gemini для анализа.

    Returns:
        Словарь с результатами анализа и метаданными.
    """
    try:
        logger.info("=" * 80)
        logger.info(f"🎬 GIF ANALYSIS STARTED: {image_path}")
        logger.info(f"📊 Parameters: mode={mode}, quality={quality}, model={model}")
        logger.info(
            f"🔧 Extraction: frame_count={frame_count}, gif_fps={gif_fps}, interval_sec={interval_sec}"
        )

        # Load GIF
        image = Image.open(image_path)

        if not getattr(image, "is_animated", False):
            logger.warning(f"❌ File is not animated: {image_path}")
            return {
                "error": "File is not an animated GIF",
                "suggestion": "Use 'analyze_image' tool for static images",
            }

        # Extract frames
        frames = extract_gif_frames(
            image,
            mode=mode,
            gif_fps=gif_fps,
            frame_count=frame_count,
            interval_sec=interval_sec,
        )

        logger.info(f"✅ Extracted {len(frames)} frames from animation")

        # Resize frames based on quality preset
        max_dimension = GIF_QUALITY_PRESETS.get(quality, 1920)
        processed_frames = [resize_image(f, max_dimension) for f in frames]

        # Calculate tokens using centralized module
        token_info = calculate_images_tokens(processed_frames)
        logger.info(f"💰 Token calculation:\n{token_info['breakdown']}")

        # Estimate cost
        cost_info = estimate_cost(token_info["total_tokens"], model)
        logger.info(
            f"💵 Estimated cost: ${cost_info['estimated_input_cost_usd']:.6f} USD "
            f"({token_info['total_tokens']:,} tokens @ {model})"
        )

        # Create extraction info for prompt
        if mode == "fps":
            fps_value = gif_fps if gif_fps else 1.0
            extraction_info = f"Extracted at {fps_value} FPS (1 frame every {1.0 / fps_value:.1f} seconds)"
        elif mode == "total":
            extraction_info = (
                f"{len(frames)} frames evenly distributed across the entire animation"
            )
        else:  # interval
            extraction_info = f"Frames extracted every {interval_sec} seconds"

        # Create enhanced prompt with system prompt
        enhanced_prompt = create_animation_prompt(
            prompt,
            len(processed_frames),
            extraction_info,
            DEFAULT_GIF_ANALYSIS_SYSTEM_PROMPT,
        )

        # Call Gemini API with multi-image method
        logger.info(f"🚀 Sending {len(processed_frames)} frames to Gemini ({model})...")
        client = GeminiClient(model_name=model)

        response_text = client.generate_content_multi_image(
            prompt=enhanced_prompt,
            images=processed_frames,  # List of PIL Images
            temperature=0.7,
        )

        logger.info(f"✅ Analysis completed successfully for {image_path}")
        logger.info(
            f"📈 Summary: {len(frames)} frames, {token_info['total_tokens']:,} tokens, "
            f"${cost_info['estimated_input_cost_usd']:.6f} USD"
        )
        logger.info("=" * 80)

        return {
            "analysis": response_text,
            "metadata": {
                "frame_count": len(frames),
                "mode": mode,
                "quality": quality,
                "tokens": token_info,
                "estimated_cost": cost_info,
                "model": model,
                "extraction_params": {
                    "gif_fps": gif_fps,
                    "frame_count": frame_count,
                    "interval_sec": interval_sec,
                },
            },
        }

    except FileNotFoundError:
        logger.error(f"❌ File not found: {image_path}")
        return {
            "error": "File not found",
            "path": image_path,
        }
    except Exception as e:
        logger.exception("GIF analysis failed")
        return {
            "error": "GIF analysis failed",
            "details": str(e),
        }


async def get_gif_guidelines() -> str:
    """Возвращает руководство по анализу GIF-анимаций."""
    return GIF_USER_GUIDELINES
