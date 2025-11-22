"""Image generation tool for the Gemini Media MCP server."""

import os
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
)
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_image(
    prompt: str,
    image_paths: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "1K",
    output_path: Optional[str] = None,
    model_type: Literal["fast", "pro"] = "fast",
) -> str:
    """
    Generate or edit images using Google Gemini models.

    This tool can generate images from scratch (text-to-image) or modify existing images
    based on text instructions (image-to-image / inpainting).

    IMPORTANT FOR THE ASSISTANT:
    1. **Language**: Translate the `prompt` to detailed ENGLISH before calling this tool
       for the best quality and text rendering accuracy.
    2. **Editing**: To edit an image, provide the file path in `image_paths` and describe
       the desired changes in the `prompt` (e.g., "Change the cat to a dog", "Add a hat").
    3. **Model Selection**:
       - Use 'fast' (Gemini 2.5 Flash) for quick drafts. Max resolution is 1K.
       - Use 'pro' (Gemini 3 Pro) for high detail, text rendering, or 2K/4K output.

    Args:
        prompt (str): Detailed description of the image to generate or edits to make.
                      MUST be in English.
        image_paths (Optional[List[str]]): List of absolute paths to reference images for editing
                                           or style transfer. Max 5 images for characters/style.
        aspect_ratio (str): Aspect ratio of the output.
                            Options: '1:1', '16:9', '9:16', '4:3', '3:4', etc. Default: '16:9'.
        resolution (str): Output resolution. Options: '1K', '2K', '4K'.
                          Note: '2K' and '4K' are ONLY supported by 'pro' model_type.
        output_path (Optional[str]): Absolute path to save the result.
        model_type (Literal['fast', 'pro']): Model speed/quality trade-off. Default: 'fast'.

    Returns:
        str: Absolute path to the saved image file.
    """
    logger.info(
        f"🎨 Image Gen Request: model={model_type}, res={resolution}, ar={aspect_ratio}"
    )
    logger.info(f"📝 Prompt: {prompt[:100]}...")

    # 1. Validation
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        logger.warning(f"Invalid aspect_ratio '{aspect_ratio}'. Resetting to 16:9.")
        aspect_ratio = "16:9"

    if resolution not in VALID_RESOLUTIONS:
        logger.warning(f"Invalid resolution '{resolution}'. Resetting to 1K.")
        resolution = "1K"

    # Force 1K resolution for Flash model (API limitation)
    if model_type == "fast" and resolution != "1K":
        logger.warning(
            f"⚠️ Model 'fast' (Flash) supports max 1K resolution. Downgrading {resolution} -> 1K."
        )
        resolution = "1K"

    selected_model = IMAGE_GEN_MODELS.get(
        model_type, IMAGE_GEN_MODELS[DEFAULT_IMAGE_GEN_MODEL]
    )

    # 2. Prepare Content
    contents = [prompt]

    if image_paths:
        valid_images_count = 0
        for path in image_paths:
            if os.path.exists(path):
                try:
                    # Gemini SDK handles PIL images directly in contents
                    img = Image.open(path)
                    contents.append(img)
                    valid_images_count += 1
                    logger.debug(f"📎 Added reference: {path}")
                except Exception as e:
                    logger.error(f"❌ Error loading reference {path}: {e}")
            else:
                logger.error(f"❌ Reference image not found: {path}")

        if valid_images_count == 0 and image_paths:
            raise FileNotFoundError(
                "No valid reference images could be loaded from the provided list."
            )

    # 3. Initialize Client & Config
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Construct ImageConfig
        img_config = types.ImageConfig(aspect_ratio=aspect_ratio, image_size=resolution)

        gen_config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],  # We only want the image
            image_config=img_config,
        )

        # 4. Call API
        logger.info(f"🚀 Sending request to {selected_model}...")
        response = client.models.generate_content(
            model=selected_model, contents=contents, config=gen_config
        )

        # 5. Handle Response
        if not response.candidates:
            raise ValueError(
                "API returned no candidates. Request might have been blocked."
            )

        # Gemini Native returns parts. We look for inline_data
        generated_image_part = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                generated_image_part = part
                break

        if not generated_image_part:
            # Иногда модель может вернуть текст отказа вместо картинки
            text_part = (
                response.candidates[0].content.parts[0].text
                if response.candidates[0].content.parts
                else "Unknown error"
            )
            raise ValueError(f"Model returned text instead of image: {text_part}")

        image_bytes = generated_image_part.inline_data.data

        # 6. Save Output
        if output_path:
            final_path = output_path
            if not final_path.lower().endswith((".png", ".jpg", ".jpeg")):
                final_path += ".png"
        else:
            # Create generic filename if none provided
            import time

            filename = f"gen_{model_type}_{resolution}_{int(time.time())}.png"
            # Save in current working directory or a temp folder
            final_path = os.path.abspath(filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(final_path)), exist_ok=True)

        with open(final_path, "wb") as f:
            f.write(image_bytes)

        logger.info(f"✅ Image saved to: {final_path}")
        return final_path

    except Exception as e:
        logger.exception(f"❌ Image generation failed: {e}")
        return f"Error generating image: {str(e)}"
