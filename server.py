"""MCP server for image analysis using Google Gemini API.

This server provides Model Context Protocol tools and prompts for analyzing
images with Google's Gemini AI models.
"""

import asyncio
import json
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
    from mcp.server import Server, InitializationOptions, NotificationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        TextContent,
        Tool,
        Prompt,
        PromptArgument,
        PromptMessage,
        GetPromptResult,
        LoggingLevel,
    )
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
    from modules.image_analysis import ImageAnalysisModule
    from utils.file_utils import (
        get_file_mime_type,
        is_image_valid,
        SUPPORTED_IMAGE_MIME_TYPES,
    )
except ImportError as e:
    logger.error(f"Local module import error: {e}")
    sys.exit(1)

server = Server("gemini-media-analyzer", version="1.0.0")

try:
    image_analyzer = ImageAnalysisModule(model_name=DEFAULT_GEMINI_MODEL)
    logger.info(f"Image analysis module initialized with model: {DEFAULT_GEMINI_MODEL}")
except ValueError as e:
    logger.error(f"ImageAnalysisModule initialization error: {e}")
    if GEMINI_MODELS:
        logger.info(f"Attempting fallback to model: {GEMINI_MODELS[0]}")
        image_analyzer = ImageAnalysisModule(model_name=GEMINI_MODELS[0])
    else:
        logger.error("No alternative model found")
        sys.exit(1)
except Exception as e:
    logger.exception(f"Unknown error during ImageAnalysisModule initialization: {e}")
    sys.exit(1)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available MCP tools.

    Returns:
        List of available tools for image analysis.
    """
    logger.info("Tools list requested")

    supported_formats = ", ".join(
        [mt.split("/")[-1].upper() for mt in SUPPORTED_IMAGE_MIME_TYPES]
    )

    return [
        Tool(
            name="analyze_image",
            description=(
                f"Analyze images using Google Gemini API. "
                f"Returns structured result with alt-text and detailed analysis. "
                f"Supported formats: {supported_formats}"
            ),
            inputSchema={
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Absolute path to the image file on local machine",
                        "minLength": 1,
                        "pattern": r"^.+\.(jpg|jpeg|png|gif|webp|bmp)$",
                    },
                    "user_prompt": {
                        "type": "string",
                        "description": "Custom analysis request (optional)",
                        "maxLength": 2000,
                        "default": "",
                    },
                    "system_instruction_name": {
                        "type": "string",
                        "description": "Name of predefined system instruction",
                        "enum": list(AVAILABLE_IMAGE_ANALYSIS_PROMPTS.keys()),
                        "default": "default",
                    },
                    "system_instruction_override": {
                        "type": "string",
                        "description": "Custom system instruction (overrides system_instruction_name)",
                        "maxLength": 5000,
                    },
                    "system_instruction_file_path": {
                        "type": "string",
                        "description": "Path to file with system instruction (highest priority)",
                    },
                },
                "required": ["image_path"],
                "additionalProperties": False,
            },
        )
    ]


@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """List available prompts for image analysis.

    Returns:
        List of prompts, one for each predefined system instruction.
    """
    logger.info("Prompts list requested")

    prompts = []
    for name, instruction in AVAILABLE_IMAGE_ANALYSIS_PROMPTS.items():
        prompts.append(
            Prompt(
                name=f"analyze_{name}",
                description=f"Analyze image using {name} prompt: {instruction[:100]}...",
                arguments=[
                    PromptArgument(
                        name="image_path",
                        description="Absolute path to image file",
                        required=True,
                    ),
                    PromptArgument(
                        name="user_prompt",
                        description="Additional analysis request (optional)",
                        required=False,
                    ),
                ],
            )
        )

    logger.info(f"Returning {len(prompts)} prompts")
    return prompts


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> GetPromptResult:
    """Get a specific prompt by name.

    Args:
        name: Prompt name (e.g., "analyze_default").
        arguments: Prompt arguments including image_path and optional user_prompt.

    Returns:
        Formatted prompt result.

    Raises:
        ValueError: If prompt name is invalid or required arguments are missing.
    """
    logger.info(f"Prompt requested: {name}")

    if not name.startswith("analyze_"):
        raise ValueError(f"Unknown prompt: {name}")

    instruction_name = name.replace("analyze_", "")

    if instruction_name not in AVAILABLE_IMAGE_ANALYSIS_PROMPTS:
        raise ValueError(f"Unknown system instruction: {instruction_name}")

    image_path = arguments.get("image_path") if arguments else ""
    user_prompt = arguments.get("user_prompt", "") if arguments else ""

    if not image_path:
        raise ValueError("Argument 'image_path' is required")

    system_instruction = AVAILABLE_IMAGE_ANALYSIS_PROMPTS[instruction_name]

    final_prompt = f"{system_instruction}\n\n"
    if user_prompt:
        final_prompt += f"User request: {user_prompt}\n\n"
    final_prompt += f"Analyze this image: {image_path}"

    return GetPromptResult(
        description=f"Image analysis using {instruction_name} prompt",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=final_prompt,
                ),
            )
        ],
    )


@server.set_logging_level()
async def handle_set_logging_level(level: LoggingLevel) -> None:
    """Set logging level.

    Args:
        level: The logging level to set (debug, info, warning, error, critical).
    """
    logger.info(f"Changing logging level to: {level}")

    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    log_level = level_map.get(level.lower(), logging.INFO)
    logger.setLevel(log_level)


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool invocation.

    Args:
        name: Tool name to invoke.
        arguments: Tool arguments.

    Returns:
        List of text content with analysis results or error messages.
    """
    safe_args = repr(arguments) if arguments else "None"
    logger.info(f"Tool invoked: {name} with arguments: {safe_args}")

    if name != "analyze_image":
        error_msg = f"Unknown tool: {name}"
        logger.error(error_msg)
        return [
            TextContent(
                type="text", text=json.dumps({"error": error_msg}, ensure_ascii=True)
            )
        ]

    if arguments is None:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": "No arguments provided"}, ensure_ascii=True),
            )
        ]

    image_path = arguments.get("image_path", "").strip()
    if not image_path:
        logger.error("Parameter 'image_path' is missing")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": "Parameter 'image_path' is required"}, ensure_ascii=True
                ),
            )
        ]

    if not os.path.exists(image_path):
        logger.error(f"File not found: {image_path}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": f"File not found: {image_path}"}, ensure_ascii=True
                ),
            )
        ]

    if not is_image_valid(image_path):
        mime_type = get_file_mime_type(image_path)
        logger.error(f"Invalid file format: {mime_type}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": f"File is not a supported image. MIME type: {mime_type}"},
                    ensure_ascii=True,
                ),
            )
        ]

    try:
        logger.info(f"Starting image analysis: {image_path}")

        result = image_analyzer.analyze(
            image_path=image_path,
            user_prompt=arguments.get("user_prompt", ""),
            system_instruction_name=arguments.get("system_instruction_name", "default"),
            system_instruction_override=arguments.get("system_instruction_override"),
            system_instruction_file_path=arguments.get("system_instruction_file_path"),
        )

        if "error" in result:
            logger.error(f"Analysis error: {result['error']}")
            return [
                TextContent(
                    type="text", text=json.dumps(result, indent=2, ensure_ascii=True)
                )
            ]

        logger.info("Analysis completed successfully")
        # Успешный результат тоже с ensure_ascii=True
        return [
            TextContent(
                type="text", text=json.dumps(result, indent=2, ensure_ascii=True)
            )
        ]

    except FileNotFoundError as e:
        error_msg = f"File not found during analysis: {e}"
        logger.error(error_msg)
        return [
            TextContent(
                type="text", text=json.dumps({"error": error_msg}, ensure_ascii=True)
            )
        ]

    except IOError as e:
        error_msg = f"I/O error: {e}"
        logger.error(error_msg)
        return [
            TextContent(
                type="text", text=json.dumps({"error": error_msg}, ensure_ascii=True)
            )
        ]

    except Exception as e:
        error_msg = f"Unexpected error during analysis: {e}"
        logger.exception(error_msg)
        return [
            TextContent(
                type="text", text=json.dumps({"error": error_msg}, ensure_ascii=True)
            )
        ]


async def main():
    """Run the MCP server main loop."""
    logger.info("Starting Gemini Image Analyzer MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gemini-media-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user (KeyboardInterrupt)")
    except Exception as e:
        logger.exception(f"Critical error during server startup: {e}")
        sys.exit(1)
