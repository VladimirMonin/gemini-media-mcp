import logging
import os
import sys

# 1. Фикс кодировки для Windows (критично для эмодзи и кириллицы)
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# 2. НАСТРОЙКА ЛОГГЕРА: СТРОГО В STDERR
# Это самое важное изменение. Теперь все print/info летят в поток ошибок,
# оставляя основной канал чистым для JSON-сообщений протокола MCP.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # <--- Направляем логи в stderr [cite: 23]
)
logger = logging.getLogger("gemini-media-mcp")

logger.info("Starting server initialization...")

# Импорт MCP (для версии пакета mcp >= 1.0.0)
try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    logger.error(f"Critical MCP import error: {e}")
    sys.exit(1)

# Импорт database и worker
try:
    from database import DatabaseManager
    from worker import WorkerManager
except ImportError as e:
    logger.error(f"Failed to import database/worker: {e}")
    sys.exit(1)

# Импорт инструментов
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
        queue_generate_audio,
        check_task_status,
        check_batch_progress,
    )
except ImportError as e:
    logger.error(f"Failed to import tools: {e}")
    sys.exit(1)

# Инициализация сервера
# dependencies=["httpx"] помогает, если fastmcp пытается сам что-то догрузить
mcp = FastMCP("gemini-media-analyzer", dependencies=["httpx"])

# Инициализация БД
logger.info("Initializing database...")
db = DatabaseManager()
db.initialize()
logger.info("Database ready")

# Инициализация воркера
logger.info("Starting background worker...")
worker = WorkerManager(db, tick_interval=30)
worker.start()
logger.info("Worker started")

# Регистрация синхронных инструментов (анализ/генерация)
mcp.tool()(analyze_image)
logger.info(f"Tool '{analyze_image.__name__}' registered.")

mcp.tool()(analyze_audio)
mcp.tool()(generate_image)
mcp.tool()(generate_audio_from_yaml)
mcp.tool()(get_audio_generation_guide)
mcp.tool()(analyze_gif)
mcp.tool()(get_gif_guidelines)
mcp.tool()(analyze_video)

# Регистрация batch/queue инструментов (Phase 3)
mcp.tool()(batch_generate_images)
mcp.tool()(queue_generate_audio)
mcp.tool()(check_task_status)
mcp.tool()(check_batch_progress)
logger.info(
    "Batch tools registered: batch_generate_images, queue_generate_audio, check_task_status, check_batch_progress"
)

if __name__ == "__main__":
    try:
        # 3. Явный запуск транспорта stdio
        # Это стандарт для локальных CLI инструментов [cite: 30]
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Critical error during server startup: {e}")
        sys.exit(1)
    finally:
        # Graceful shutdown
        logger.info("Stopping worker...")
        worker.stop(timeout=10)
        logger.info("Closing database...")
        db.close()
        logger.info("Shutdown complete")
