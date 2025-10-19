"""
MCP Сервер для анализа изображений с использованием Google Gemini API.
"""

import asyncio
import json
import logging
import os
import sys

# Установка корневого логгера для MCP
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gemini-media-mcp-server")

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
    logger.error(
        f"Критическая ошибка импорта MCP: {e}. Убедитесь, что все зависимости из requirements.txt установлены в виртуальном окружении."
    )
    logger.error("Попробуйте: pip install -r requirements.txt")
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
    logger.error(
        f"Ошибка импорта локальных модулей: {e}. Убедитесь, что структура проекта корректна."
    )
    sys.exit(1)

# Инициализация Gemini SDK
# Конфигурация теперь выполняется внутри GeminiClient при его создании
# genai.configure(api_key=GEMINI_API_KEY)

# Инициализация MCP сервера
server = Server("gemini-media-analyzer", version="1.0.0")

# Инициализация модуля анализа изображений
try:
    image_analyzer = ImageAnalysisModule(model_name=DEFAULT_GEMINI_MODEL)
    logger.info(
        f"Модуль анализа изображений инициализирован с моделью {DEFAULT_GEMINI_MODEL}"
    )
except ValueError as e:
    logger.error(f"Ошибка инициализации ImageAnalysisModule: {e}")
    if GEMINI_MODELS:
        logger.info(
            f"Попытка инициализации с альтернативной моделью: {GEMINI_MODELS[0]}"
        )
        image_analyzer = ImageAnalysisModule(model_name=GEMINI_MODELS[0])
    else:
        logger.error("Не удалось найти альтернативную модель.")
        sys.exit(1)
except Exception as e:  # Общий случай, если что-то пошло не так
    logger.error(f"Неизвестная ошибка при инициализации ImageAnalysisModule: {e}")
    sys.exit(1)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Список доступных инструментов."""
    logger.info("Запрос списка инструментов")

    return [
        Tool(
            name="analyze_image",
            description=(
                "Анализирует изображение с помощью Google Gemini API. "
                "Возвращает структурированный результат с alt-текстом и детальным описанием. "
                f"Поддерживаемые форматы: {', '.join([mt.split('/')[-1].upper() for mt in SUPPORTED_IMAGE_MIME_TYPES])}"
            ),
            inputSchema={
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Абсолютный путь к файлу изображения на локальной машине",
                        "minLength": 1,
                        "pattern": r"^.+\.(jpg|jpeg|png|gif|webp|bmp)$",
                    },
                    "user_prompt": {
                        "type": "string",
                        "description": "Пользовательский запрос для анализа изображения (опционально)",
                        "maxLength": 2000,
                        "default": "",
                    },
                    "system_instruction_name": {
                        "type": "string",
                        "description": "Имя предустановленной системной инструкции",
                        "enum": list(AVAILABLE_IMAGE_ANALYSIS_PROMPTS.keys()),
                        "default": "default",
                    },
                    "system_instruction_override": {
                        "type": "string",
                        "description": "Кастомная системная инструкция (переопределяет system_instruction_name)",
                        "maxLength": 5000,
                    },
                    "system_instruction_file_path": {
                        "type": "string",
                        "description": "Путь к файлу с системной инструкцией (наивысший приоритет)",
                    },
                },
                "required": ["image_path"],
                "additionalProperties": False,
            },
        )
    ]


@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """Список доступных промптов для анализа изображений."""
    logger.info("Запрос списка промптов")

    prompts = []

    # Создаем промпт для каждой предустановленной системной инструкции
    for name, instruction in AVAILABLE_IMAGE_ANALYSIS_PROMPTS.items():
        prompts.append(
            Prompt(
                name=f"analyze_{name}",
                description=f"Анализ изображения с использованием {name} промпта: {instruction[:100]}...",
                arguments=[
                    PromptArgument(
                        name="image_path",
                        description="Абсолютный путь к файлу изображения",
                        required=True,
                    ),
                    PromptArgument(
                        name="user_prompt",
                        description="Дополнительный запрос для анализа (опционально)",
                        required=False,
                    ),
                ],
            )
        )

    logger.info(f"Возвращено {len(prompts)} промптов")
    return prompts


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> GetPromptResult:
    """Получение конкретного промпта."""
    logger.info(f"Запрос промпта: {name}")

    # Извлекаем имя системной инструкции из имени промпта
    # Например: "analyze_default" -> "default"
    if not name.startswith("analyze_"):
        raise ValueError(f"Неизвестный промпт: {name}")

    instruction_name = name.replace("analyze_", "")

    if instruction_name not in AVAILABLE_IMAGE_ANALYSIS_PROMPTS:
        raise ValueError(f"Неизвестная системная инструкция: {instruction_name}")

    # Получаем аргументы
    image_path = arguments.get("image_path") if arguments else ""
    user_prompt = arguments.get("user_prompt", "") if arguments else ""

    if not image_path:
        raise ValueError("Аргумент 'image_path' обязателен")

    # Формируем системную инструкцию
    system_instruction = AVAILABLE_IMAGE_ANALYSIS_PROMPTS[instruction_name]

    # Формируем финальный промпт
    final_prompt = f"{system_instruction}\n\n"
    if user_prompt:
        final_prompt += f"Запрос пользователя: {user_prompt}\n\n"
    final_prompt += f"Проанализируй изображение: {image_path}"

    return GetPromptResult(
        description=f"Анализ изображения с {instruction_name} промптом",
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
    """Установка уровня логирования."""
    logger.info(f"Изменение уровня логирования на: {level}")

    # Преобразуем LoggingLevel в уровень logging
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
    """Обработка вызова инструмента."""
    logger.info(f"Вызов инструмента: {name} с аргументами: {arguments}")

    if name != "analyze_image":
        error_msg = f"Неизвестный инструмент: {name}"
        logger.error(error_msg)
        return [
            TextContent(
                type="text", text=json.dumps({"error": error_msg}, ensure_ascii=False)
            )
        ]

    # Валидация аргументов
    if arguments is None:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": "Аргументы не предоставлены"}, ensure_ascii=False
                ),
            )
        ]

    image_path = arguments.get("image_path", "").strip()
    if not image_path:
        logger.error("Параметр 'image_path' отсутствует")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": "Параметр 'image_path' обязателен"}, ensure_ascii=False
                ),
            )
        ]

    # Проверка существования файла
    if not os.path.exists(image_path):
        logger.error(f"Файл не найден: {image_path}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": f"Файл не найден: {image_path}"}, ensure_ascii=False
                ),
            )
        ]

    # Проверка валидности изображения
    if not is_image_valid(image_path):
        mime_type = get_file_mime_type(image_path)
        logger.error(f"Неверный формат файла: {mime_type}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Файл не является поддерживаемым изображением. MIME тип: {mime_type}"
                    },
                    ensure_ascii=False,
                ),
            )
        ]

    # Анализ изображения
    try:
        logger.info(f"Начало анализа изображения: {image_path}")

        result = image_analyzer.analyze(
            image_path=image_path,
            user_prompt=arguments.get("user_prompt", ""),
            system_instruction_name=arguments.get("system_instruction_name", "default"),
            system_instruction_override=arguments.get("system_instruction_override"),
            system_instruction_file_path=arguments.get("system_instruction_file_path"),
        )

        # Если есть ошибка в результате
        if "error" in result:
            logger.error(f"Ошибка анализа: {result['error']}")
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        logger.info("Анализ успешно завершен")
        return [
            TextContent(
                type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
            )
        ]

    except FileNotFoundError as e:
        error_msg = f"Файл не найден во время анализа: {e}"
        logger.error(error_msg)
        return [
            TextContent(
                type="text", text=json.dumps({"error": error_msg}, ensure_ascii=False)
            )
        ]

    except IOError as e:
        error_msg = f"Ошибка ввода-вывода: {e}"
        logger.error(error_msg)
        return [
            TextContent(
                type="text", text=json.dumps({"error": error_msg}, ensure_ascii=False)
            )
        ]

    except Exception as e:
        error_msg = f"Неожиданная ошибка при анализе: {e}"
        logger.error(error_msg, exc_info=True)
        return [
            TextContent(
                type="text", text=json.dumps({"error": error_msg}, ensure_ascii=False)
            )
        ]


async def main():
    """Главная функция запуска сервера."""
    logger.info("Запуск Gemini Image Analyzer MCP сервера...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gemini-image-mcp-server",
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
        logger.info("Сервер остановлен пользователем (KeyboardInterrupt).")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске сервера: {e}", exc_info=True)
        sys.exit(1)
