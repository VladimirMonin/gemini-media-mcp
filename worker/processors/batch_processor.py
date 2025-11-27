"""
Batch Processor — обработка задач через Google Batch API.

Используется для операций с поддержкой Batch API (50% скидка):
- IMG_GEN_BATCH
- IMG_ANALYZE_BATCH
- VIDEO_ANALYZE_BATCH
- GIF_ANALYZE_BATCH
"""

import logging
import os

import google.genai as genai

from config import GEMINI_API_KEY, get_batch_model

logger = logging.getLogger("gemini-media-mcp.worker.batch_processor")

# Feature flag: включить реальный Batch API или использовать моки
ENABLE_BATCH_API = os.getenv("ENABLE_BATCH_API", "true").lower() == "true"

# Инициализация клиента Google Batch API
client = None
if ENABLE_BATCH_API:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Google Batch API client initialized (real mode)")
    except Exception as e:
        logger.error(f"Failed to initialize Google Batch API client: {e}")
        logger.warning("Falling back to MOCK mode")
        ENABLE_BATCH_API = False
        client = None
else:
    logger.info("ENABLE_BATCH_API=false → using MOCK mode (no API calls)")


def submit_pending_batches(db) -> int:
    """
    Фаза 1: Отправка PENDING задач в Google Batch API.

    Алгоритм:
    1. Получить pending batches (не задачи!)
    2. Отфильтровать только batch-режим (execution_mode='batch')
    3. Для каждого пакета:
       - Получить все задачи этого пакета
       - Сформировать inline_requests из input_payload каждой задачи
       - Вызвать client.batches.create() или mock
       - Получить google_batch_id
       - Обновить статусы (batch → SUBMITTED, tasks → SUBMITTED)

    Args:
        db: DatabaseManager instance

    Returns:
        Количество отправленных пакетов

    Raises:
        Exception: При ошибках API — пакет помечается как FAILED
    """
    # Получить pending батчи (не задачи!)
    pending_batches = db.get_pending_batches()

    # Фильтр: только batch-режим
    batch_mode_batches = []
    for batch in pending_batches:
        # Получить первую задачу пакета, чтобы узнать operation_type
        tasks_in_batch = [
            t
            for t in db.get_pending_tasks(limit=1000)
            if t.get("batch_id") == batch["id"]
        ]

        if not tasks_in_batch:
            logger.warning(f"Batch {batch['id']} has no tasks, skipping")
            continue

        # Проверить execution_mode через operation_type первой задачи
        first_task = tasks_in_batch[0]
        op_type = db.get_operation_type(first_task["operation_type"])

        if op_type["execution_mode"] == "batch":
            batch_mode_batches.append({"batch": batch, "tasks": tasks_in_batch})

    submitted_count = 0

    for item in batch_mode_batches:
        batch = item["batch"]
        tasks = item["tasks"]
        batch_id = batch["id"]

        logger.info(f"Submitting batch {batch_id} with {len(tasks)} tasks")

        try:
            if not ENABLE_BATCH_API:
                # MOCK режим: создать фейковый google_batch_id для тестов
                fake_google_id = f"batches/mock_{batch_id[:8]}"
                logger.info(f"[MOCK] Created fake batch: {fake_google_id}")

                # Обновить статус пакета
                db.update_batch_status(batch_id, "SUBMITTED", fake_google_id)

                # Обновить статусы всех задач в пакете
                for task in tasks:
                    db.update_task_status(task["id"], "SUBMITTED")

                submitted_count += 1
            else:
                # РЕАЛЬНЫЙ режим: отправка в Google Batch API

                # Формируем inline_requests из input_payload каждой задачи
                # Note: inline режим НЕ поддерживает custom_id (только для file-based метода)
                # Порядок результатов гарантирован для <20MB батчей (документация Google)
                # TODO Phase 3 Step 3: Переход на file-based режим при необходимости (>20MB)
                inline_requests = []
                for task in tasks:
                    input_payload = task.get("input_payload", {})

                    # Для IMG_GEN_BATCH: input_payload = {"prompt": "..."}
                    prompt = input_payload.get("prompt", "")

                    request = {
                        "contents": [{"parts": [{"text": prompt}], "role": "user"}]
                    }
                    inline_requests.append(request)

                # Динамически выбираем модель по operation_type
                operation_type = tasks[0]["operation_type"]
                # Передаём input_payload первой задачи для извлечения model_type (fast/pro)
                first_payload = tasks[0].get("input_payload", {})
                model = get_batch_model(operation_type, first_payload)

                logger.info(f"Selected model: {model} (operation: {operation_type})")

                # Вызываем Batch API
                # TODO Phase 4: Exponential backoff для transient ошибок (429, 503)
                result = client.batches.create(model=model, src=inline_requests)

                google_batch_id = result.name  # "batches/abc123xyz..."
                logger.info(f"✅ Batch submitted: {google_batch_id}")

                # Обновить статус пакета
                db.update_batch_status(batch_id, "SUBMITTED", google_batch_id)

                # Обновить статусы всех задач в пакете
                for task in tasks:
                    db.update_task_status(task["id"], "SUBMITTED")

                submitted_count += 1

        except Exception as e:
            logger.error(f"❌ Failed to submit batch {batch_id}: {e}")
            # Пометить пакет как FAILED (error message залогирован выше)
            db.update_batch_status(batch_id, "FAILED")

    logger.info(f"Submitted {submitted_count}/{len(batch_mode_batches)} batches")
    return submitted_count


def poll_active_batches(db) -> int:
    """
    Фаза 3 Шаг 2: Проверка статусов активных пакетов в Google Batch API.

    Алгоритм:
    1. Получить пакеты со статусом SUBMITTED/PROCESSING с google_batch_id
    2. Для каждого пакета:
       - Если Mock ID (batches/mock_*) → эмулировать переход к COMPLETED
       - Если Real ID → запросить статус через client.batches.get()
       - Преобразовать Google статус в DB статус через STATUS_MAP
       - Обновить БД только если статус изменился
    3. Обработать ошибки (404, rate limits) без краша

    Args:
        db: DatabaseManager instance

    Returns:
        Количество обработанных пакетов (с обновлённым статусом или без)

    Status Mapping (Google → DB):
        JOB_STATE_PENDING    → SUBMITTED (или PROCESSING если хотим видеть движение)
        JOB_STATE_RUNNING    → PROCESSING
        JOB_STATE_SUCCEEDED  → COMPLETED (сигнал для Шага 3)
        JOB_STATE_FAILED     → FAILED
        JOB_STATE_CANCELLED  → FAILED
    """
    # 1. Получить активные пакеты (SUBMITTED или PROCESSING) с google_batch_id
    batches = db.get_pending_batches()
    active_batches = [
        b
        for b in batches
        if b.get("google_batch_id") and b["status"] in ["SUBMITTED", "PROCESSING"]
    ]

    if not active_batches:
        return 0

    logger.info(f"📊 Polling {len(active_batches)} active batches")

    # 2. Маппинг статусов Google → DB
    STATUS_MAP = {
        "JOB_STATE_PENDING": "SUBMITTED",  # Ещё в очереди Google
        "JOB_STATE_RUNNING": "PROCESSING",  # Google обрабатывает
        "JOB_STATE_SUCCEEDED": "COMPLETED",  # Готов к скачиванию (Step 3)
        "JOB_STATE_FAILED": "FAILED",  # Критическая ошибка
        "JOB_STATE_CANCELLED": "FAILED",  # Отменён пользователем
        "STATE_UNSPECIFIED": "SUBMITTED",  # Fallback для неизвестных статусов
    }

    processed_count = 0

    for batch in active_batches:
        batch_id = batch["id"]
        google_batch_id = batch["google_batch_id"]
        current_status = batch["status"]

        try:
            # 3. Определить новый статус
            new_status = None

            # КРИТИЧЕСКАЯ ПРОВЕРКА: Mock ID (из Step 1)
            if google_batch_id.startswith("batches/mock_"):
                # Mock режим: эмулируем быстрое завершение для тестов
                if not ENABLE_BATCH_API:
                    # Переход: SUBMITTED → PROCESSING → COMPLETED
                    if current_status == "SUBMITTED":
                        new_status = "PROCESSING"
                    elif current_status == "PROCESSING":
                        new_status = "COMPLETED"

                    logger.debug(
                        f"🧪 [MOCK] Batch {batch_id[:8]} emulated: {current_status} → {new_status}"
                    )
                else:
                    # Если ENABLE_BATCH_API=true, но ID mock → пропустить
                    logger.warning(
                        f"⚠️ Batch {batch_id[:8]} has mock ID but ENABLE_BATCH_API=true. "
                        f"Skipping (inconsistent state)"
                    )
                    continue

            # Real API режим
            elif ENABLE_BATCH_API and client:
                # Запрос к Google Batch API
                google_batch = client.batches.get(name=google_batch_id)

                # Получить статус (например: "JOB_STATE_RUNNING")
                google_state = google_batch.state

                # Преобразовать в наш статус
                new_status = STATUS_MAP.get(google_state, "SUBMITTED")

                logger.debug(
                    f"📡 Batch {batch_id[:8]}: Google state={google_state} → DB status={new_status}"
                )

            else:
                # ENABLE_BATCH_API=false и не mock ID → пропустить
                logger.warning(
                    f"⚠️ Batch {batch_id[:8]} has real ID but ENABLE_BATCH_API=false. "
                    f"Cannot poll without API access"
                )
                continue

            # 4. Обновить БД только если статус изменился (оптимизация)
            if new_status and new_status != current_status:
                db.update_batch_status(batch_id, new_status)
                logger.info(
                    f"✅ Batch {batch_id[:8]} status updated: {current_status} → {new_status}"
                )
            elif new_status == current_status:
                logger.debug(
                    f"⏸️ Batch {batch_id[:8]} status unchanged: {current_status}"
                )

            processed_count += 1

        except Exception as e:
            # Обработка ошибок: 404, rate limits, network issues
            logger.error(f"❌ Failed to poll batch {batch_id[:8]}: {e}")

            # НЕ обновляем статус на FAILED при ошибке polling
            # Это может быть временная проблема (сеть, rate limit)
            # Повторим проверку в следующем цикле

            # Однако если это 404 NOT_FOUND, можно пометить как FAILED
            error_str = str(e).lower()
            if "404" in error_str or "not found" in error_str:
                logger.warning(
                    f"⚠️ Batch {batch_id[:8]} not found in Google API. "
                    f"Possible causes: expired, deleted, or invalid ID"
                )
                # Опционально: можно пометить как FAILED после N попыток
                # Но для MVP оставляем в текущем статусе для retry

    logger.info(
        f"📊 Polling complete: {processed_count}/{len(active_batches)} batches processed"
    )
    return processed_count


def retrieve_completed_batches(db) -> int:
    """
    Фаза 3: Скачивание готовых результатов из Google Batch API.

    Алгоритм:
    1. Найти пакеты со статусом PROCESSING, у которых JOB_STATE_SUCCEEDED
    2. Для каждого batch:
       - results = batch_status.results
       - Для каждого result:
         * Найти задачу по custom_id (это task_id)
         * Извлечь bytes изображения
         * Сохранить в target_path
         * db.update_task_completed()
    3. Проверить прогресс пакета:
       - Если все задачи завершены → db.update_batch_completed()

    Args:
        db: DatabaseManager instance

    Returns:
        Количество скачанных результатов

    Note:
        ЗАГЛУШКА для Фазы 2.
        Реальная реализация будет в Фазе 3 (Batch API Integration).
    """
    logger.debug("[MOCK] No completed batches to retrieve yet")
    # TODO Фаза 3: реальное скачивание результатов
    return 0
