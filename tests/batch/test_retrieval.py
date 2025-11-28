"""
Тесты для Фазы 3 Шаг 3: Batch Retrieval (получение результатов).

Проверяет функцию retrieve_completed_batches():
- Mock режим с генерацией файлов
- Детерминированная сортировка по (created_at, id)
- КРИТИЧЕСКАЯ валидация: len(results) == len(tasks)
- Обработка ошибок (404, битый JSON, битый base64)
- Шардинг файлов по batch_id
"""

import pytest
from uuid import uuid4
from pathlib import Path
from worker.processors.batch_processor import retrieve_completed_batches


# ==============================================================================
# ТЕСТ 1: Детерминированная сортировка (критично!)
# ==============================================================================


class TestDeterministicSorting:
    """Тесты детерминированной сортировки задач."""

    def test_sorting_by_created_at_and_id(self, temp_db, mock_mode):
        """
        КРИТИЧЕСКИ: Задачи должны сортироваться по (created_at, id).

        Если два tasks имеют одинаковый created_at (миллисекунды),
        сортировка только по created_at нестабильна.
        Решение: сортировка по кортежу (created_at, id).
        """
        batch_id = str(uuid4())
        task_ids = sorted([str(uuid4()) for _ in range(3)])

        tasks_data = [
            {
                "task_id": tid,
                "input_payload": {"prompt": f"Task {i}"},
                "target_path": f"/tmp/{tid}.png",
            }
            for i, tid in enumerate(task_ids)
        ]

        temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)

        tasks = temp_db.get_tasks_by_batch(batch_id)
        tasks_sorted = sorted(tasks, key=lambda t: (t["created_at"], t["id"]))

        for i, task in enumerate(tasks_sorted):
            assert task["id"] == task_ids[i], (
                f"Task order mismatch at index {i}: expected {task_ids[i]}, got {task['id']}"
            )


# ==============================================================================
# ТЕСТ 2: КРИТИЧЕСКАЯ ВАЛИДАЦИЯ - len(results) != len(tasks)
# ==============================================================================


class TestCriticalValidation:
    """Тесты паранойя-режима валидации индексов."""

    def test_length_mismatch_fails_entire_batch(
        self, temp_db, broken_jsonl, monkeypatch
    ):
        """
        КРИТИЧЕСКИ: Если len(results) != len(tasks), весь батч → FAILED.

        Симулирует Safety Filter: Google отфильтровал 1 промпт из 3.
        """
        import worker.processors.batch_processor as bp

        batch_id = str(uuid4())
        task_ids = [str(uuid4()) for _ in range(3)]

        tasks_data = [
            {
                "task_id": tid,
                "input_payload": {"prompt": f"Task {i}"},
                "target_path": f"/tmp/{tid}.png",
            }
            for i, tid in enumerate(task_ids)
        ]

        temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)

        fake_google_id = f"batches/real_{batch_id[:8]}"
        temp_db.update_batch_status(batch_id, "COMPLETED", fake_google_id)

        for tid in task_ids:
            temp_db.update_task_status(tid, "SUBMITTED")

        # Mock client и httpx
        class MockBatch:
            output_file_uri = "https://fake.url/results.jsonl"

        class MockBatches:
            def get(self, name):
                return MockBatch()

        class MockClient:
            batches = MockBatches()

        jsonl_content = broken_jsonl

        class MockResponse:
            text = jsonl_content

            def raise_for_status(self):
                pass

        monkeypatch.setattr(bp, "ENABLE_BATCH_API", True)
        monkeypatch.setattr(bp, "client", MockClient())
        monkeypatch.setattr(bp.httpx, "get", lambda url: MockResponse())

        processed = retrieve_completed_batches(temp_db)

        batch = temp_db.get_batch(batch_id)
        assert batch["status"] == "FAILED"

        for tid in task_ids:
            task = temp_db.get_task(tid)
            assert task["status"] == "FAILED"
            assert "mismatch" in task.get("error_details", "").lower()

        assert processed == 0


# ==============================================================================
# ТЕСТ 3: Mock режим
# ==============================================================================


class TestMockMode:
    """Тесты mock режима (без реального API)."""

    def test_processes_batch_without_api(
        self, temp_db, mock_mode, tmp_path, monkeypatch
    ):
        """Mock режим должен создать файлы без реального API."""
        monkeypatch.chdir(tmp_path)

        batch_id = str(uuid4())
        task_ids = sorted([str(uuid4()), str(uuid4())])

        tasks_data = [
            {
                "task_id": tid,
                "input_payload": {"prompt": f"Prompt {i}"},
                "target_path": f"/tmp/{tid}.png",
            }
            for i, tid in enumerate(task_ids)
        ]

        temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)
        temp_db.update_batch_status(
            batch_id, "COMPLETED", f"batches/mock_{batch_id[:8]}"
        )

        for tid in task_ids:
            temp_db.update_task_status(tid, "SUBMITTED")

        processed = retrieve_completed_batches(temp_db)

        assert processed == 1

        for tid in task_ids:
            task = temp_db.get_task(tid)
            assert task["status"] == "COMPLETED"
            assert task.get("local_path")

            local_path = Path(task["local_path"])
            assert local_path.exists()

            with open(local_path, "rb") as f:
                header = f.read(8)
            assert header[:4] == b"\x89PNG"

        batch = temp_db.get_batch(batch_id)
        assert batch["status"] == "COMPLETED"
        assert batch.get("completed_at")


# ==============================================================================
# ТЕСТ 4: Шардинг файлов
# ==============================================================================


class TestFileSharding:
    """Тесты файлового шардинга по batch_id."""

    def test_files_saved_in_batch_folders(
        self, temp_db, mock_mode, tmp_path, monkeypatch
    ):
        """Файлы должны сохраняться в media/generated/{batch_id}/ при fallback."""
        monkeypatch.chdir(tmp_path)

        batch1_id = str(uuid4())
        batch2_id = str(uuid4())
        task1_id, task2_id = str(uuid4()), str(uuid4())
        task3_id, task4_id = str(uuid4()), str(uuid4())

        # Используем путь с запрещёнными символами для Windows (< > : " | ? *)
        # чтобы гарантированно вызвать fallback на шардинг
        invalid_path = "Z:\\<invalid>|path*"

        # Batch 1
        temp_db.create_batch_with_tasks(
            batch1_id,
            "IMG_GEN_BATCH",
            [
                {
                    "task_id": task1_id,
                    "input_payload": {"prompt": "A"},
                    "target_path": f"{invalid_path}/{task1_id}.png",
                },
                {
                    "task_id": task2_id,
                    "input_payload": {"prompt": "B"},
                    "target_path": f"{invalid_path}/{task2_id}.png",
                },
            ],
        )
        temp_db.update_batch_status(
            batch1_id, "COMPLETED", f"batches/mock_{batch1_id[:8]}"
        )

        # Batch 2
        temp_db.create_batch_with_tasks(
            batch2_id,
            "IMG_GEN_BATCH",
            [
                {
                    "task_id": task3_id,
                    "input_payload": {"prompt": "C"},
                    "target_path": f"{invalid_path}/{task3_id}.png",
                },
                {
                    "task_id": task4_id,
                    "input_payload": {"prompt": "D"},
                    "target_path": f"{invalid_path}/{task4_id}.png",
                },
            ],
        )
        temp_db.update_batch_status(
            batch2_id, "COMPLETED", f"batches/mock_{batch2_id[:8]}"
        )

        processed = retrieve_completed_batches(temp_db)
        assert processed == 2

        media_dir = tmp_path / "media" / "generated"
        assert media_dir.exists()

        batch1_dir = media_dir / batch1_id
        assert (batch1_dir / f"{task1_id}.png").exists()
        assert (batch1_dir / f"{task2_id}.png").exists()

        batch2_dir = media_dir / batch2_id
        assert (batch2_dir / f"{task3_id}.png").exists()
        assert (batch2_dir / f"{task4_id}.png").exists()

        # Файлы не перемешались
        assert not (batch1_dir / f"{task3_id}.png").exists()


# ==============================================================================
# ТЕСТ 5: Фильтрация по статусу
# ==============================================================================


class TestStatusFiltering:
    """Тесты фильтрации батчей по статусу."""

    def test_only_completed_batches_processed(self, temp_db, mock_mode):
        """Должен обрабатывать только батчи со статусом COMPLETED."""
        # PENDING
        batch1_id = str(uuid4())
        tid1 = str(uuid4())
        temp_db.create_batch_with_tasks(
            batch1_id,
            "IMG_GEN_BATCH",
            [
                {
                    "task_id": tid1,
                    "input_payload": {"prompt": "1"},
                    "target_path": f"/tmp/{tid1}.png",
                }
            ],
        )

        # PROCESSING
        batch2_id = str(uuid4())
        tid2 = str(uuid4())
        temp_db.create_batch_with_tasks(
            batch2_id,
            "IMG_GEN_BATCH",
            [
                {
                    "task_id": tid2,
                    "input_payload": {"prompt": "2"},
                    "target_path": f"/tmp/{tid2}.png",
                }
            ],
        )
        temp_db.update_batch_status(
            batch2_id, "PROCESSING", f"batches/mock_{batch2_id[:8]}"
        )

        # COMPLETED
        batch3_id = str(uuid4())
        tid3 = str(uuid4())
        temp_db.create_batch_with_tasks(
            batch3_id,
            "IMG_GEN_BATCH",
            [
                {
                    "task_id": tid3,
                    "input_payload": {"prompt": "3"},
                    "target_path": f"/tmp/{tid3}.png",
                }
            ],
        )
        temp_db.update_batch_status(
            batch3_id, "COMPLETED", f"batches/mock_{batch3_id[:8]}"
        )

        processed = retrieve_completed_batches(temp_db)

        assert processed == 1
        assert temp_db.get_batch(batch1_id)["status"] == "PENDING"
        assert temp_db.get_batch(batch2_id)["status"] == "PROCESSING"


# ==============================================================================
# ТЕСТ 6: Обработка ошибок
# ==============================================================================


class TestErrorHandling:
    """Тесты обработки ошибок."""

    def test_invalid_json_fails_batch(self, temp_db, invalid_json, monkeypatch):
        """Битый JSON должен пометить batch и tasks как FAILED."""
        import worker.processors.batch_processor as bp

        batch_id = str(uuid4())
        task_ids = [str(uuid4()), str(uuid4())]

        tasks_data = [
            {
                "task_id": tid,
                "input_payload": {"prompt": f"Prompt {i}"},
                "target_path": f"/tmp/{tid}.png",
            }
            for i, tid in enumerate(task_ids)
        ]

        temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)
        temp_db.update_batch_status(
            batch_id, "COMPLETED", f"batches/real_{batch_id[:8]}"
        )

        for tid in task_ids:
            temp_db.update_task_status(tid, "SUBMITTED")

        class MockBatch:
            output_file_uri = "https://fake.url/results.jsonl"

        class MockBatches:
            def get(self, name):
                return MockBatch()

        class MockClient:
            batches = MockBatches()

        broken_content = invalid_json

        class MockResponse:
            text = broken_content

            def raise_for_status(self):
                pass

        monkeypatch.setattr(bp, "ENABLE_BATCH_API", True)
        monkeypatch.setattr(bp, "client", MockClient())
        monkeypatch.setattr(bp.httpx, "get", lambda url: MockResponse())

        processed = retrieve_completed_batches(temp_db)

        assert processed == 0
        assert temp_db.get_batch(batch_id)["status"] == "FAILED"

        for tid in task_ids:
            task = temp_db.get_task(tid)
            assert task["status"] == "FAILED"
            assert "json" in task.get("error_details", "").lower()

    def test_missing_output_file_uri_skips_batch(self, temp_db, monkeypatch):
        """Batch без output_file_uri должен пропускаться (не crash)."""
        import worker.processors.batch_processor as bp

        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch_with_tasks(
            batch_id,
            "IMG_GEN_BATCH",
            [
                {
                    "task_id": task_id,
                    "input_payload": {"prompt": "Test"},
                    "target_path": f"/tmp/{task_id}.png",
                }
            ],
        )
        temp_db.update_batch_status(
            batch_id, "COMPLETED", f"batches/real_{batch_id[:8]}"
        )

        class MockBatch:
            output_file_uri = None
            state = "JOB_STATE_PENDING"

        class MockBatches:
            def get(self, name):
                return MockBatch()

        class MockClient:
            batches = MockBatches()

        monkeypatch.setattr(bp, "ENABLE_BATCH_API", True)
        monkeypatch.setattr(bp, "client", MockClient())

        processed = retrieve_completed_batches(temp_db)

        assert processed == 0
        assert temp_db.get_batch(batch_id)["status"] == "COMPLETED"
        assert temp_db.get_task(task_id)["status"] != "FAILED"

    def test_task_error_in_jsonl_marks_task_failed(
        self, temp_db, error_jsonl, monkeypatch, tmp_path
    ):
        """Ошибка в JSONL должна пометить только эту задачу как FAILED."""
        import worker.processors.batch_processor as bp

        monkeypatch.chdir(tmp_path)

        batch_id = str(uuid4())
        task_ids = sorted([str(uuid4()), str(uuid4())])

        tasks_data = [
            {
                "task_id": tid,
                "input_payload": {"prompt": f"T{i}"},
                "target_path": f"/tmp/{tid}.png",
            }
            for i, tid in enumerate(task_ids)
        ]

        temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)
        temp_db.update_batch_status(
            batch_id, "COMPLETED", f"batches/real_{batch_id[:8]}"
        )

        for tid in task_ids:
            temp_db.update_task_status(tid, "SUBMITTED")

        class MockBatch:
            output_file_uri = "https://fake.url/results.jsonl"

        class MockBatches:
            def get(self, name):
                return MockBatch()

        class MockClient:
            batches = MockBatches()

        jsonl_content = error_jsonl

        class MockResponse:
            text = jsonl_content

            def raise_for_status(self):
                pass

        monkeypatch.setattr(bp, "ENABLE_BATCH_API", True)
        monkeypatch.setattr(bp, "client", MockClient())
        monkeypatch.setattr(bp.httpx, "get", lambda url: MockResponse())

        processed = retrieve_completed_batches(temp_db)

        assert processed == 1

        task1 = temp_db.get_task(task_ids[0])
        task2 = temp_db.get_task(task_ids[1])

        assert task1["status"] == "COMPLETED"
        assert task2["status"] == "FAILED"
        assert "safety" in task2.get("error_details", "").lower()

    def test_invalid_base64_marks_task_failed(
        self, temp_db, invalid_base64_jsonl, monkeypatch
    ):
        """Битый base64 должен пометить задачу как FAILED."""
        import worker.processors.batch_processor as bp

        batch_id = str(uuid4())
        task_id = str(uuid4())

        temp_db.create_batch_with_tasks(
            batch_id,
            "IMG_GEN_BATCH",
            [
                {
                    "task_id": task_id,
                    "input_payload": {"prompt": "Test"},
                    "target_path": f"/tmp/{task_id}.png",
                }
            ],
        )
        temp_db.update_batch_status(
            batch_id, "COMPLETED", f"batches/real_{batch_id[:8]}"
        )
        temp_db.update_task_status(task_id, "SUBMITTED")

        class MockBatch:
            output_file_uri = "https://fake.url/results.jsonl"

        class MockBatches:
            def get(self, name):
                return MockBatch()

        class MockClient:
            batches = MockBatches()

        jsonl_content = invalid_base64_jsonl

        class MockResponse:
            text = jsonl_content

            def raise_for_status(self):
                pass

        monkeypatch.setattr(bp, "ENABLE_BATCH_API", True)
        monkeypatch.setattr(bp, "client", MockClient())
        monkeypatch.setattr(bp.httpx, "get", lambda url: MockResponse())

        processed = retrieve_completed_batches(temp_db)

        assert processed == 1  # Batch обработан
        task = temp_db.get_task(task_id)
        assert task["status"] == "FAILED"
