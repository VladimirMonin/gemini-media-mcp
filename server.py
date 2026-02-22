"""Основной модуль MCP сервера для работы с медиа-контентом через Gemini API.

Инициализирует MCP сервер с инструментами анализа и генерации медиа-контента.
Запускает фоновый воркер для обработки батч-задач.
"""

import logging
import os
import sys

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("gemini-media-mcp")

logger.info("🚀 Запуск инициализации сервера...")

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    logger.error(f"❌ Критическая ошибка импорта MCP: {e}")
    sys.exit(1)

try:
    from database import DatabaseManager
    from worker import WorkerManager
except ImportError as e:
    logger.error(f"❌ Ошибка импорта database/worker: {e}")
    sys.exit(1)

try:
    from tools.image_analyzer import analyze_image
    from tools.audio_analyzer import analyze_audio
    from tools.image_generator import generate_image
    from tools.audio_generator import (
        generate_audio_from_yaml,
        get_audio_generation_guide,
    )
    from tools.gif_analyzer import analyze_gif, get_gif_guidelines
    from tools.video_analyzer import analyze_video
    from tools.batch_tools import (
        batch_generate_images,
        # TODO: queue_generate_audio отключен — Batch API не поддерживает TTS модели (404 NOT_FOUND).
        # Когда Google добавит поддержку — раскомментировать.
        # queue_generate_audio,
        check_task_status,
        check_batch_progress,
    )
except ImportError as e:
    logger.error(f"❌ Ошибка импорта tools: {e}")
    sys.exit(1)

mcp = FastMCP("gemini-media-analyzer", dependencies=["httpx"])

logger.info("📊 Инициализация базы данных...")
db = DatabaseManager()
db.initialize()
logger.info("✅ База данных готова")

logger.info("🔧 Запуск фонового воркера...")
worker = WorkerManager(db, tick_interval=30)
worker.start()
logger.info("✅ Воркер запущен")

# Регистрация инструментов анализа и генерации
mcp.tool()(analyze_image)
logger.info(f"🔧 Инструмент '{analyze_image.__name__}' зарегистрирован")

mcp.tool()(analyze_audio)
mcp.tool()(generate_image)
mcp.tool()(generate_audio_from_yaml)
mcp.tool()(get_audio_generation_guide)
mcp.tool()(analyze_gif)
mcp.tool()(get_gif_guidelines)
mcp.tool()(analyze_video)

# Регистрация batch/queue инструментов
mcp.tool()(batch_generate_images)
# TODO: queue_generate_audio отключен — TTS не работает через Batch API
# mcp.tool()(queue_generate_audio)
mcp.tool()(check_task_status)
mcp.tool()(check_batch_progress)
logger.info("✅ Batch инструменты зарегистрированы (⚠️ queue_generate_audio отключен)")

if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("⏹️ Сервер остановлен пользователем")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при запуске сервера: {e}")
        sys.exit(1)
    finally:
        logger.info("🔄 Остановка воркера...")
        worker.stop(timeout=10)
        logger.info("🔄 Закрытие базы данных...")
        db.close()
        logger.info("✅ Завершение работы")
