"""MCP server for image analysis using Google Gemini API.

This server provides Model Context Protocol tools for analyzing
images with Google's Gemini AI models using FastMCP.
"""

import asyncio
import logging
import os
import sys

# Простая настройка кодировки для Windows
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

try:
    from utils.logger import get_logger

    logger = get_logger(__name__)
except Exception as e:
    # Fallback если логгер не работает
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"Logger initialization failed: {e}")

logger.info("Starting server import phase...")

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    logger.error(f"Critical MCP import error: {e}")
    logger.error("Try: pip install -r requirements.txt")
    sys.exit(1)

try:
    from config import (
        GEMINI_MODELS,
        DEFAULT_GEMINI_MODEL,
        AVAILABLE_IMAGE_ANALYSIS_PROMPTS,
    )
    from models.analysis import ImageAnalysisResponse, ErrorResponse
    from utils.gemini_client import GeminiClient
    from utils.file_utils import is_image_valid
except ImportError as e:
    logger.error(f"Local module import error: {e}")
    sys.exit(1)

# Инициализация FastMCP сервера
mcp = FastMCP("gemini-media-analyzer")

# Инициализация клиента Gemini
try:
    gemini_client = GeminiClient(model_name=DEFAULT_GEMINI_MODEL)
    logger.info(f"Gemini client initialized with model: {DEFAULT_GEMINI_MODEL}")
except ValueError as e:
    logger.error(f"GeminiClient initialization error: {e}")
    if GEMINI_MODELS:
        logger.info(f"Attempting fallback to model: {GEMINI_MODELS[0]}")
        gemini_client = GeminiClient(model_name=GEMINI_MODELS[0])
    else:
        logger.error("No alternative model found")
        sys.exit(1)
except Exception as e:
    logger.exception(f"Unknown error during GeminiClient initialization: {e}")
    sys.exit(1)


def get_system_instruction(
    name: str = "default",
    override: str | None = None,
    file_path: str | None = None
) -> str | None:
    """Get system instruction with priority handling.
    
    Priority order:
    1. File path (highest priority)
    2. Custom override
    3. Predefined instruction by name
    
    Args:
        name: Name of predefined system instruction.
        override: Custom system instruction string.
        file_path: Path to file with system instruction.
        
    Returns:
        System instruction string or None if not found.
        
    Raises:
        FileNotFoundError: If system instruction file not found.
        IOError: If error reading system instruction file.
    """
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    if override:
        return override
    return AVAILABLE_IMAGE_ANALYSIS_PROMPTS.get(name)


@mcp.tool()
def analyze_image(
    image_path: str,
    user_prompt: str = "",
    system_instruction_name: str = "default",
    system_instruction_override: str | None = None,
    system_instruction_file_path: str | None = None
) -> ImageAnalysisResponse | ErrorResponse:
    """Analyze images using Google Gemini API.
    
    Returns structured result with alt-text and detailed analysis.
    Supported formats: JPEG, PNG, GIF, WEBP, BMP
    
    Args:
        image_path: Absolute path to the image file on local machine.
        user_prompt: Custom analysis request (optional).
        system_instruction_name: Name of predefined system instruction.
        system_instruction_override: Custom system instruction (overrides system_instruction_name).
        system_instruction_file_path: Path to file with system instruction (highest priority).
        
    Returns:
        Structured analysis response with alt-text and detailed analysis.
        
    Raises:
        ValueError: If image is invalid or system instruction not found.
        FileNotFoundError: If image file or system instruction file not found.
        IOError: If error reading files.
    """
    logger.info(f"Starting image analysis: {image_path}")
    
    # Валидация изображения
    if not is_image_valid(image_path):
        raise ValueError(f"File is not a supported image: {image_path}")
    
    # Получение системной инструкции
    try:
        system_instruction = get_system_instruction(
            name=system_instruction_name,
            override=system_instruction_override,
            file_path=system_instruction_file_path
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
    
    # Анализ изображения
    result = gemini_client.analyze_image(
        image_path=image_path,
        user_prompt=user_prompt,
        system_instruction_override=system_instruction
    )
    
    logger.info("Analysis completed successfully")
    return result


if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user (KeyboardInterrupt)")
    except Exception as e:
        logger.exception(f"Critical error during server startup: {e}")
        sys.exit(1)
