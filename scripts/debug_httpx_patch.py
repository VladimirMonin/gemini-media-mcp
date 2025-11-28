"""
Одноразовый скрипт для диагностики патчинга httpx в тестах.
Проверяет работоспособность broken_jsonl и механизм monkeypatch.
"""

import json

# Проверка 1: Валидность broken_jsonl
print("=" * 60)
print("ПРОВЕРКА 1: Валидность broken_jsonl")
print("=" * 60)

broken_jsonl = """
{"response": {"candidates": [{"content": {"parts": [{"text": "Cat"}], "role": "model"}}]}}
{"response": {"candidates": [{"content": {"parts": [{"text": "Dog"}], "role": "model"}}]}}
""".strip()

print(f"Raw text:\n{broken_jsonl}\n")

results = []
for i, line in enumerate(broken_jsonl.split("\n")):
    if line.strip():
        try:
            parsed = json.loads(line)
            results.append(parsed)
            print(f"✅ Line {i + 1}: OK")
        except json.JSONDecodeError as e:
            print(f"❌ Line {i + 1}: FAILED - {e}")

print(f"\nTotal results: {len(results)}")
print(f"Expected: 2 (симуляция Safety Filter: 3 задачи → 2 результата)")

# Проверка 2: Доступность httpx в batch_processor
print("\n" + "=" * 60)
print("ПРОВЕРКА 2: httpx в batch_processor")
print("=" * 60)

import worker.processors.batch_processor as bp

print(f"ENABLE_BATCH_API: {bp.ENABLE_BATCH_API}")
print(f"client: {bp.client}")
print(f"httpx в модуле: {'httpx' in dir(bp)}")

if hasattr(bp, "httpx"):
    print(f"bp.httpx.get: {bp.httpx.get}")

# Проверка 3: Патчинг httpx.get
print("\n" + "=" * 60)
print("ПРОВЕРКА 3: Симуляция патчинга httpx.get")
print("=" * 60)


class MockResponse:
    text = broken_jsonl

    def raise_for_status(self):
        pass


def mock_httpx_get(url):
    print(f"  [MOCK] httpx.get called with: {url[:50]}...")
    return MockResponse()


# Сохранить оригинал
original_get = bp.httpx.get

# Патчим
bp.httpx.get = mock_httpx_get

# Тестируем
print("Вызов bp.httpx.get('https://fake.url')...")
response = bp.httpx.get("https://fake.url/results.jsonl")
print(f"Response type: {type(response)}")
print(f"Response.text length: {len(response.text)}")

# Восстанавливаем
bp.httpx.get = original_get
print("✅ httpx.get успешно пропатчен и восстановлен")

# Проверка 4: Полный цикл с retrieve_completed_batches
print("\n" + "=" * 60)
print("ПРОВЕРКА 4: Диагностика retrieve_completed_batches")
print("=" * 60)

import tempfile
import os
from database import DatabaseManager
from uuid import uuid4

# Создаём временную БД
with tempfile.TemporaryDirectory() as tmpdir:
    db_path = os.path.join(tmpdir, "test.db")
    db = DatabaseManager()
    db.initialize(db_path)

    # Создаём batch с 3 задачами
    batch_id = str(uuid4())
    task_ids = [str(uuid4()) for _ in range(3)]

    tasks_data = [
        {
            "task_id": tid,
            "input_payload": {"prompt": f"Prompt {i}"},
            "target_path": f"/tmp/{tid}.png",
        }
        for i, tid in enumerate(task_ids)
    ]

    db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks_data)

    # Устанавливаем COMPLETED с mock google_batch_id
    fake_google_id = f"batches/mock_{batch_id[:8]}"
    db.update_batch_status(batch_id, "COMPLETED", fake_google_id)

    # Обновляем задачи в SUBMITTED
    for tid in task_ids:
        db.update_task_status(tid, "SUBMITTED")

    print(f"Batch ID: {batch_id[:8]}...")
    print(f"Tasks: {len(task_ids)}")
    print(f"Google Batch ID: {fake_google_id}")
    print(f"Batch Status: {db.get_batch(batch_id)['status']}")

    # Патчим client и httpx для теста
    class MockBatch:
        output_file_uri = "https://fake.url/results.jsonl"

    class MockBatches:
        def get(self, name):
            print(f"  [MOCK] client.batches.get({name})")
            return MockBatch()

    class MockClient:
        batches = MockBatches()

    # Сохраняем оригиналы
    orig_enable = bp.ENABLE_BATCH_API
    orig_client = bp.client
    orig_httpx_get = bp.httpx.get

    # Патчим
    bp.ENABLE_BATCH_API = True
    bp.client = MockClient()
    bp.httpx.get = mock_httpx_get

    print("\nВызов retrieve_completed_batches()...")
    from worker.processors.batch_processor import retrieve_completed_batches

    processed = retrieve_completed_batches(db)

    # Восстанавливаем
    bp.ENABLE_BATCH_API = orig_enable
    bp.client = orig_client
    bp.httpx.get = orig_httpx_get

    print(f"\nProcessed: {processed}")

    # Проверяем результат
    batch = db.get_batch(batch_id)
    print(f"Batch Status After: {batch['status']}")

    for tid in task_ids:
        task = db.get_task(tid)
        print(
            f"Task {tid[:8]}: {task['status']} | error: {task.get('error_details', 'None')[:50] if task.get('error_details') else 'None'}"
        )

    db.close()

print("\n" + "=" * 60)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 60)
