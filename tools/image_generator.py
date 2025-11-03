"""Image generation tool for the Gemini Media MCP server."""

import os
from typing import List, Optional
from PIL import Image
from io import BytesIO
from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_image(
    user_prompt: str,
    image_paths: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate image based on text prompt and optional reference images.

    Args:
        user_prompt (str): Text description for generation.
        image_paths (Optional[List[str]]): List of ABSOLUTE paths to reference images.
        output_path (Optional[str]): ABSOLUTE path for saving the generated image.

    Returns:
        str: Absolute path to the saved image.

    Raises:
        ValueError: If image generation failed.
        FileNotFoundError: If reference image file not found.
        IOError: If error saving image.
    """
    logger.info(f"Starting image generation with prompt: {user_prompt[:50]}...")
    
    # Use image generation model
    model_name = "gemini-2.5-flash-image-preview"
    
    # Create content for request
    contents = [user_prompt]
    
    # Add reference images if provided
    if image_paths:
        for image_path in image_paths:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found at path: {image_path}")
            
            try:
                img = Image.open(image_path)
                contents.append(img)
                logger.debug(f"Added reference image: {image_path}")
            except Exception as e:
                raise IOError(f"Error opening image {image_path}: {e}")

    # Initialize client and generate content
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Call generate_content and get full response object
        response = client.models.generate_content(
            model=model_name,
            contents=contents
        )
        
        # Extract image data from response
        image_part = None
        if (response.candidates and len(response.candidates) > 0 and 
            hasattr(response.candidates[0], 'content') and response.candidates[0].content and
            hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts):
            for part in response.candidates[0].content.parts:
                if (hasattr(part, 'inline_data') and part.inline_data and 
                    hasattr(part.inline_data, 'data') and part.inline_data.data):
                    image_part = part
                    break
        
        if not image_part:
            raise ValueError("Could not generate image. The API did not return image data.")
        
        # Get binary image data
        image_bytes = image_part.inline_data.data
        
        if not image_bytes:
            raise ValueError("Could not generate image. The API returned empty image data.")
        
        # Determine save path
        if output_path:
            final_path = output_path
        else:
            # If path not specified, save to current directory with default name
            final_path = "generated_image.png"
        
        # Save image
        with open(final_path, "wb") as f:
            f.write(image_bytes)
        
        absolute_path = os.path.abspath(final_path)
        logger.info(f"Image successfully generated and saved to: {absolute_path}")
        
        return absolute_path
        
    except Exception as e:
        logger.exception(f"Failed to generate image: {e}")
        raise
