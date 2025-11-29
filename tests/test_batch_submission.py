"""Тесты для Batch Submission — отправка задач в Google Batch API.

Классы:
    TestBatchSubmission — тесты submit_pending_batches().
    TestBatchSubmissionErrors — тесты обработки ошибок.
"""

import os
import pytest
import logging
from uuid import uuid4

from database import DatabaseManager
from worker.processors.batch_processor import submit_pending_batches, ENABLE_BATCH_API

# Включить логирование для отладки
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_db(tmp_path):
    """Создаёт временную БД для тестов."""
    db_path = tmp_path / "test_batch_submission.db"
    db = DatabaseManager()
    db.initialize(str(db_path))
    yield db
    db.close()


@pytest.fixture
def mock_mode(monkeypatch):
    """Включает MOCK режим для тестов."""
    # Патчим переменную в модуле batch_processor
    import worker.processors.batch_processor as bp

    monkeypatch.setattr(bp, "ENABLE_BATCH_API", False)
    monkeypatch.setattr(bp, "client", None)
    yield


class TestBatchSubmission:
    """Тесты submit_pending_batches()."""

    def test_mock_mode_creates_fake_batch_id(self, temp_db, mock_mode):
        """Проверяет создание fake google_batch_id в mock режиме."""
        # Создать batch-операцию
        batch_id = str(uuid4())
        temp_db.create_batch(
            batch_id=batch_id, operation_type="IMG_GEN_BATCH", total_tasks=2
        )

        # Создать 2 задачи для пакета
        task_id_1 = str(uuid4())
        task_id_2 = str(uuid4())

        temp_db.create_task(
            task_id=task_id_1,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "A cat in space"},
            target_path=f"output/images/{task_id_1}.png",
        )

        temp_db.create_task(
            task_id=task_id_2,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "A dog in forest"},
            target_path=f"output/images/{task_id_2}.png",
        )

        # Выполнить submit_pending_batches()
        submitted_count = submit_pending_batches(temp_db)

        # Проверки
        assert submitted_count == 1, "Должен быть отправлен 1 пакет"

        # Проверить статус пакета
        batch = temp_db.get_batch(batch_id)
        assert batch["status"] == "SUBMITTED", "Пакет должен быть SUBMITTED"
        assert batch["google_batch_id"].startswith("batches/mock_"), (
            f"google_batch_id должен начинаться с 'batches/mock_', got: {batch['google_batch_id']}"
        )

        # Проверить статусы задач
        task_1 = temp_db.get_task(task_id_1)
        task_2 = temp_db.get_task(task_id_2)

        assert task_1["status"] == "SUBMITTED", "Задача 1 должна быть SUBMITTED"
        assert task_2["status"] == "SUBMITTED", "Задача 2 должна быть SUBMITTED"

    def test_filters_only_batch_mode(self, temp_db, mock_mode):
        """Проверяет, что только execution_mode='batch' задачи отправляются."""
        # Создать sync-операцию (не batch)
        sync_batch_id = str(uuid4())
        temp_db.create_batch(
            batch_id=sync_batch_id,
            operation_type="IMG_GEN",  # sync mode, не batch
            total_tasks=1,
        )

        sync_task_id = str(uuid4())
        temp_db.create_task(
            task_id=sync_task_id,
            batch_id=sync_batch_id,
            operation_type="IMG_GEN",
            input_payload={"prompt": "Test sync"},
            target_path=f"output/images/{sync_task_id}.png",
        )

        # Создать batch-операцию
        batch_batch_id = str(uuid4())
        temp_db.create_batch(
            batch_id=batch_batch_id,
            operation_type="IMG_GEN_BATCH",  # batch mode
            total_tasks=1,
        )

        batch_task_id = str(uuid4())
        temp_db.create_task(
            task_id=batch_task_id,
            batch_id=batch_batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test batch"},
            target_path=f"output/images/{batch_task_id}.png",
        )

        # Выполнить submit_pending_batches()
        submitted_count = submit_pending_batches(temp_db)

        # Проверки
        assert submitted_count == 1, "Только batch-режим должен быть отправлен"

        # Sync batch не должен быть отправлен
        sync_batch = temp_db.get_batch(sync_batch_id)
        assert sync_batch["status"] == "PENDING", "Sync batch должен остаться PENDING"
        assert sync_batch["google_batch_id"] is None, (
            "Sync batch не должен иметь google_batch_id"
        )

        # Batch batch должен быть отправлен
        batch_batch = temp_db.get_batch(batch_batch_id)
        assert batch_batch["status"] == "SUBMITTED", "Batch batch должен быть SUBMITTED"
        assert batch_batch["google_batch_id"] is not None, (
            "Batch batch должен иметь google_batch_id"
        )

    def test_empty_batch_skipped(self, temp_db, mock_mode):
        """Проверяет, что пакет без задач пропускается."""
        # Создать пакет без задач
        empty_batch_id = str(uuid4())
        temp_db.create_batch(
            batch_id=empty_batch_id, operation_type="IMG_GEN_BATCH", total_tasks=0
        )

        # Выполнить submit_pending_batches()
        submitted_count = submit_pending_batches(temp_db)

        # Проверки
        assert submitted_count == 0, "Пустой пакет не должен быть отправлен"

        # Пакет должен остаться PENDING
        batch = temp_db.get_batch(empty_batch_id)
        assert batch["status"] == "PENDING", "Пустой пакет должен остаться PENDING"

    @pytest.mark.skipif(
        not ENABLE_BATCH_API or os.getenv("CI") == "true",
        reason="Пропускается в CI или если ENABLE_BATCH_API=false",
    )
    def test_real_api_submission(self, temp_db):
        """
        Реальный API вызов (опциональный тест).

        ⚠️ Требует:
        - Реальный GEMINI_API_KEY в config.py
        - ENABLE_BATCH_API=true
        - Не запускается в CI (стоит skip marker)

        Этот тест создаёт реальный batch в Google Batch API!
        """
        # Создать batch
        batch_id = str(uuid4())
        temp_db.create_batch(
            batch_id=batch_id, operation_type="IMG_GEN_BATCH", total_tasks=1
        )

        # Создать задачу
        task_id = str(uuid4())
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "A simple test image of a red ball"},
            target_path=f"output/images/{task_id}.png",
        )

        # Выполнить submit_pending_batches()
        submitted_count = submit_pending_batches(temp_db)

        # Проверки
        assert submitted_count == 1, "Должен быть отправлен 1 пакет"

        # Проверить google_batch_id
        batch = temp_db.get_batch(batch_id)
        assert batch["status"] == "SUBMITTED", "Пакет должен быть SUBMITTED"
        assert batch["google_batch_id"].startswith("batches/"), (
            f"google_batch_id должен начинаться с 'batches/', got: {batch['google_batch_id']}"
        )

        # Проверить, что это НЕ mock (реальный ID длиннее 20 символов)
        assert len(batch["google_batch_id"]) > 20, (
            "Реальный google_batch_id должен быть длинным"
        )


class TestBatchSubmissionErrors:
    """Тесты обработки ошибок отправки."""

    def test_api_error_marks_batch_failed(self, temp_db, monkeypatch):
        """Проверяет, что при ошибке API пакет помечается как FAILED."""

        # Патчим client.batches.create, чтобы он выбрасывал исключение
        def mock_create_error(*args, **kwargs):
            raise Exception("Mock API error: rate limit exceeded")

        # Включить реальный режим для этого теста
        monkeypatch.setenv("ENABLE_BATCH_API", "true")

        # Патчим модуль batch_processor
        import worker.processors.batch_processor as bp

        monkeypatch.setattr(bp, "ENABLE_BATCH_API", True)

        # Создаём mock client
        class MockClient:
            class batches:
                @staticmethod
                def create(*args, **kwargs):
                    raise Exception("Mock API error: rate limit exceeded")

        monkeypatch.setattr(bp, "client", MockClient())

        # Создать batch
        batch_id = str(uuid4())
        temp_db.create_batch(
            batch_id=batch_id, operation_type="IMG_GEN_BATCH", total_tasks=1
        )

        # Создать задачу
        task_id = str(uuid4())
        temp_db.create_task(
            task_id=task_id,
            batch_id=batch_id,
            operation_type="IMG_GEN_BATCH",
            input_payload={"prompt": "Test"},
            target_path=f"output/images/{task_id}.png",
        )

        # Выполнить submit_pending_batches()
        submitted_count = submit_pending_batches(temp_db)

        # Проверки
        assert submitted_count == 0, "При ошибке пакет не считается отправленным"

        # Пакет должен быть FAILED
        batch = temp_db.get_batch(batch_id)
        assert batch["status"] == "FAILED", "Пакет должен быть помечен FAILED"
        # Опционально: проверить error_message
        # assert "rate limit" in batch.get("error_message", "").lower()
