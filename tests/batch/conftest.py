"""
Общие фикстуры для тестов Batch API.

Содержит:
- temp_db: временная БД для изолированных тестов
- mock_mode: отключение реального API
- JSONL fixtures: примеры ответов Google Batch API
"""

import os
import pytest
from uuid import uuid4
from pathlib import Path
from database import DatabaseManager

# Feature flag для реального API
ENABLE_BATCH_API = os.getenv("ENABLE_BATCH_API", "false").lower() == "true"


@pytest.fixture
def temp_db(tmp_path):
    """Временная БД для изолированных тестов."""
    db_path = tmp_path / "test_batch.db"
    db = DatabaseManager()
    db.initialize(str(db_path))
    yield db
    db.close()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def mock_mode(monkeypatch):
    """Фикстура для mock режима (отключает реальный API)."""
    import worker.processors.batch_processor as bp

    monkeypatch.setattr(bp, "ENABLE_BATCH_API", False)
    monkeypatch.setattr(bp, "client", None)
    yield


# ==============================================================================
# JSONL Fixtures: примеры ответов Google Batch API
# ==============================================================================


@pytest.fixture
def perfect_jsonl():
    """
    Идеальный JSONL от Google (2 успешных задачи).

    Структура: каждая строка = 1 результат
    Base64: 1x1 пиксель PNG (красный цвет) для тестов
    """
    return """{"response": {"candidates": [{"content": {"parts": [{"inline_data": {"mime_type": "image/png", "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}}], "role": "model"}, "finish_reason": "STOP"}]}}
{"response": {"candidates": [{"content": {"parts": [{"inline_data": {"mime_type": "image/png", "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}}], "role": "model"}, "finish_reason": "STOP"}]}}"""


@pytest.fixture
def broken_jsonl():
    """
    Сломанный JSONL (меньше результатов чем задач).

    Симулирует Safety Filter: отправили 3 задачи, вернулось 2.
    КРИТИЧНО: вызовет рассинхрон индексов!
    """
    return """{"response": {"candidates": [{"content": {"parts": [{"text": "Cat"}], "role": "model"}}]}}
{"response": {"candidates": [{"content": {"parts": [{"text": "Dog"}], "role": "model"}}]}}"""


@pytest.fixture
def error_jsonl():
    """
    JSONL с ошибками от Google (одна задача провалилась).

    Строка 1: успех с изображением
    Строка 2: error (Safety Filter или Invalid Prompt)
    """
    return """{"response": {"candidates": [{"content": {"parts": [{"inline_data": {"mime_type": "image/png", "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}}], "role": "model"}}]}}
{"error": {"code": 400, "message": "Image generation failed: safety filters triggered", "status": "INVALID_ARGUMENT"}}"""


@pytest.fixture
def invalid_json():
    """
    Невалидный JSON (поврежденный файл).

    Симулирует сетевой сбой или битый файл на сервере.
    """
    return """{"response": {"candidates": [{"content": {"parts
THIS_IS_NOT_VALID_JSON"""


@pytest.fixture
def invalid_base64_jsonl():
    """
    JSONL с битым base64 (невалидные символы).
    """
    return """{"response": {"candidates": [{"content": {"parts": [{"inline_data": {"mime_type": "image/png", "data": "NOT_VALID_BASE64_!@#$%"}}], "role": "model"}}]}}"""


# ==============================================================================
# Helper fixtures
# ==============================================================================


@pytest.fixture
def create_completed_batch(temp_db):
    """
    Factory fixture для создания COMPLETED батча с задачами.

    Usage:
        batch_id, task_ids = create_completed_batch(num_tasks=3)
    """

    def _create(num_tasks: int = 2, use_mock_id: bool = True):
        batch_id = str(uuid4())
        task_ids = sorted([str(uuid4()) for _ in range(num_tasks)])

        tasks_data = [
            {
                "task_id": tid,
                "input_payload": {"prompt": f"Task {i}"},
                "target_path": f"/tmp/generated/{tid}.png",  # NOT NULL в БД
            }
            for i, tid in enumerate(task_ids)
        ]

        temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)

        prefix = "mock_" if use_mock_id else "real_"
        google_id = f"batches/{prefix}{batch_id[:8]}"
        temp_db.update_batch_status(batch_id, "COMPLETED", google_id)

        for tid in task_ids:
            temp_db.update_task_status(tid, "SUBMITTED")

        return batch_id, task_ids

    return _create
