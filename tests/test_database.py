"""Тесты для пакета database.

Классы:
    TestInitialization — тесты инициализации БД.
    TestOperationTypes — тесты операций с типами операций.
    TestBatches — тесты CRUD операций с пакетами.
    TestTasks — тесты CRUD операций с задачами.
    TestTransactions — тесты транзакционных операций.
    TestUtilities — тесты вспомогательных функций.
"""

import pytest
import tempfile
import os
from pathlib import Path
from uuid import uuid4

# Add project root to path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import DatabaseManager


@pytest.fixture
def temp_db():
    """Создаёт временную БД для тестирования."""
    # Create temp file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Initialize database
    db = DatabaseManager()
    db.initialize(db_path=db_path)

    yield db

    # Cleanup
    db.close()
    try:
        os.unlink(db_path)
    except Exception:
        pass


class TestInitialization:
    """Тесты инициализации базы данных."""

    def test_initialize_creates_tables(self, temp_db):
        """Проверяет, что инициализация создаёт все таблицы."""
        conn = temp_db.get_connection()
        cursor = conn.cursor()

        # Check operation_types table exists
        result = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='operation_types'"
        ).fetchone()
        assert result is not None

        # Check batches table exists
        result = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='batches'"
        ).fetchone()
        assert result is not None

        # Check tasks table exists
        result = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        ).fetchone()
        assert result is not None

    def test_seed_data_loaded(self, temp_db):
        """Проверяет, что seed данные загружены в operation_types."""
        op_types = temp_db.get_all_operation_types()
        assert len(op_types) == 11  # 6 sync + 4 batch + 1 local_queue (TTS_GEN_QUEUE)

        # Check specific operation exists
        img_gen = temp_db.get_operation_type("IMG_GEN")
        assert img_gen is not None
        assert img_gen["display_name"] == "Image Generation"
        assert img_gen["execution_mode"] == "sync"


class TestOperationTypes:
    """Тесты операций с типами операций."""

    def test_get_operation_type_exists(self, temp_db):
        """Проверяет получение существующего типа операции."""
        result = temp_db.get_operation_type("IMG_GEN_BATCH")
        assert result is not None
        assert result["operation_type"] == "IMG_GEN_BATCH"
        assert result["execution_mode"] == "batch"

    def test_get_operation_type_not_exists(self, temp_db):
        """Проверяет получение несуществующего типа операции."""
        result = temp_db.get_operation_type("INVALID_OP")
        assert result is None

    def test_get_all_operation_types(self, temp_db):
        """Проверяет получение всех типов операций."""
        result = temp_db.get_all_operation_types()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("operation_type" in op for op in result)

    def test_get_execution_mode(self, temp_db):
        """Проверяет получение режима выполнения."""
        mode = temp_db.get_execution_mode("IMG_GEN_BATCH")
        assert mode == "batch"

        mode = temp_db.get_execution_mode("TTS_GEN")
        assert mode == "sync"

    def test_get_execution_mode_invalid(self, temp_db):
        """Проверяет ошибку при получении режима для недействительной операции."""
        with pytest.raises(ValueError, match="Unknown operation_type"):
            temp_db.get_execution_mode("INVALID_OP")


class TestBatches:
    """Тесты CRUD операций с пакетами."""

    def test_create_batch(self, temp_db):
        """Проверяет создание пакета."""
        batch_id = str(uuid4())
        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 5)

        # Verify
        batch = temp_db.get_batch(batch_id)
        assert batch is not None
        assert batch["id"] == batch_id
        assert batch["operation_type"] == "IMG_GEN_BATCH"
        assert batch["total_tasks"] == 5
        assert batch["status"] == "PENDING"

    def test_create_batch_invalid_operation(self, temp_db):
        """Проверяет создание пакета с недействительным типом операции."""
        batch_id = str(uuid4())
        with pytest.raises(ValueError, match="Unknown operation_type"):
            temp_db.create_batch(batch_id, "INVALID_OP", 5)

    def test_get_batch_not_exists(self, temp_db):
        """Проверяет получение несуществующего пакета."""
        result = temp_db.get_batch("nonexistent-id")
        assert result is None

    def test_update_batch_status(self, temp_db):
        """Проверяет обновление статуса пакета."""
        batch_id = str(uuid4())
        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 5)

        # Update status
        temp_db.update_batch_status(batch_id, "SUBMITTED", "google-batch-123")

        # Verify
        batch = temp_db.get_batch(batch_id)
        assert batch["status"] == "SUBMITTED"
        assert batch["google_batch_id"] == "google-batch-123"

    def test_update_batch_completed(self, temp_db):
        """Проверяет завершение пакета."""
        batch_id = str(uuid4())
        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 5)

        # Complete batch
        temp_db.update_batch_completed(batch_id)

        # Verify
        batch = temp_db.get_batch(batch_id)
        assert batch["status"] == "COMPLETED"
        assert batch["completed_at"] is not None

    def test_get_pending_batches(self, temp_db):
        """Проверяет получение ожидающих пакетов."""
        # Create batches with different statuses
        batch1 = str(uuid4())
        batch2 = str(uuid4())
        batch3 = str(uuid4())

        temp_db.create_batch(batch1, "IMG_GEN_BATCH", 5)
        temp_db.create_batch(batch2, "IMG_GEN_BATCH", 3)
        temp_db.create_batch(batch3, "IMG_GEN_BATCH", 2)

        # Complete one batch
        temp_db.update_batch_completed(batch3)

        # Get pending
        pending = temp_db.get_pending_batches()
        assert len(pending) == 2
        assert all(
            b["status"] in ["PENDING", "SUBMITTED", "PROCESSING"] for b in pending
        )


class TestTasks:
    """Тесты CRUD операций с задачами."""

    def test_create_task(self, temp_db):
        """Проверяет создание задачи."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 1)
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test prompt", "model": "gemini-2.5-flash-image"},
            target_path="/tmp/test.png",
            search_keywords="test prompt",
        )

        # Verify
        task = temp_db.get_task(task_id)
        assert task is not None
        assert task["id"] == task_id
        assert task["batch_id"] == batch_id
        assert task["status"] == "PENDING"
        assert task["input_payload"]["prompt"] == "Test prompt"
        assert task["target_path"] == "/tmp/test.png"

    def test_get_task_not_exists(self, temp_db):
        """Проверяет получение несуществующей задачи."""
        result = temp_db.get_task("nonexistent-id")
        assert result is None

    def test_update_task_status(self, temp_db):
        """Проверяет обновление статуса задачи."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 1)
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test"},
            target_path="/tmp/test.png",
        )

        # Update status
        temp_db.update_task_status(task_id, "PROCESSING")

        # Verify
        task = temp_db.get_task(task_id)
        assert task["status"] == "PROCESSING"

    def test_update_task_completed(self, temp_db):
        """Проверяет завершение задачи."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 1)
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test"},
            target_path="/tmp/test.png",
        )

        # Complete task
        temp_db.update_task_completed(task_id, "/tmp/test_result.png")

        # Verify
        task = temp_db.get_task(task_id)
        assert task["status"] == "COMPLETED"
        assert task["local_path"] == "/tmp/test_result.png"
        assert task["completed_at"] is not None

    def test_update_task_failed(self, temp_db):
        """Проверяет провал задачи."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 1)
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test"},
            target_path="/tmp/test.png",
        )

        # Fail task
        temp_db.update_task_failed(task_id, "Test error message")

        # Verify
        task = temp_db.get_task(task_id)
        assert task["status"] == "FAILED"
        assert task["error_details"] == "Test error message"
        assert task["completed_at"] is not None

    def test_get_tasks_by_batch(self, temp_db):
        """Проверяет получение всех задач пакета."""
        batch_id = str(uuid4())
        task1 = str(uuid4())
        task2 = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 2)
        temp_db.create_task(
            task_id=task1,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test 1"},
            target_path="/tmp/test1.png",
        )
        temp_db.create_task(
            task_id=task2,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test 2"},
            target_path="/tmp/test2.png",
        )

        # Get tasks
        tasks = temp_db.get_tasks_by_batch(batch_id)
        assert len(tasks) == 2
        assert all(t["batch_id"] == batch_id for t in tasks)

    def test_get_pending_tasks(self, temp_db):
        """Проверяет получение ожидающих задач."""
        batch_id = str(uuid4())
        task1 = str(uuid4())
        task2 = str(uuid4())
        task3 = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 3)

        # Create tasks
        for tid in [task1, task2, task3]:
            temp_db.create_task(
                task_id=tid,
                batch_id=batch_id,
                operation_type="IMG_GEN_BATCH",
                input_payload={"prompt": "Test"},
                target_path="/tmp/test.png",
            )

        # Complete one task
        temp_db.update_task_completed(task3, "/tmp/result.png")

        # Get pending
        pending = temp_db.get_pending_tasks()
        assert len(pending) == 2
        assert all(t["status"] == "PENDING" for t in pending)

    def test_search_tasks(self, temp_db):
        """Проверяет поиск задач."""
        batch_id = str(uuid4())
        task1 = str(uuid4())
        task2 = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 2)
        temp_db.create_task(
            task_id=task1,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "cyberpunk city at night"},
            target_path="/tmp/city.png",
            search_keywords="cyberpunk city night",
        )
        temp_db.create_task(
            task_id=task2,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "forest landscape"},
            target_path="/tmp/forest.png",
            search_keywords="forest landscape",
        )

        # Search
        results = temp_db.search_tasks(query="cyberpunk")
        assert len(results) == 1
        assert results[0]["id"] == task1


class TestTransactions:
    """Тесты транзакционных операций."""

    def test_create_batch_with_tasks(self, temp_db):
        """Проверяет атомарное создание пакета с задачами."""
        batch_id = str(uuid4())
        task1 = str(uuid4())
        task2 = str(uuid4())

        temp_db.create_batch_with_tasks(
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            tasks=[
                {
                    "task_id": task1,
                    "input_payload": {"prompt": "Test 1"},
                    "target_path": "/tmp/test1.png",
                    "search_keywords": "test 1",
                },
                {
                    "task_id": task2,
                    "input_payload": {"prompt": "Test 2"},
                    "target_path": "/tmp/test2.png",
                    "search_keywords": "test 2",
                },
            ],
        )

        # Verify batch
        batch = temp_db.get_batch(batch_id)
        assert batch is not None
        assert batch["total_tasks"] == 2

        # Verify tasks
        tasks = temp_db.get_tasks_by_batch(batch_id)
        assert len(tasks) == 2


class TestUtilities:
    """Тесты вспомогательных операций."""

    def test_get_stats(self, temp_db):
        """Проверяет получение статистики БД."""
        batch_id = str(uuid4())
        task1 = str(uuid4())
        task2 = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 2)
        temp_db.create_task(
            task_id=task1,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test"},
            target_path="/tmp/test.png",
        )
        temp_db.create_task(
            task_id=task2,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test"},
            target_path="/tmp/test.png",
        )

        # Complete one task
        temp_db.update_task_completed(task1, "/tmp/result.png")

        # Get stats
        stats = temp_db.get_stats()
        assert stats["total_tasks"] == 2
        assert stats["completed"] == 1
        assert stats["pending"] == 1
        assert stats["batches_active"] == 1

    def test_retry_task(self, temp_db):
        """Проверяет повторную попытку провалившейся задачи."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 1)
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test"},
            target_path="/tmp/test.png",
        )

        # Fail task
        temp_db.update_task_failed(task_id, "Test error")

        # Retry
        temp_db.retry_task(task_id)

        # Verify
        task = temp_db.get_task(task_id)
        assert task["status"] == "PENDING"
        assert task["error_details"] is None

    def test_retry_task_not_failed(self, temp_db):
        """Проверяет ошибку при повторе не провалившейся задачи."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", 1)
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test"},
            target_path="/tmp/test.png",
        )

        # Try to retry pending task
        with pytest.raises(ValueError, match="is not FAILED"):
            temp_db.retry_task(task_id)

    def test_cancel_batch(self, temp_db):
        """Проверяет отмену ожидающего пакета."""
        batch_id = str(uuid4())
        task1 = str(uuid4())
        task2 = str(uuid4())

        temp_db.create_batch_with_tasks(
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            tasks=[
                {
                    "task_id": task1,
                    "input_payload": {"prompt": "Test 1"},
                    "target_path": "/tmp/test1.png",
                },
                {
                    "task_id": task2,
                    "input_payload": {"prompt": "Test 2"},
                    "target_path": "/tmp/test2.png",
                },
            ],
        )

        # Cancel batch
        cancelled_count = temp_db.cancel_batch(batch_id)

        # Verify
        assert cancelled_count == 2
        batch = temp_db.get_batch(batch_id)
        assert batch["status"] == "FAILED"

        # Check tasks
        tasks = temp_db.get_tasks_by_batch(batch_id)
        assert all(t["status"] == "FAILED" for t in tasks)
        assert all("Cancelled by user" in t["error_details"] for t in tasks)

    def test_get_batch_progress(self, temp_db):
        """Проверяет получение прогресса пакета."""
        batch_id = str(uuid4())
        task1 = str(uuid4())
        task2 = str(uuid4())
        task3 = str(uuid4())

        temp_db.create_batch_with_tasks(
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            tasks=[
                {
                    "task_id": task1,
                    "input_payload": {"prompt": "Test"},
                    "target_path": "/tmp/1.png",
                },
                {
                    "task_id": task2,
                    "input_payload": {"prompt": "Test"},
                    "target_path": "/tmp/2.png",
                },
                {
                    "task_id": task3,
                    "input_payload": {"prompt": "Test"},
                    "target_path": "/tmp/3.png",
                },
            ],
        )

        # Complete one, fail one
        temp_db.update_task_completed(task1, "/tmp/result1.png")
        temp_db.update_task_failed(task2, "Error")

        # Get progress
        progress = temp_db.get_batch_progress(batch_id)
        assert progress["total"] == 3
        assert progress["completed"] == 1
        assert progress["failed"] == 1
        assert progress["pending"] == 1
