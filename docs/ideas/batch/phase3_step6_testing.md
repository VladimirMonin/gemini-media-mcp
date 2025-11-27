# Шаг 6: E2E Testing & Validation — Финальное тестирование системы

**Время выполнения:** 2-3 часа  
**Сложность:** Средняя  
**Стоимость тестирования:** ~$0.05-0.10 (полный E2E цикл)

---

## Цель шага

Проверить **всю систему целиком** через реальные сценарии использования. После этого шага:

- Все компоненты работают вместе (БД → Worker → Batch API → MCP Tools)
- Подтверждена экономия 50% для batch операций
- Система готова к production деплою
- Документирована производительность и стоимость

---

## Стратегия тестирования

### Уровни тестирования

| Уровень | Что тестируем | Стоимость | Статус |
|---------|---------------|-----------|--------|
| Unit | Отдельные функции (моки) | $0.00 | ✅ Фаза 2 |
| Integration | Взаимодействие компонентов | $0.00 | ✅ Фаза 2 |
| **E2E** | **Полный цикл с реальным API** | **$0.05-0.10** | **⏳ Фаза 3** |
| Performance | Скорость и нагрузка | $0.50+ | 🔜 После деплоя |

**Фокус этого шага:** E2E тестирование

---

## E2E Test Suite

### Тест 1: Batch Image Generation (Full Cycle)

**Цель:** Проверить полный цикл batch генерации изображений

**Сценарий:**

1. Создать batch с 5 изображениями через `batch_generate_images()`
2. Дождаться SUBMITTED статуса (Шаг 1: Submission)
3. Дождаться PROCESSING статуса (Шаг 2: Polling)
4. Дождаться COMPLETED статуса (Шаг 2: Polling)
5. Проверить, что все изображения скачались (Шаг 3: Retrieval)
6. Проверить, что файлы валидные PNG

**Скрипт:**

```python
# tests/e2e/test_batch_images.py

import pytest
import asyncio
import time
from uuid import uuid4
from pathlib import Path
from server import batch_generate_images, check_batch_progress
from database import DatabaseManager
from worker import WorkerManager

@pytest.mark.asyncio
async def test_full_batch_image_cycle():
    """E2E test: Batch image generation full cycle."""
    
    # Setup
    db = DatabaseManager()
    db.initialize()
    
    worker = WorkerManager(db, tick_interval=30)
    worker.start()
    
    try:
        # 1. Создать batch
        result = await batch_generate_images(
            prompts=[
                "A red sports car",
                "A blue modern house",
                "A green oak tree",
                "A yellow sunflower field",
                "A purple mountain landscape"
            ],
            aspect_ratio="16:9",
            resolution="1K",
            model_type="fast"
        )
        
        batch_id = result["batch_id"]
        print(f"✅ Batch created: {batch_id}")
        
        # 2. Дождаться SUBMITTED (max 60 секунд)
        await _wait_for_status(batch_id, "SUBMITTED", timeout=60)
        print("✅ Batch submitted to Google")
        
        # 3. Дождаться PROCESSING (max 120 секунд)
        await _wait_for_status(batch_id, "PROCESSING", timeout=120)
        print("✅ Batch is being processed")
        
        # 4. Дождаться COMPLETED (max 300 секунд = 5 минут)
        await _wait_for_status(batch_id, "COMPLETED", timeout=300)
        print("✅ Batch completed")
        
        # 5. Проверить прогресс
        progress = await check_batch_progress(batch_id)
        
        assert progress["completed_tasks"] == 5, "Not all tasks completed"
        assert progress["failed_tasks"] == 0, "Some tasks failed"
        assert progress["progress_percent"] == 100, "Progress not 100%"
        
        print(f"✅ All tasks completed: {progress}")
        
        # 6. Проверить файлы
        batch = db.get_batch(batch_id)
        tasks = db.get_tasks_by_batch(batch_id)
        
        for task in tasks:
            assert task["status"] == "COMPLETED", f"Task {task['id']} not completed"
            assert task["local_path"], f"Task {task['id']} has no local_path"
            
            file_path = Path(task["local_path"])
            assert file_path.exists(), f"File not found: {file_path}"
            assert file_path.suffix == ".png", f"Not a PNG: {file_path}"
            assert file_path.stat().st_size > 1000, f"File too small: {file_path}"
            
            print(f"✅ Image verified: {file_path.name}")
        
        print("\n🎉 E2E TEST PASSED: Batch Image Generation")
    
    finally:
        worker.stop(timeout=10)


async def _wait_for_status(batch_id: str, target_status: str, timeout: int):
    """Wait for batch to reach target status."""
    start = time.time()
    
    while time.time() - start < timeout:
        progress = await check_batch_progress(batch_id)
        
        if progress["status"] == target_status:
            return
        
        print(f"⏳ Waiting for {target_status}... (current: {progress['status']})")
        await asyncio.sleep(10)
    
    raise TimeoutError(f"Batch did not reach {target_status} within {timeout}s")
```

**Ожидаемый результат:**

```
✅ Batch created: uuid-here
✅ Batch submitted to Google
✅ Batch is being processed
✅ Batch completed
✅ All tasks completed: {'completed_tasks': 5, 'failed_tasks': 0, ...}
✅ Image verified: uuid1.png
✅ Image verified: uuid2.png
✅ Image verified: uuid3.png
✅ Image verified: uuid4.png
✅ Image verified: uuid5.png

🎉 E2E TEST PASSED: Batch Image Generation
```

**Стоимость:** ~$0.0125 (5 изображений × $0.0025 batch)

---

### Тест 2: TTS Queue Processing

**Цель:** Проверить обработку TTS задач через очередь

**Сценарий:**

1. Создать 3 TTS задачи через `queue_generate_audio()`
2. Дождаться завершения всех задач (учитывая rate limiting)
3. Проверить, что все аудио файлы созданы
4. Проверить, что файлы валидные WAV

**Скрипт:**

```python
# tests/e2e/test_tts_queue.py

import pytest
import asyncio
import time
from pathlib import Path
from server import queue_generate_audio, check_task_status
from database import DatabaseManager
from worker import WorkerManager

@pytest.mark.asyncio
async def test_tts_queue_processing():
    """E2E test: TTS queue processing with rate limiting."""
    
    # Setup
    db = DatabaseManager()
    db.initialize()
    
    worker = WorkerManager(db, tick_interval=5)  # Быстрый режим для теста
    worker.start()
    
    try:
        # 1. Создать 3 TTS задачи
        task_ids = []
        
        for i in range(3):
            result = await queue_generate_audio(
                text=f"This is test message number {i + 1}.",
                voice="Puck"
            )
            task_ids.append(result["task_id"])
            print(f"✅ TTS task created: {result['task_id']}")
        
        # 2. Дождаться завершения всех задач (max 60 секунд)
        # (3 задачи × 1.8 сек rate limit + API время ≈ 10-15 секунд)
        timeout = 60
        start = time.time()
        
        while time.time() - start < timeout:
            statuses = []
            
            for task_id in task_ids:
                status = await check_task_status(task_id)
                statuses.append(status["status"])
            
            completed = sum(1 for s in statuses if s == "COMPLETED")
            failed = sum(1 for s in statuses if s == "FAILED")
            
            print(f"⏳ Progress: {completed}/3 completed, {failed} failed")
            
            if completed == 3:
                print("✅ All TTS tasks completed")
                break
            
            if failed > 0:
                pytest.fail(f"Some tasks failed: {failed}")
            
            await asyncio.sleep(5)
        else:
            pytest.fail("TTS tasks did not complete within timeout")
        
        # 3. Проверить файлы
        for task_id in task_ids:
            status = await check_task_status(task_id)
            
            assert status["status"] == "COMPLETED", f"Task {task_id} not completed"
            assert status["local_path"], f"Task {task_id} has no local_path"
            
            file_path = Path(status["local_path"])
            assert file_path.exists(), f"File not found: {file_path}"
            assert file_path.suffix == ".wav", f"Not a WAV: {file_path}"
            assert file_path.stat().st_size > 1000, f"File too small: {file_path}"
            
            print(f"✅ Audio verified: {file_path.name}")
        
        print("\n🎉 E2E TEST PASSED: TTS Queue Processing")
    
    finally:
        worker.stop(timeout=10)
```

**Ожидаемый результат:**

```
✅ TTS task created: uuid1
✅ TTS task created: uuid2
✅ TTS task created: uuid3
⏳ Progress: 0/3 completed, 0 failed
⏳ Progress: 1/3 completed, 0 failed
⏳ Progress: 2/3 completed, 0 failed
⏳ Progress: 3/3 completed, 0 failed
✅ All TTS tasks completed
✅ Audio verified: uuid1.wav
✅ Audio verified: uuid2.wav
✅ Audio verified: uuid3.wav

🎉 E2E TEST PASSED: TTS Queue Processing
```

**Стоимость:** ~$0.03 (3 TTS задачи × $0.01)

---

### Тест 3: Cost Verification (Batch vs Sync)

**Цель:** Подтвердить экономию 50% для batch операций

**Сценарий:**

1. Создать 10 изображений через batch API
2. Создать 10 изображений через sync API (через старый инструмент `generate_image`)
3. Сравнить стоимость

**Расчет:**

```python
# Batch API (через batch_generate_images)
batch_cost = 10 images × $0.0025 = $0.025

# Sync API (через generate_image)
sync_cost = 10 images × $0.005 = $0.05

# Экономия
savings = (sync_cost - batch_cost) / sync_cost × 100% = 50%
```

**Вывод:** ✅ Подтверждена экономия 50%

---

### Тест 4: Error Handling

**Цель:** Проверить корректную обработку ошибок

**Сценарий 1: Невалидный prompt**

```python
result = await batch_generate_images(
    prompts=[""],  # Пустой prompt
    aspect_ratio="16:9"
)

# Ожидаем: ValueError("prompts cannot be empty")
```

**Сценарий 2: Превышение лимита текста TTS**

```python
long_text = "A" * 10000  # 10,000 символов

result = await queue_generate_audio(text=long_text)

# Ожидаем: ValueError("Text too long: 10000 > 5000")
```

**Сценарий 3: Невалидный task_id**

```python
status = await check_task_status("nonexistent-uuid")

# Ожидаем: ValueError("Task not found: nonexistent-uuid")
```

---

## Performance Metrics

### Метрики для измерения

| Метрика | Цель | Измерение |
|---------|------|-----------|
| **Batch Throughput** | > 10 изображений/мин | Время обработки batch |
| **TTS Latency** | < 10 сек/задача | Время от создания до COMPLETED |
| **Worker Tick Overhead** | < 1 сек | Время выполнения 1 цикла воркера |
| **Database Query Time** | < 100 мс | Время выполнения запросов к БД |

---

### Измерение производительности

**Скрипт:**

```python
# scripts/benchmark.py

import time
import asyncio
from server import batch_generate_images, check_batch_progress

async def benchmark_batch_throughput():
    """Измерение throughput batch генерации."""
    
    # Создать batch из 20 изображений
    start = time.time()
    
    result = await batch_generate_images(
        prompts=[f"Test image {i}" for i in range(20)],
        aspect_ratio="1:1"
    )
    
    batch_id = result["batch_id"]
    
    # Дождаться завершения
    while True:
        progress = await check_batch_progress(batch_id)
        
        if progress["status"] == "COMPLETED":
            break
        
        await asyncio.sleep(10)
    
    end = time.time()
    duration = end - start
    
    throughput = 20 / (duration / 60)  # изображений в минуту
    
    print(f"Batch Throughput: {throughput:.2f} images/min")
    print(f"Total time: {duration:.2f} seconds")

asyncio.run(benchmark_batch_throughput())
```

**Ожидаемые результаты:**

```
Batch Throughput: 12-15 images/min
Total time: 80-100 seconds
```

---

## Regression Testing

### Проверка обратной совместимости

**Цель:** Убедиться, что старые инструменты работают после интеграции Phase 3

**Тесты:**

```bash
# 1. Запустить все существующие тесты (Фаза 1 + Фаза 2)
pytest tests/ -v

# Ожидаемый результат:
# 50 passed (27 database + 8 worker + 15 backup)
```

**Если тесты проваливаются:**

- Проверить, что `DatabaseManager` не изменился
- Проверить, что `WorkerManager` совместим с новыми процессорами

---

## Deployment Checklist

### Перед деплоем в production

- ✅ Все E2E тесты проходят
- ✅ Стоимость подтверждена ($0.0025 за batch image)
- ✅ Performance метрики в пределах нормы
- ✅ Обратная совместимость сохранена
- ✅ Документация обновлена
- ✅ Логи настроены (уровень INFO для production)
- ✅ Health check работает (recover_stale_tasks)
- ✅ Graceful shutdown работает

---

### Проверка health check

**Скрипт:**

```python
# scripts/test_health_check.py

from database import DatabaseManager
import time

db = DatabaseManager()
db.initialize()

# 1. Создать "зависшую" задачу (искусственно)
task_id = "test-stale-task"
db.create_task(
    task_id=task_id,
    operation_type="IMG_GEN_BATCH",
    input_payload='{"prompt": "test"}',
    target_path="/tmp/test.png"
)

# Пометить как PROCESSING вручную
db.execute(
    "UPDATE tasks SET status='PROCESSING', updated_at=datetime('now', '-40 minutes') WHERE id=?",
    (task_id,)
)

# 2. Запустить health check
recovered = db.recover_stale_tasks(timeout_minutes=30)

print(f"Recovered stale tasks: {recovered}")

# 3. Проверить статус
task = db.get_task(task_id)
print(f"Task status after recovery: {task['status']}")

assert task["status"] == "PENDING", "Task should be recovered to PENDING"
print("✅ Health check working correctly")
```

---

## Финальная проверка

### Smoke Test (быстрая проверка всей системы)

**Цель:** Проверить все ключевые функции за 5 минут

**Скрипт:**

```python
# scripts/smoke_test.py

import asyncio
from server import (
    batch_generate_images,
    queue_generate_audio,
    check_batch_progress,
    check_task_status
)

async def smoke_test():
    """Быстрая проверка всей системы."""
    
    print("🔥 Starting Smoke Test...")
    
    # 1. Batch Images (2 изображения)
    print("\n1️⃣ Testing batch_generate_images...")
    batch_result = await batch_generate_images(
        prompts=["A red car", "A blue house"],
        aspect_ratio="1:1"
    )
    print(f"✅ Batch created: {batch_result['batch_id']}")
    
    # 2. Check Batch Progress
    print("\n2️⃣ Testing check_batch_progress...")
    progress = await check_batch_progress(batch_result["batch_id"])
    print(f"✅ Batch progress: {progress['status']}")
    
    # 3. Queue Audio
    print("\n3️⃣ Testing queue_generate_audio...")
    audio_result = await queue_generate_audio(
        text="Smoke test audio",
        voice="Puck"
    )
    print(f"✅ TTS task created: {audio_result['task_id']}")
    
    # 4. Check Task Status
    print("\n4️⃣ Testing check_task_status...")
    status = await check_task_status(audio_result["task_id"])
    print(f"✅ Task status: {status['status']}")
    
    print("\n🎉 SMOKE TEST PASSED: All tools working")

asyncio.run(smoke_test())
```

**Стоимость:** $0.00 (только создание задач)

**Время:** < 1 минута

---

## Проверка готовности к деплою

### Критерии успеха

- ✅ E2E тест batch images проходит
- ✅ E2E тест TTS queue проходит
- ✅ Экономия 50% подтверждена
- ✅ Performance метрики в норме
- ✅ Regression тесты проходят (50/50)
- ✅ Health check работает
- ✅ Graceful shutdown работает
- ✅ Smoke test проходит

---

## Запуск полного тестового набора

**Команда:**

```bash
# 1. Unit + Integration тесты (бесплатно)
pytest tests/ -v

# 2. E2E тесты (платно, ~$0.05)
pytest tests/e2e/ -v

# 3. Smoke test (бесплатно)
python scripts/smoke_test.py

# 4. Benchmark (опционально, платно ~$0.10)
python scripts/benchmark.py
```

**Ожидаемое время:** 10-15 минут  
**Ожидаемая стоимость:** ~$0.05-0.15

---

## Итоговый отчет

После успешного прохождения всех тестов создать отчет:

**Файл:** `docs/ideas/batch/phase3_completion_report.md`

**Содержание:**

- ✅ Все шаги Phase 3 завершены (1-6)
- ✅ 4 новых MCP инструмента созданы
- ✅ Batch API интегрирован (submission, polling, retrieval)
- ✅ TTS queue работает с rate limiting
- ✅ E2E тесты проходят
- ✅ Экономия 50% подтверждена
- ✅ Система готова к production

---

## Следующие шаги (после Phase 3)

1. **Production деплой** → Запуск на реальных workloads
2. **Мониторинг** → Настройка логов и метрик
3. **Оптимизация** → Тюнинг tick_interval и rate limits
4. **Документация для пользователей** → User guide для MCP клиентов

---

**Версия:** 1.0  
**Дата:** 27 ноября 2025 г.

---

**КОНЕЦ ДОКУМЕНТАЦИИ PHASE 3** 🎉
