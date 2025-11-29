"""Инструмент генерации изображений через Gemini API.

Функции:
    generate_image(prompt: str, output_path: str, ...) -> str
        Генерирует изображение из текста или редактирует существующее.
"""

import os
from datetime import datetime
from typing import List, Optional, Literal
from PIL import Image
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    IMAGE_GEN_MODELS,
    DEFAULT_IMAGE_GEN_MODEL,
    VALID_ASPECT_RATIOS,
    VALID_RESOLUTIONS,
    OUTPUT_IMAGES_DIR,
    validate_model_for_tier,
)
from utils.logger import get_logger
from utils.backup_manager import backup_generation

logger = get_logger(__name__)


def _resolve_path(path: str) -> str:
    """Преобразует относительные пути в абсолютные."""
    if not path:
        return ""
    return os.path.abspath(os.path.expanduser(path))


def generate_image(
    prompt: str,
    output_path: str,
    image_paths: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "1K",
    model_type: Literal["fast", "pro"] = "fast",
) -> str:
    """Генерирует или редактирует изображение через Gemini API.

    Args:
        prompt: Детальное описание желаемого изображения на английском.
        output_path: Абсолютный путь для сохранения файла.
        image_paths: Список путей к референсным изображениям.
        aspect_ratio: Соотношение сторон.
        resolution: Разрешение ('1K' или '2K').
        model_type: Тип модели ('fast' или 'pro').

    Returns:
        Абсолютный путь к сохранённому изображению.

    Raises:
        ValueError: Неверные параметры или tier не поддерживает генерацию.
        FileNotFoundError: Референсные изображения не найдены.
    """
    # --- 0. Pre-validation logging ---
    logger.info(
        f"🎨 Image Gen Request: model={model_type}, res={resolution}, ar={aspect_ratio}"
    )
    logger.info(f"💾 Target Output: {output_path}")

    # --- 0.5. Tier Validation (CRITICAL for Free tier users) ---
    # Проверяем доступность генерации изображений на текущем tier
    is_available, error_message = validate_model_for_tier("", "image_generation")
    if not is_available:
        logger.error(f"❌ {error_message}")
        raise ValueError(error_message)

    # --- 1. Validate Output Path (Critical) ---
    if not output_path:
        raise ValueError(
            "output_path is missing. The agent must specify an absolute path to save the file."
        )

    final_path = _resolve_path(output_path)

    # Check if path is a directory (it must be a file)
    if os.path.isdir(final_path):
        raise ValueError(
            f"output_path '{final_path}' is a directory. Please specify a full file path including the filename (e.g., .../image.png)."
        )

    # Ensure valid extension
    if not final_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        final_path += ".png"
        logger.info(f"🔄 Appended extension: {final_path}")

    # --- 2. Validate Parameters ---
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        logger.warning(
            f"⚠️ Invalid aspect_ratio '{aspect_ratio}'. Resetting to default '16:9'."
        )
        aspect_ratio = "16:9"

    if resolution not in VALID_RESOLUTIONS:
        logger.warning(f"⚠️ Invalid resolution '{resolution}'. Resetting to '1K'.")
        resolution = "1K"

    # API Limit Check: Flash model only supports 1K
    if model_type == "fast" and resolution != "1K":
        logger.warning(
            f"⚠️ Model 'fast' (Flash) does not support {resolution}. Downgrading to 1K."
        )
        resolution = "1K"

    # Resolve model name from config
    selected_model = IMAGE_GEN_MODELS.get(
        model_type, IMAGE_GEN_MODELS.get(DEFAULT_IMAGE_GEN_MODEL)
    )
    if not selected_model:
        selected_model = "gemini-2.5-flash-image"  # Hard fallback

    # --- 3. Prepare Content (Prompt + Images) ---
    contents = [prompt]

    if image_paths:
        valid_images_count = 0
        for raw_path in image_paths:
            path = _resolve_path(raw_path)
            if os.path.exists(path):
                try:
                    # Gemini SDK handles PIL images natively in contents list
                    img = Image.open(path)
                    contents.append(img)
                    valid_images_count += 1
                    logger.debug(f"📎 Loaded reference image: {path}")
                except Exception as e:
                    logger.error(f"❌ Failed to load reference image {path}: {e}")
            else:
                logger.error(f"❌ Reference image not found at path: {path}")

        # If inputs were provided but none were valid, fail fast
        if valid_images_count == 0 and image_paths:
            raise FileNotFoundError(
                f"Could not load any of the provided reference images: {image_paths}"
            )

    # --- 4. Configure and Call API ---
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Construct ImageConfig
        # Only pass image_size if strictly necessary to avoid Pydantic validation errors in SDK
        img_config_params = {"aspect_ratio": aspect_ratio}

        if model_type == "pro" and resolution != "1K":
            img_config_params["image_size"] = resolution

        gen_config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],  # We only want the image blob
            image_config=types.ImageConfig(**img_config_params),
        )

        logger.info(f"🚀 Sending request to Gemini ({selected_model})...")
        logger.info(f"📝 Prompt (start): {prompt[:100]}...")

        response = client.models.generate_content(
            model=selected_model, contents=contents, config=gen_config
        )

        # --- 5. Handle Response ---
        if not response.candidates:
            # Usually happens if safety filters block the request
            raise ValueError(
                "API returned no candidates. The prompt might have triggered safety filters."
            )

        generated_image_part = None
        # Iterate through parts to find the inline_data (image blob)
        if response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    generated_image_part = part
                    break

        if not generated_image_part:
            # Extract text error if present
            text_error = "Unknown error"
            if response.candidates[0].content and response.candidates[0].content.parts:
                text_part = response.candidates[0].content.parts[0]
                if text_part.text:
                    text_error = text_part.text

            raise ValueError(
                f"Model returned text instead of an image. This often means the model refused the request. Response: {text_error}"
            )

        # --- 6. Save to Disk ---
        image_bytes = generated_image_part.inline_data.data

        # Ensure directory exists
        os.makedirs(os.path.dirname(final_path), exist_ok=True)

        with open(final_path, "wb") as f:
            f.write(image_bytes)

        logger.info(f"✅ Image successfully saved to: {final_path}")

        # --- Backup to output/images/ with metadata ---
        try:
            backup_metadata = {
                "timestamp": datetime.now().isoformat(),
                "file_path": final_path,
                "parameters": {
                    "prompt": prompt,
                    "model_type": model_type,
                    "model": selected_model,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "reference_images": image_paths if image_paths else None,
                },
            }
            backup_path, metadata_path = backup_generation(
                original_path=final_path,
                file_type="image",
                metadata=backup_metadata,
            )
            logger.info(f"📦 Backup created: {backup_path}")
        except Exception as backup_error:
            logger.warning(f"⚠️ Backup failed (non-critical): {backup_error}")

        return final_path

    except Exception as e:
        logger.exception(f"❌ Image generation process failed: {e}")
        # Return a clean error message to the agent
        return f"Error generating image: {str(e)}"
