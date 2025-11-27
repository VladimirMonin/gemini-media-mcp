"""
Тесты для WorkerManager — фоновый обработчик очереди задач.

Проверяет:
- Старт/стоп воркера
- Health Check восстановление зависших задач
- Обработка local_queue задач
- Graceful shutdown
"""

import pytest
import time
import logging
from uuid import uuid4
from datetime import datetime, timedelta

from database import DatabaseManager
from worker import WorkerManager

# Включить логирование для отладки
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_db(tmp_path):
    """Временная БД для тестов."""
    db_path = tmp_path / "test_worker.db"
    db = DatabaseManager()
    db.initialize(str(db_path))
    yield db
    db.close()


class TestWorkerLifecycle:
    """Тесты жизненного цикла воркера."""

    def test_worker_start_stop(self, temp_db):
        """Воркер запускается и корректно останавливается."""
        worker = WorkerManager(temp_db, tick_interval=1)

        # Запуск
        worker.start()
        assert worker._thread is not None
        assert worker._thread.is_alive()

        # Даём воркеру время на 2-3 цикла
        time.sleep(3)

        # Остановка
        worker.stop(timeout=5)
        assert not worker._thread.is_alive()

    def test_worker_already_running(self, temp_db):
        """Повторный start() игнорируется, если воркер уже запущен."""
        worker = WorkerManager(temp_db, tick_interval=1)

        worker.start()
        thread1 = worker._thread

        # Попытка запустить ещё раз
        worker.start()
        thread2 = worker._thread

        # Должен остаться тот же поток
        assert thread1 is thread2

        worker.stop(timeout=5)

    def test_worker_stop_not_running(self, temp_db):
        """stop() без запущенного воркера не падает."""
        worker = WorkerManager(temp_db, tick_interval=1)

        # Остановка без старта
        worker.stop(timeout=5)
        # Не должно быть исключений


class TestHealthCheck:
    """Тесты Health Check восстановления зависших задач."""

    def test_health_check_recovers_stale_tasks(self, temp_db):
        """Health Check находит и восстанавливает зависшие задачи."""
        # Создать задачу в статусе PROCESSING со старым updated_at
        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch(batch_id, "TTS_GEN", 1)
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="TTS_GEN",
            input_payload={"script": "test"},
            target_path="test.wav",
        )

        # Перевести в PROCESSING
        temp_db.update_task_status(task_id, "PROCESSING")

        # Вручную установить старый updated_at (имитация зависания)
        # updated_at должен быть > 30 минут назад для срабатывания recover_stale_tasks
        old_time = (datetime.now() - timedelta(minutes=35)).isoformat()
        temp_db._conn.execute(
            "UPDATE tasks SET updated_at = ? WHERE id = ?", (old_time, task_id)
        )
        temp_db._conn.commit()

        # Запустить воркер (должен сработать Health Check)
        worker = WorkerManager(temp_db, tick_interval=1)
        worker.start()

        # Даём время на Health Check и 1 цикл
        time.sleep(3)

        worker.stop(timeout=5)

        # Проверить, что задача восстановлена в PENDING
        task = temp_db.get_task(task_id)
        assert task["status"] == "PENDING", f"Expected PENDING, got {task['status']}"


class TestLocalQueueProcessing:
    """Тесты обработки local_queue задач."""

    def test_local_queue_processes_one_task(self, temp_db):
        """Воркер обрабатывает 1 TTS задачу за цикл."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        # Добавить временный operation_type с local_queue режимом для теста
        temp_db._conn.execute("""
            INSERT OR IGNORE INTO operation_types (operation_type, display_name, execution_mode, description)
            VALUES ('TTS_QUEUE', 'TTS Local Queue', 'local_queue', 'Test operation for local queue')
        """)
        temp_db._conn.commit()

        temp_db.create_batch_with_tasks(
            batch_id=batch_id,
            operation_type="TTS_QUEUE",  # Используем тестовый operation_type
            tasks=[
                {
                    "task_id": task_id,
                    "input_payload": {"script": "test audio"},
                    "target_path": "output/test.wav",
                    "search_keywords": "test",
                }
            ],
        )

        # Запустить воркер
        worker = WorkerManager(temp_db, tick_interval=2)
        worker.start()

        # Даём время на обработку (1 цикл + mock sleep 2s)
        time.sleep(5)

        worker.stop(timeout=5)

        # Проверить, что задача завершена
        task = temp_db.get_task(task_id)
        assert task["status"] == "COMPLETED"
        assert task["local_path"] == "output/test.wav"

    def test_local_queue_ignores_batch_tasks(self, temp_db):
        """Воркер не обрабатывает batch задачи в local_queue процессоре."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        # Создать batch-задачу (не local_queue)
        temp_db.create_batch_with_tasks(
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            tasks=[
                {
                    "task_id": task_id,
                    "input_payload": {"prompt": "test image"},
                    "target_path": "output/test.png",
                    "search_keywords": "test",
                }
            ],
        )

        # Патчим batch_processor для mock режима
        import worker.processors.batch_processor as bp

        original_enable = bp.ENABLE_BATCH_API
        original_client = bp.client
        bp.ENABLE_BATCH_API = False
        bp.client = None

        # Запустить воркер
        worker = WorkerManager(temp_db, tick_interval=2)
        worker.start()

        time.sleep(5)

        worker.stop(timeout=5)

        # Восстановить оригинальные значения
        bp.ENABLE_BATCH_API = original_enable
        bp.client = original_client

        # В mock режиме batch задачи проходят через polling:
        # PENDING → SUBMITTED (submission) → PROCESSING/COMPLETED (polling)
        task = temp_db.get_task(task_id)
        batch = temp_db.get_batch(batch_id)

        # Проверить, что это был mock (fake batch_id)
        assert batch["google_batch_id"].startswith("batches/mock_")
        assert (
            task["status"] == "SUBMITTED"
        )  # Tasks не обновляются polling (только Step 3)

        # Статус batch может быть SUBMITTED, PROCESSING или COMPLETED (зависит от timing)
        assert batch["status"] in ["SUBMITTED", "PROCESSING", "COMPLETED"], (
            f"Expected batch in submitted/processing/completed, got {batch['status']}"
        )


class TestGracefulShutdown:
    """Тесты корректного завершения воркера."""

    def test_worker_graceful_shutdown(self, temp_db):
        """Воркер завершается корректно, не оставляя зомби-потоков."""
        worker = WorkerManager(temp_db, tick_interval=10)

        worker.start()
        assert worker._thread.is_alive()

        # Остановка в середине цикла
        time.sleep(0.5)
        worker.stop(timeout=5)

        # Поток должен завершиться
        assert not worker._thread.is_alive()

    def test_worker_stop_event_interrupts_sleep(self, temp_db):
        """stop_event.wait() прерывается немедленно, не ждёт tick_interval."""
        worker = WorkerManager(temp_db, tick_interval=30)  # Длинный интервал

        worker.start()
        time.sleep(1)  # Воркер в режиме wait(30)

        start_time = time.time()
        worker.stop(timeout=5)
        elapsed = time.time() - start_time

        # Должен завершиться быстро (< 5s), а не ждать 30s
        assert elapsed < 5
        assert not worker._thread.is_alive()
