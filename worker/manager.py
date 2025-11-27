"""
WorkerManager — фоновый обработчик очереди задач.

Запускается в отдельном daemon-потоке параллельно с MCP-сервером.
Обрабатывает задачи из БД в двух режимах:
- batch: через Google Batch API (50% скидка)
- local_queue: последовательная обработка (TTS fallback)
"""

import logging
import threading
import time
from typing import Optional

from .processors import (
    submit_pending_batches,
    poll_active_batches,
    retrieve_completed_batches,
    process_local_queue_tasks,
)

logger = logging.getLogger("gemini-media-mcp.worker")


class WorkerManager:
    """
    Менеджер фонового воркера для обработки очереди задач.

    Attributes:
        _thread: Daemon-поток для фонового выполнения
        _stop_event: Event для graceful shutdown
        _db: Ссылка на DatabaseManager
        _tick_interval: Интервал между циклами обработки (секунды)
        _health_check_on_start: Флаг для Health Check при первом запуске
    """

    def __init__(self, db, tick_interval: int = 30):
        """
        Инициализация воркера.

        Args:
            db: Инициализированный DatabaseManager
            tick_interval: Интервал между циклами в секундах (по умолчанию 30)
        """
        self._db = db
        self._tick_interval = tick_interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._health_check_on_start = True

        logger.info(f"WorkerManager initialized (tick_interval={tick_interval}s)")

    def start(self) -> None:
        """
        Запустить фоновый воркер в daemon-потоке.

        Daemon-поток автоматически завершается при выходе из главного процесса,
        что предотвращает появление процессов-зомби.
        """
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Worker already running, ignoring start() call")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker_loop,
            name="WorkerThread",
            daemon=True,  # Критично: поток завершится при выходе из main
        )
        self._thread.start()
        logger.info("Worker started in background thread")

    def stop(self, timeout: int = 10) -> None:
        """
        Graceful shutdown воркера.

        Устанавливает stop event и ждёт завершения текущего цикла.

        Args:
            timeout: Максимальное время ожидания в секундах
        """
        if self._thread is None or not self._thread.is_alive():
            logger.warning("Worker not running, ignoring stop() call")
            return

        logger.info("Stopping worker...")
        self._stop_event.set()  # Сигнал для _worker_loop()

        self._thread.join(timeout=timeout)  # Ждём завершения потока

        if self._thread.is_alive():
            logger.error(f"Worker did not stop within {timeout}s timeout")
        else:
            logger.info("Worker stopped successfully")

    def _worker_loop(self) -> None:
        """
        Главный бесконечный цикл воркера.

        Фазы обработки:
        1. Health Check (только при первом запуске)
        2. Batch Submission (отправка pending задач в Google Batch API)
        3. Batch Polling (проверка статусов активных пакетов)
        4. Batch Retrieval (скачивание готовых результатов)
        5. Local Queue Processing (TTS задачи с rate limiting)
        6. Sleep до следующего тика
        """
        logger.info("Worker loop started")

        # Health Check при старте
        if self._health_check_on_start:
            self._health_check()
            self._health_check_on_start = False

        while not self._stop_event.is_set():
            try:
                logger.debug("Worker cycle starting...")

                # === BATCH MODE ===
                # Фаза 1: Submission
                self._submit_pending_batches()

                # Фаза 2: Polling
                self._poll_active_batches()

                # Фаза 3: Retrieval
                self._retrieve_completed_batches()

                # === LOCAL QUEUE MODE ===
                # Фаза 4: TTS обработка
                self._process_local_queue()

                # Фаза 5: Sleep
                logger.debug(f"Worker cycle complete, sleeping {self._tick_interval}s")
                self._stop_event.wait(timeout=self._tick_interval)

            except Exception as e:
                logger.exception(f"Worker loop error: {e}")
                # Не падаем, продолжаем работу после паузы
                time.sleep(5)

        logger.info("Worker loop stopped")

    def _health_check(self) -> None:
        """
        Health Check при старте воркера.

        Восстанавливает зависшие задачи (статус PROCESSING, но давно не обновлялись).
        """
        logger.info("Running Health Check...")

        try:
            recovered = self._db.recover_stale_tasks(timeout_minutes=30)

            if recovered > 0:
                logger.warning(f"Health Check: recovered {recovered} stale tasks")
            else:
                logger.info("Health Check: no stale tasks found")

        except Exception as e:
            logger.exception(f"Health Check failed: {e}")

    def _submit_pending_batches(self) -> None:
        """
        Фаза 1: Отправка PENDING задач в Google Batch API.

        ЗАГЛУШКА для Фазы 2.
        Реальная реализация будет в Фазе 3 (Batch API Integration).
        """
        submit_pending_batches(self._db)

    def _poll_active_batches(self) -> None:
        """
        Фаза 2: Проверка статусов активных пакетов.

        ЗАГЛУШКА для Фазы 2.
        Реальная реализация будет в Фазе 3 (Batch API Integration).
        """
        poll_active_batches(self._db)

    def _retrieve_completed_batches(self) -> None:
        """
        Фаза 3: Скачивание готовых результатов из Batch API.

        ЗАГЛУШКА для Фазы 2.
        Реальная реализация будет в Фазе 3 (Batch API Integration).
        """
        retrieve_completed_batches(self._db)

    def _process_local_queue(self) -> None:
        """
        Фаза 4: Обработка TTS задач (local_queue режим).

        ЗАГЛУШКА для Фазы 2.
        Реальная реализация будет в Этапе 2.2.
        """
        processed = process_local_queue_tasks(self._db)

        if processed:
            # Rate limiting для TTS (3-10 RPM)
            logger.debug("Sleeping 10s for TTS rate limiting")
            time.sleep(10)
