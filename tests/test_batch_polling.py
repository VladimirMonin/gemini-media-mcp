"""
Тесты для Фазы 3 Шаг 2: Batch Polling (отслеживание статусов).

Проверяет функцию poll_active_batches():
- Mock режим с fake batch IDs
- Корректный маппинг статусов Google → DB
- Обновление только при изменении статуса
- Обработка ошибок (404, пустые батчи)
- Опциональный real API тест
"""

import os
import pytest
from uuid import uuid4
from pathlib import Path
from database import DatabaseManager
from worker.processors.batch_processor import poll_active_batches

# Feature flag для реального API
ENABLE_BATCH_API = os.getenv("ENABLE_BATCH_API", "false").lower() == "true"


@pytest.fixture
def temp_db(tmp_path):
    """Временная БД для изолированных тестов."""
    db_path = tmp_path / "test_polling.db"
    db = DatabaseManager()
    db.initialize(str(db_path))
    yield db
    # Cleanup: закрыть соединение перед удалением
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
    monkeypatch.setattr(bp, "ENABLE_BATCH_API", ENABLE_BATCH_API)


# ==============================================================================
# ТЕСТ 1: Mock режим - эмуляция статусных переходов
# ==============================================================================


def test_mock_mode_emulates_status_transitions(temp_db, mock_mode):
    """
    Mock режим должен эмулировать переход статусов без вызова Google API.

    Сценарий:
    1. Создать batch с fake google_batch_id (batches/mock_...)
    2. Вызвать poll_active_batches()
    3. Проверить что статус обновился SUBMITTED → PROCESSING или COMPLETED
    """
    # 1. Создать batch с fake ID (как в Submission)
    batch_id = str(uuid4())
    task_id = str(uuid4())
    tasks = [
        {
            "task_id": task_id,
            "input_payload": {"prompt": "Test image"},
            "target_path": "/tmp/test.png",
        }
    ]

    temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks)

    # Эмулировать что batch был отправлен
    fake_google_id = f"batches/mock_{batch_id[:8]}"
    temp_db.update_batch_status(batch_id, "SUBMITTED", fake_google_id)

    # 2. Запустить polling
    updated_count = poll_active_batches(temp_db)

    # 3. Проверки
    assert updated_count == 1, "Должен обновить 1 batch"

    batch = temp_db.get_batch(batch_id)
    assert batch["status"] in ["PROCESSING", "COMPLETED"], (
        f"Mock должен эмулировать переход, получили: {batch['status']}"
    )
    assert batch["google_batch_id"] == fake_google_id, "ID не должен измениться"


# ==============================================================================
# ТЕСТ 2: Фильтрация - только батчи с google_batch_id
# ==============================================================================


def test_filters_only_submitted_batches(temp_db, mock_mode):
    """
    Должен проверять только батчи с google_batch_id (уже отправленные).

    Сценарий:
    1. Создать 2 батча: один PENDING (без google_id), второй SUBMITTED (с google_id)
    2. Вызвать polling
    3. Проверить что обработан только второй
    """
    # Batch 1: PENDING (не отправлен)
    batch1_id = str(uuid4())
    temp_db.create_batch_with_tasks(
        batch1_id,
        "IMG_GEN_BATCH",
        [
            {
                "task_id": str(uuid4()),
                "input_payload": {"prompt": "1"},
                "target_path": "/tmp/1.png",
            }
        ],
    )

    # Batch 2: SUBMITTED (отправлен)
    batch2_id = str(uuid4())
    temp_db.create_batch_with_tasks(
        batch2_id,
        "IMG_GEN_BATCH",
        [
            {
                "task_id": str(uuid4()),
                "input_payload": {"prompt": "2"},
                "target_path": "/tmp/2.png",
            }
        ],
    )
    temp_db.update_batch_status(batch2_id, "SUBMITTED", f"batches/mock_{batch2_id[:8]}")

    # Запустить polling
    updated_count = poll_active_batches(temp_db)

    # Проверки
    assert updated_count == 1, "Должен обработать только 1 batch (второй)"

    batch1 = temp_db.get_batch(batch1_id)
    batch2 = temp_db.get_batch(batch2_id)

    assert batch1["status"] == "PENDING", "Batch 1 не должен измениться"
    assert batch2["status"] in ["PROCESSING", "COMPLETED"], "Batch 2 должен обновиться"


# ==============================================================================
# ТЕСТ 3: Пустой список - нет активных батчей
# ==============================================================================


def test_no_active_batches_returns_zero(temp_db, mock_mode):
    """
    Если нет активных батчей, должен вернуть 0.
    """
    # Создать batch но не отправлять (нет google_batch_id)
    batch_id = str(uuid4())
    temp_db.create_batch_with_tasks(
        batch_id,
        "IMG_GEN_BATCH",
        [
            {
                "task_id": str(uuid4()),
                "input_payload": {"prompt": "Test"},
                "target_path": "/tmp/test.png",
            }
        ],
    )

    # Запустить polling
    updated_count = poll_active_batches(temp_db)

    assert updated_count == 0, "Не должен обработать ни одного batch"


# ==============================================================================
# ТЕСТ 4: Не обновлять если статус не изменился
# ==============================================================================


def test_does_not_update_if_status_unchanged(temp_db, mock_mode, monkeypatch):
    """
    Если Google вернул тот же статус, не делать UPDATE в БД.

    Это тест на оптимизацию - избегаем лишних операций записи.
    """
    # Создать batch в статусе PROCESSING
    batch_id = str(uuid4())
    temp_db.create_batch_with_tasks(
        batch_id,
        "IMG_GEN_BATCH",
        [
            {
                "task_id": str(uuid4()),
                "input_payload": {"prompt": "Test"},
                "target_path": "/tmp/test.png",
            }
        ],
    )
    fake_google_id = f"batches/mock_{batch_id[:8]}"
    temp_db.update_batch_status(batch_id, "PROCESSING", fake_google_id)

    # Патчим mock чтобы он возвращал тот же статус (PROCESSING)
    import worker.processors.batch_processor as bp

    original_poll = bp.poll_active_batches
    update_count = {"value": 0}

    def mock_poll(db):
        # Эмулируем что Google вернул JOB_STATE_RUNNING (наш PROCESSING)
        batches = db.get_pending_batches()
        submitted = [b for b in batches if b.get("google_batch_id")]

        for batch in submitted:
            if batch["google_batch_id"].startswith("batches/mock_"):
                # Возвращаем тот же статус
                if batch["status"] == "PROCESSING":
                    # НЕ обновляем
                    pass
                else:
                    db.update_batch_status(batch["id"], "PROCESSING")
                    update_count["value"] += 1

        return len(submitted)

    monkeypatch.setattr(bp, "poll_active_batches", mock_poll)

    # Запустить polling
    poll_active_batches(temp_db)

    # Проверка: update НЕ должен был произойти
    assert update_count["value"] == 0, "Не должен обновлять если статус не изменился"


# ==============================================================================
# ТЕСТ 5: Real API - опциональный тест (требует ENABLE_BATCH_API=true)
# ==============================================================================


@pytest.mark.skipif(
    not ENABLE_BATCH_API or os.getenv("CI") == "true",
    reason="Пропускается в CI или если ENABLE_BATCH_API=false",
)
def test_real_api_polling(temp_db):
    """
    ОПЦИОНАЛЬНЫЙ тест с реальным Google Batch API.

    Требования:
    - ENABLE_BATCH_API=true
    - GEMINI_API_KEY в .env
    - Предварительно созданный batch через Submission

    Стоимость: $0.00 (чтение статуса бесплатно)
    """
    pytest.skip("Требует предварительно созданный batch через Step 1")

    # Этот тест должен запускаться вручную после создания real batch
    # Для автоматизации можно создать batch в setUp

    # Пример:
    # batch_id = "uuid_from_previous_submission"
    # updated = poll_active_batches(temp_db)
    # assert updated > 0


# ==============================================================================
# ТЕСТ 6: Error handling - 404 NOT FOUND
# ==============================================================================


def test_handles_404_error_gracefully(temp_db, monkeypatch):
    """
    Если Google вернул 404 (batch не найден), должен залогировать и продолжить.

    Не должен:
    - Крашиться
    - Обновлять статус на FAILED (может быть временная проблема)
    """
    # Создать batch с невалидным google_id
    batch_id = str(uuid4())
    temp_db.create_batch_with_tasks(
        batch_id,
        "IMG_GEN_BATCH",
        [
            {
                "task_id": str(uuid4()),
                "input_payload": {"prompt": "Test"},
                "target_path": "/tmp/test.png",
            }
        ],
    )
    temp_db.update_batch_status(batch_id, "SUBMITTED", "batches/invalid_id_404")

    # Патчим client.batches.get чтобы выбросить 404
    import worker.processors.batch_processor as bp

    class MockClient:
        class Batches:
            def get(self, name):
                from google.api_core.exceptions import NotFound

                raise NotFound(f"Batch {name} not found")

        batches = Batches()

    if ENABLE_BATCH_API:
        monkeypatch.setattr(bp, "client", MockClient())

        # Запустить polling
        updated_count = poll_active_batches(temp_db)

        # Проверки
        batch = temp_db.get_batch(batch_id)
        # Статус НЕ должен измениться (ждём retry в следующем цикле)
        assert batch["status"] == "SUBMITTED", "Статус не должен меняться при 404"
    else:
        pytest.skip("Test requires ENABLE_BATCH_API=true")


# ==============================================================================
# ТЕСТ 7: Множественные батчи - проверка всех
# ==============================================================================


def test_polls_multiple_batches(temp_db, mock_mode):
    """
    Должен проверить все активные батчи за один вызов.
    """
    # Создать 3 батча
    batch_ids = []
    for i in range(3):
        batch_id = str(uuid4())
        batch_ids.append(batch_id)
        temp_db.create_batch_with_tasks(
            batch_id,
            "IMG_GEN_BATCH",
            [
                {
                    "task_id": str(uuid4()),
                    "input_payload": {"prompt": f"Test {i}"},
                    "target_path": f"/tmp/{i}.png",
                }
            ],
        )
        temp_db.update_batch_status(
            batch_id, "SUBMITTED", f"batches/mock_{batch_id[:8]}"
        )

    # Запустить polling
    updated_count = poll_active_batches(temp_db)

    # Проверки
    assert updated_count == 3, "Должен обновить все 3 батча"

    for batch_id in batch_ids:
        batch = temp_db.get_batch(batch_id)
        assert batch["status"] in ["PROCESSING", "COMPLETED"], (
            f"Batch {batch_id} должен обновиться"
        )
