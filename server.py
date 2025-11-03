"""MCP server for image analysis using Google Gemini API.

This server provides Model Context Protocol tools for analyzing
images with Google's Gemini AI models using FastMCP.
"""

import logging
import os
import sys

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
    from tools.image_analyzer import analyze_image
    from tools.audio_analyzer import analyze_audio
    from tools.image_generator import generate_image
except ImportError as e:
    logger.error(f"Failed to import tools: {e}")
    sys.exit(1)



mcp = FastMCP("gemini-media-analyzer")


mcp.tool()(analyze_image)
logger.info(f"Tool '{analyze_image.__name__}' registered successfully.")
mcp.tool()(analyze_audio)
logger.info(f"Tool '{analyze_audio.__name__}' registered successfully.")
mcp.tool()(generate_image)
logger.info(f"Tool '{generate_image.__name__}' registered successfully.")


if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user (KeyboardInterrupt)")
    except Exception as e:
        logger.exception(f"Critical error during server startup: {e}")
        sys.exit(1)
