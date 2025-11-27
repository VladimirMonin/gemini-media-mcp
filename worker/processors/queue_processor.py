"""
Queue Processor — обработка задач в режиме local_queue (последовательная обработка).

Используется для операций, которые НЕ поддерживают Google Batch API
(например, TTS из-за бага Google).
"""

import logging
import time

logger = logging.getLogger("gemini-media-mcp.worker.queue_processor")


def process_local_queue_tasks(db) -> int:
    """
    Обработать 1 задачу из local_queue (последовательная обработка).

    Режим local_queue используется для операций БЕЗ поддержки Batch API:
    - TTS_GEN (Batch API возвращает 404 NOT_FOUND)

    Args:
        db: DatabaseManager instance

    Returns:
        1 если задача обработана, 0 если очередь пуста

    Note:
        Обрабатывает только 1 задачу за вызов для соблюдения rate limiting.
        После успешной обработки рекомендуется вызвать time.sleep(10)
        для соблюдения лимита 3-10 RPM для TTS.
    """
    # Получить 1 pending задачу
    tasks = db.get_pending_tasks(limit=1)

    if not tasks:
        logger.debug("Local queue is empty")
        return 0

    task = tasks[0]
    task_id_short = task["id"][:8]

    # Проверить execution_mode
    op_type = db.get_operation_type(task["operation_type"])

    if op_type["execution_mode"] != "local_queue":
        # Это batch задача, пропускаем
        return 0

    logger.info(
        f"Processing local_queue task {task_id_short} ({task['operation_type']})"
    )

    # Обновить статус на PROCESSING
    db.update_task_status(task["id"], "PROCESSING")

    try:
        # === ЗАГЛУШКА для Фазы 2 ===
        # В Фазе 3 здесь будет реальный вызов генератора:
        # payload = task['input_payload']  # уже dict
        # result_path = generate_audio_from_yaml(**payload)

        logger.debug(f"[MOCK] Generating audio for task {task_id_short}...")
        time.sleep(2)  # Имитация работы API
        result_path = task["target_path"]

        # === Конец заглушки ===

        # Обновить статус на COMPLETED
        db.update_task_completed(task["id"], result_path)
        logger.info(f"Task {task_id_short} completed successfully (mock)")

        return 1

    except Exception as e:
        # Обработка ошибок
        logger.error(f"Task {task_id_short} failed: {e}")
        db.update_task_failed(task["id"], str(e))

        return 1
