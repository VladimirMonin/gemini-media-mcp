"""
Тесты для Фазы 3 Шаг 3: Batch Retrieval (получение результатов).

Проверяет функцию retrieve_completed_batches():
- Mock режим с fake JSONL
- Детерминированная сортировка по (created_at, id)
- КРИТИЧЕСКАЯ валидация: len(results) == len(tasks)
- Обработка ошибок (404, битый JSON, битый base64)
- Шардинг файлов по batch_id
- Edge cases (пустые результаты, несовпадение длин)
"""

import os
import json
import base64
import pytest
from uuid import uuid4
from pathlib import Path
from database import DatabaseManager
from worker.processors.batch_processor import retrieve_completed_batches

# Feature flag для реального API
ENABLE_BATCH_API = os.getenv("ENABLE_BATCH_API", "false").lower() == "true"


@pytest.fixture
def temp_db(tmp_path):
    """Временная БД для изолированных тестов."""
    db_path = tmp_path / "test_retrieval.db"
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
# FIXTURE: Примеры JSONL результатов от Google
# ==============================================================================


@pytest.fixture
def perfect_jsonl():
    """
    Идеальный JSONL от Google (2 успешных задачи).

    Структура: каждая строка = 1 результат (response.candidates[0].content.parts[0].inline_data.data)
    Base64: 1x1 пиксель PNG (красный цвет) для тестов
    """
    return """
{"response": {"candidates": [{"content": {"parts": [{"inline_data": {"mime_type": "image/png", "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}}], "role": "model"}, "finish_reason": "STOP"}]}}
{"response": {"candidates": [{"content": {"parts": [{"inline_data": {"mime_type": "image/png", "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}}], "role": "model"}, "finish_reason": "STOP"}]}}
""".strip()


@pytest.fixture
def broken_jsonl():
    """
    Сломанный JSONL (меньше результатов чем задач).

    Симулирует Safety Filter: отправили 3 задачи, вернулось 2 результата.
    КРИТИЧНО: Это вызовет рассинхрон индексов!
    """
    return """
{"response": {"candidates": [{"content": {"parts": [{"text": "Cat"}], "role": "model"}]}}
{"response": {"candidates": [{"content": {"parts": [{"text": "Dog"}], "role": "model"}]}}
""".strip()


@pytest.fixture
def error_jsonl():
    """
    JSONL с ошибками от Google (одна задача провалилась).

    Структура:
    - Строка 1: успех с изображением
    - Строка 2: error (Safety Filter или Invalid Prompt)
    """
    return """
{"response": {"candidates": [{"content": {"parts": [{"inline_data": {"mime_type": "image/png", "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}}], "role": "model"}]}}
{"error": {"code": 400, "message": "Image generation failed: safety filters triggered", "status": "INVALID_ARGUMENT"}}
""".strip()


@pytest.fixture
def invalid_json():
    """
    Невалидный JSON (поврежденный файл).

    Симулирует сетевой сбой или битый файл на сервере.
    Ожидаемое поведение: выбросить исключение, retry в следующем цикле.
    """
    return """
{"response": {"candidates": [{"content": {"parts
THIS_IS_NOT_VALID_JSON
""".strip()


# ==============================================================================
# ТЕСТ 1: Детерминированная сортировка (критично!)
# ==============================================================================


def test_deterministic_sorting_by_created_at_and_id(temp_db, mock_mode):
    """
    КРИТИЧЕСКИ: Задачи должны сортироваться по (created_at, id).

    Проблема: Если два tasks имеют одинаковый created_at (миллисекунды),
    сортировка только по created_at может быть нестабильной.

    Решение: Сортировка по кортежу (created_at, id).

    Сценарий:
    1. Создать 3 задачи с ОДИНАКОВЫМ created_at (эмулируем массовый INSERT)
    2. Проверить что retrieval сортирует их по ID
    3. Убедиться что порядок результатов совпадает с порядком задач
    """
    # Создать batch с 3 задачами
    batch_id = str(uuid4())
    task_ids = [str(uuid4()) for _ in range(3)]

    # Сортируем task_ids лексикографически для предсказуемости
    task_ids.sort()

    tasks_data = [
        {
            "task_id": task_ids[0],
            "input_payload": {"prompt": "Task A"},
            "target_path": f"/tmp/{task_ids[0]}.png",
        },
        {
            "task_id": task_ids[1],
            "input_payload": {"prompt": "Task B"},
            "target_path": f"/tmp/{task_ids[1]}.png",
        },
        {
            "task_id": task_ids[2],
            "input_payload": {"prompt": "Task C"},
            "target_path": f"/tmp/{task_ids[2]}.png",
        },
    ]

    temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)

    # Получить задачи из БД и проверить сортировку
    tasks = temp_db.get_tasks_by_batch(batch_id)

    # КРИТИЧЕСКАЯ ПРОВЕРКА: сортировка должна быть детерминированной
    tasks_sorted = sorted(tasks, key=lambda t: (t["created_at"], t["id"]))

    # Проверить что порядок стабилен
    for i, task in enumerate(tasks_sorted):
        assert task["id"] == task_ids[i], (
            f"Task order mismatch at index {i}: expected {task_ids[i]}, got {task['id']}"
        )

    # Этот тест проверяет только логику сортировки, не retrieval
    # Полную интеграцию проверим в test_mock_mode_processes_perfect_jsonl


# ==============================================================================
# ТЕСТ 2: КРИТИЧЕСКАЯ ВАЛИДАЦИЯ - len(results) != len(tasks)
# ==============================================================================


def test_critical_validation_length_mismatch_fails_batch(
    temp_db, mock_mode, broken_jsonl, monkeypatch
):
    """
    КРИТИЧЕСКИ: Если len(results) != len(tasks), весь батч → FAILED.

    Симулирует Safety Filter: Google отфильтровал 1 промпт из 3.

    Сценарий:
    1. Создать batch с 3 задачами
    2. Эмулировать JSONL с 2 результатами (broken_jsonl)
    3. Вызвать retrieve_completed_batches()
    4. Проверить:
       - batch.status == 'FAILED'
       - Все tasks.status == 'FAILED'
       - error_details содержит "Result count mismatch"
    """
    import worker.processors.batch_processor as bp

    # 1. Создать batch с 3 задачами
    batch_id = str(uuid4())
    task_ids = [str(uuid4()) for _ in range(3)]

    tasks_data = [
        {
            "task_id": task_ids[0],
            "input_payload": {"prompt": "Task 1"},
            "target_path": f"/tmp/{task_ids[0]}.png",
        },
        {
            "task_id": task_ids[1],
            "input_payload": {"prompt": "Task 2"},
            "target_path": f"/tmp/{task_ids[1]}.png",
        },
        {
            "task_id": task_ids[2],
            "input_payload": {"prompt": "Task 3 (will be filtered by Safety)"},
            "target_path": f"/tmp/{task_ids[2]}.png",
        },
    ]

    temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)

    # Эмулировать что batch отправлен и завершён
    fake_google_id = f"batches/mock_{batch_id[:8]}"
    temp_db.update_batch_status(batch_id, "COMPLETED", fake_google_id)

    # Обновить все задачи в SUBMITTED (как после Step 1)
    for task_id in task_ids:
        temp_db.update_task_status(task_id, "SUBMITTED")

    # 2. Патчим mock чтобы вернуть broken_jsonl (2 результата вместо 3)
    class MockBatch:
        output_file_uri = "https://fake.url/results.jsonl"

    class MockClient:
        class Batches:
            def get(self, name):
                return MockBatch()

        batches = Batches()

    # Mock httpx для возврата broken_jsonl
    class MockResponse:
        text = broken_jsonl

        def raise_for_status(self):
            pass

    def mock_httpx_get(url):
        return MockResponse()

    # Патчим если ENABLE_BATCH_API=false (mock режим)
    if not bp.ENABLE_BATCH_API:
        # В mock режиме нужно эмулировать скачивание JSONL
        monkeypatch.setattr(bp, "client", MockClient())

        # Патчим httpx.get
        import httpx

        monkeypatch.setattr(httpx, "get", mock_httpx_get)

        # Временно включаем API для прохода проверки mock ID
        original_enable = bp.ENABLE_BATCH_API
        monkeypatch.setattr(bp, "ENABLE_BATCH_API", True)

    # 3. Запустить retrieval
    processed = retrieve_completed_batches(temp_db)

    # Восстановить флаг
    if not original_enable:
        monkeypatch.setattr(bp, "ENABLE_BATCH_API", False)

    # 4. Проверки КРИТИЧЕСКИЕ
    batch = temp_db.get_batch(batch_id)

    assert batch["status"] == "FAILED", (
        f"Batch должен быть FAILED при рассинхроне, получили: {batch['status']}"
    )

    # Проверить что ВСЕ задачи помечены FAILED
    for task_id in task_ids:
        task = temp_db.get_task(task_id)
        assert task["status"] == "FAILED", (
            f"Task {task_id} должна быть FAILED, получили: {task['status']}"
        )

        # Проверить что error содержит объяснение
        assert task.get("error_details"), "error_details должен быть заполнен"
        assert "mismatch" in task["error_details"].lower(), (
            f"error_details должен содержать 'mismatch', получили: {task['error_details']}"
        )

    assert processed == 1, "Должен обработать 1 batch (пометить FAILED)"


# ==============================================================================
# ТЕСТ 3: Mock режим - идеальный JSONL
# ==============================================================================


def test_mock_mode_processes_perfect_jsonl(temp_db, mock_mode):
    """
    Mock режим должен обработать идеальный JSONL без API.

    Сценарий:
    1. Создать batch с 2 задачами в статусе COMPLETED
    2. Эмулировать JSONL с 2 успешными результатами
    3. Вызвать retrieve_completed_batches()
    4. Проверить:
       - Задачи перешли в COMPLETED
       - Файлы сохранились в media/generated/{batch_id}/{task_id}.png
       - Батч закрылся (status=COMPLETED, completed_at заполнен)
    """
    pytest.skip("Waiting for JSONL structure from mentor")


# ==============================================================================
# ТЕСТ 4: Шардинг файлов по batch_id
# ==============================================================================


def test_file_sharding_by_batch_id(temp_db, mock_mode, tmp_path):
    """
    Файлы должны сохраняться с шардингом: media/generated/{batch_id}/{task_id}.png

    Обоснование:
    - 10 000 файлов в одной папке → проводник виснет
    - Легко чистить старые батчи (удалить папку batch_id)

    Сценарий:
    1. Создать batch с 2 задачами
    2. Обработать результаты
    3. Проверить структуру папок:
       media/generated/{batch_id}/task1.png
       media/generated/{batch_id}/task2.png
    """
    pytest.skip("Waiting for JSONL structure from mentor")


# ==============================================================================
# ТЕСТ 5: Фильтрация - только COMPLETED батчи
# ==============================================================================


def test_filters_only_completed_batches(temp_db, mock_mode):
    """
    Должен обрабатывать только батчи со статусом COMPLETED.

    Сценарий:
    1. Создать 3 батча: PENDING, PROCESSING, COMPLETED
    2. Вызвать retrieve_completed_batches()
    3. Проверить что обработан только COMPLETED
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

    # Batch 2: PROCESSING (обрабатывается)
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
    temp_db.update_batch_status(
        batch2_id, "PROCESSING", f"batches/mock_{batch2_id[:8]}"
    )

    # Batch 3: COMPLETED (готов к retrieval)
    batch3_id = str(uuid4())
    temp_db.create_batch_with_tasks(
        batch3_id,
        "IMG_GEN_BATCH",
        [
            {
                "task_id": str(uuid4()),
                "input_payload": {"prompt": "3"},
                "target_path": "/tmp/3.png",
            }
        ],
    )
    temp_db.update_batch_status(batch3_id, "COMPLETED", f"batches/mock_{batch3_id[:8]}")

    # Запустить retrieval
    processed = retrieve_completed_batches(temp_db)

    # Проверки
    assert processed == 1, "Должен обработать только 1 batch (COMPLETED)"

    batch1 = temp_db.get_batch(batch1_id)
    batch2 = temp_db.get_batch(batch2_id)
    batch3 = temp_db.get_batch(batch3_id)

    assert batch1["status"] == "PENDING", "Batch 1 не должен измениться"
    assert batch2["status"] == "PROCESSING", "Batch 2 не должен измениться"
    # Batch 3 проверим после реализации mock JSONL


# ==============================================================================
# ТЕСТ 6: Обработка ошибок - битый JSON
# ==============================================================================


def test_handles_invalid_json_gracefully(temp_db, mock_mode):
    """
    Если JSONL поврежден, должен залогировать и пометить batch FAILED.

    Сценарий:
    1. Создать batch в статусе COMPLETED
    2. Эмулировать битый JSONL (невалидный JSON)
    3. Вызвать retrieve_completed_batches()
    4. Проверить:
       - batch.status == 'FAILED' (или остался COMPLETED для retry?)
       - Логируется ошибка парсинга
    """
    pytest.skip("Waiting for implementation decision: FAILED vs retry")


# ==============================================================================
# ТЕСТ 7: Обработка ошибок - output_file_uri is None
# ==============================================================================


def test_skips_batch_without_output_file_uri(temp_db, mock_mode):
    """
    Если output_file_uri отсутствует, должен пропустить batch (не крашиться).

    Причина: Batch еще не полностью обработан Google.
    Действие: Пропустить, проверить в следующем цикле.

    Сценарий:
    1. Создать batch в статусе COMPLETED
    2. Эмулировать google_batch без output_file_uri
    3. Вызвать retrieve_completed_batches()
    4. Проверить:
       - batch.status == 'COMPLETED' (не изменился)
       - Логируется warning
       - processed_count == 0
    """
    pytest.skip("Waiting for mock client implementation")


# ==============================================================================
# ТЕСТ 8: Обработка ошибок в задачах (error field)
# ==============================================================================


def test_processes_task_errors_from_jsonl(temp_db, mock_mode):
    """
    Если задача провалилась в Google (error field), должна пометиться FAILED.

    Сценарий:
    1. Создать batch с 2 задачами
    2. Эмулировать JSONL: 1 успех, 1 ошибка
    3. Вызвать retrieve_completed_batches()
    4. Проверить:
       - Task 1: status=COMPLETED, local_path заполнен
       - Task 2: status=FAILED, error_details заполнен
       - Batch: status=COMPLETED (обработан полностью)
    """
    pytest.skip("Waiting for JSONL structure from mentor")


# ==============================================================================
# ТЕСТ 9: Real API - опциональный E2E тест
# ==============================================================================


@pytest.mark.skipif(
    not ENABLE_BATCH_API or os.getenv("CI") == "true",
    reason="Пропускается в CI или если ENABLE_BATCH_API=false",
)
def test_real_api_e2e_cycle(temp_db):
    """
    ОПЦИОНАЛЬНЫЙ E2E тест с реальным Google Batch API.

    Требования:
    - ENABLE_BATCH_API=true
    - GEMINI_API_KEY в .env
    - Полный цикл: создать → отправить → дождаться → скачать

    Стоимость: ~$0.005 (2 изображения × $0.0025)
    """
    pytest.skip("Requires manual E2E test with real API key")


# ==============================================================================
# ТЕСТ 10: Битый base64
# ==============================================================================


def test_handles_invalid_base64_gracefully(temp_db, mock_mode):
    """
    Если base64 невалиден, задача должна пометиться FAILED.

    Сценарий:
    1. Создать batch с 1 задачей
    2. Эмулировать JSONL с битым base64 ("NOT_VALID_BASE64")
    3. Вызвать retrieve_completed_batches()
    4. Проверить:
       - task.status == 'FAILED'
       - error_details содержит "Invalid base64" или подобное
    """
    pytest.skip("Waiting for implementation")
