# Шаг 5: MCP Tools Integration — Инструменты для агента

**Время выполнения:** 3-4 часа  
**Сложность:** Высокая  
**Стоимость тестирования:** $0.00 (только вызовы инструментов, без генерации)

---

## Цель шага

Создать **4 MCP инструмента** для управления асинхронными задачами. После этого шага:

- AI-агент может создавать пакеты изображений через `batch_generate_images`
- AI-агент может генерировать аудио через `queue_generate_audio`
- AI-агент может проверять статус задач через `check_task_status`
- AI-агент может проверять прогресс пакетов через `check_batch_progress`
- Все инструменты интегрированы в FastMCP сервер

---

## Что нужно сделать

Создать **4 новых инструмента** в FastMCP сервере:

| Инструмент | Назначение | Сложность |
|-----------|-----------|----------|
| `batch_generate_images` | Создать пакет изображений (async) | Высокая |
| `queue_generate_audio` | Создать TTS задачу (async) | Средняя |
| `check_task_status` | Проверить статус задачи | Низкая |
| `check_batch_progress` | Проверить прогресс пакета | Низкая |

---

## Инструмент 1: batch_generate_images

### Назначение

Создать **batch задач** для генерации изображений через Google Batch API.

**Когда использовать:**

- Пользователь хочет создать **10+ изображений**
- Нужна **экономия 50%** (batch дешевле sync)
- Не важна скорость (результат через 1-5 минут)

---

### Параметры

**Schema:**

```python
@mcp.tool()
async def batch_generate_images(
    prompts: List[str],
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    model_type: Literal["fast", "pro"] = "fast"
) -> dict:
    """
    Create a batch of image generation tasks.
    
    Args:
        prompts: List of English prompts (2-100 items)
        aspect_ratio: Image aspect ratio (default: "1:1")
        resolution: Output resolution: "1K" or "2K" (default: "1K")
        model_type: Model: "fast" or "pro" (default: "fast")
    
    Returns:
        {
            "batch_id": "uuid",
            "total_tasks": 10,
            "status": "PENDING",
            "estimated_cost": "$0.025",
            "estimated_time": "2-5 minutes",
            "message": "Batch created. Use check_batch_progress(batch_id) to track."
        }
    """
```

---

### Алгоритм

```
1. Валидация входных данных
   └─ 2 ≤ len(prompts) ≤ 100
   └─ aspect_ratio in VALID_RATIOS
   └─ resolution in ["1K", "2K"]

2. Создать batch_id
   └─ str(uuid4())

3. Создать список задач
   └─ Для каждого prompt:
      ├─ task_id = str(uuid4())
      ├─ input_payload = {prompt, aspect_ratio, resolution, model_type}
      └─ target_path = f"output/images/{task_id}.png"

4. Записать в БД
   └─ db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks)

5. Вернуть результат
   └─ batch_id, total_tasks, статус, стоимость
```

---

### Пример реализации

**Файл:** `server.py`

```python
from fastmcp import FastMCP
from database import DatabaseManager
from uuid import uuid4
from typing import List, Literal
import json

mcp = FastMCP("Gemini Media MCP")
db = DatabaseManager()

VALID_ASPECT_RATIOS = [
    "1:1", "16:9", "9:16", "4:3", "3:4",
    "2:3", "3:2", "4:5", "5:4", "21:9"
]

@mcp.tool()
async def batch_generate_images(
    prompts: List[str],
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    model_type: Literal["fast", "pro"] = "fast"
) -> dict:
    """
    Create a batch of image generation tasks.
    
    Cost savings: 50% cheaper than sync generation.
    Processing time: 2-5 minutes.
    """
    # 1. Валидация
    if not (2 <= len(prompts) <= 100):
        raise ValueError("prompts must contain 2-100 items")
    
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise ValueError(f"Invalid aspect_ratio. Valid: {VALID_ASPECT_RATIOS}")
    
    if resolution not in ["1K", "2K"]:
        raise ValueError("resolution must be '1K' or '2K'")
    
    # 2. Создать batch_id
    batch_id = str(uuid4())
    
    # 3. Создать задачи
    tasks = []
    for prompt in prompts:
        task_id = str(uuid4())
        tasks.append({
            "task_id": task_id,
            "input_payload": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "model_type": model_type
            },
            "target_path": f"output/images/{task_id}.png"
        })
    
    # 4. Записать в БД
    db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks)
    
    # 5. Расчет стоимости
    cost_per_image = 0.0025  # $0.0025 за изображение (batch)
    estimated_cost = len(prompts) * cost_per_image
    
    # 6. Вернуть результат
    return {
        "batch_id": batch_id,
        "total_tasks": len(prompts),
        "status": "PENDING",
        "estimated_cost": f"${estimated_cost:.4f}",
        "estimated_time": "2-5 minutes",
        "message": f"Batch created with {len(prompts)} tasks. Use check_batch_progress('{batch_id}') to track progress."
    }
```

---

## Инструмент 2: queue_generate_audio

### Назначение

Создать **TTS задачу** для синхронной генерации аудио.

**Когда использовать:**

- Пользователь хочет создать **1 аудио файл**
- Нужна **быстрая обработка** (1-3 секунды)
- Применяется rate limiting (20 задач в минуту)

---

### Параметры

**Schema:**

```python
@mcp.tool()
async def queue_generate_audio(
    text: str,
    voice: str = "Puck",
    model: str = "gemini-2.5-flash-preview-tts",
    output_path: str = None
) -> dict:
    """
    Create a TTS task for audio generation.
    
    Args:
        text: Text to synthesize (max 5000 characters)
        voice: Voice name (default: "Puck")
        model: TTS model (default: "gemini-2.5-flash-preview-tts")
        output_path: Optional custom output path
    
    Returns:
        {
            "task_id": "uuid",
            "status": "PENDING",
            "estimated_cost": "$0.01",
            "estimated_time": "5-10 seconds",
            "message": "Task created. Use check_task_status(task_id) to track."
        }
    """
```

---

### Алгоритм

```
1. Валидация
   └─ len(text) ≤ 5000
   └─ voice in VALID_VOICES

2. Создать task_id
   └─ str(uuid4())

3. Определить output_path
   └─ Если None → output_audio/{task_id}.wav

4. Записать в БД
   └─ db.create_task(task_id, "TTS_GEN_QUEUE", input_payload, target_path)

5. Вернуть результат
   └─ task_id, статус, стоимость
```

---

### Пример реализации

```python
VALID_VOICES = ["Aoede", "Charon", "Fenrir", "Kore", "Puck"]

@mcp.tool()
async def queue_generate_audio(
    text: str,
    voice: str = "Puck",
    model: str = "gemini-2.5-flash-preview-tts",
    output_path: str = None
) -> dict:
    """
    Create a TTS task for audio generation.
    
    Processing time: 5-10 seconds (includes rate limiting).
    """
    # 1. Валидация
    if len(text) > 5000:
        raise ValueError(f"Text too long: {len(text)} > 5000 characters")
    
    if voice not in VALID_VOICES:
        raise ValueError(f"Invalid voice. Valid: {VALID_VOICES}")
    
    # 2. Создать task_id
    task_id = str(uuid4())
    
    # 3. Определить output_path
    if not output_path:
        output_path = f"output_audio/{task_id}.wav"
    
    # 4. Записать в БД
    db.create_task(
        task_id=task_id,
        operation_type="TTS_GEN_QUEUE",
        input_payload=json.dumps({
            "text": text,
            "voice": voice,
            "model": model
        }),
        target_path=output_path
    )
    
    # 5. Расчет стоимости
    estimated_cost = 0.01  # ~$0.01 за задачу
    
    # 6. Вернуть результат
    return {
        "task_id": task_id,
        "status": "PENDING",
        "estimated_cost": f"${estimated_cost:.2f}",
        "estimated_time": "5-10 seconds",
        "message": f"TTS task created. Use check_task_status('{task_id}') to track progress."
    }
```

---

## Инструмент 3: check_task_status

### Назначение

Проверить **статус одной задачи**.

**Когда использовать:**

- После вызова `queue_generate_audio`
- Для отслеживания прогресса TTS задачи

---

### Параметры

**Schema:**

```python
@mcp.tool()
async def check_task_status(task_id: str) -> dict:
    """
    Check the status of a single task.
    
    Args:
        task_id: Task UUID
    
    Returns:
        {
            "task_id": "uuid",
            "status": "COMPLETED",  # PENDING, PROCESSING, COMPLETED, FAILED
            "local_path": "/path/to/file.wav",  # Если COMPLETED
            "error": "Error message",  # Если FAILED
            "created_at": "2025-11-27 10:00:00",
            "completed_at": "2025-11-27 10:00:05"
        }
    """
```

---

### Алгоритм

```
1. Получить задачу из БД
   └─ db.get_task(task_id)

2. Проверить существование
   └─ Если None → raise ValueError("Task not found")

3. Вернуть статус
   └─ task_id, status, local_path, error, timestamps
```

---

### Пример реализации

```python
@mcp.tool()
async def check_task_status(task_id: str) -> dict:
    """Check the status of a single task."""
    
    # 1. Получить задачу
    task = db.get_task(task_id)
    
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    
    # 2. Вернуть статус
    return {
        "task_id": task["id"],
        "status": task["status"],
        "operation_type": task["operation_type"],
        "local_path": task.get("local_path"),
        "error": task.get("error_details"),
        "created_at": task["created_at"],
        "completed_at": task.get("completed_at")
    }
```

---

## Инструмент 4: check_batch_progress

### Назначение

Проверить **прогресс пакета** и получить статистику.

**Когда использовать:**

- После вызова `batch_generate_images`
- Для отслеживания прогресса batch обработки

---

### Параметры

**Schema:**

```python
@mcp.tool()
async def check_batch_progress(batch_id: str) -> dict:
    """
    Check the progress of a batch.
    
    Args:
        batch_id: Batch UUID
    
    Returns:
        {
            "batch_id": "uuid",
            "status": "PROCESSING",  # PENDING, SUBMITTED, PROCESSING, COMPLETED, FAILED
            "total_tasks": 10,
            "completed_tasks": 3,
            "failed_tasks": 0,
            "pending_tasks": 7,
            "progress_percent": 30,
            "google_batch_id": "batches/abc123",  # Если отправлен в Google
            "created_at": "2025-11-27 10:00:00",
            "message": "Batch is being processed by Google Batch API"
        }
    """
```

---

### Алгоритм

```
1. Получить пакет из БД
   └─ db.get_batch(batch_id)

2. Получить статистику
   └─ db.get_batch_progress(batch_id)

3. Проверить существование
   └─ Если None → raise ValueError("Batch not found")

4. Рассчитать прогресс
   └─ progress_percent = (completed + failed) / total * 100

5. Вернуть результат
   └─ batch_id, status, статистика, прогресс
```

---

### Пример реализации

```python
@mcp.tool()
async def check_batch_progress(batch_id: str) -> dict:
    """Check the progress of a batch."""
    
    # 1. Получить пакет
    batch = db.get_batch(batch_id)
    
    if not batch:
        raise ValueError(f"Batch not found: {batch_id}")
    
    # 2. Получить статистику
    stats = db.get_batch_progress(batch_id)
    
    # 3. Рассчитать прогресс
    total = stats["total"]
    completed = stats["completed"]
    failed = stats["failed"]
    pending = stats["pending"]
    
    progress_percent = int((completed + failed) / total * 100) if total > 0 else 0
    
    # 4. Сообщение
    if batch["status"] == "PENDING":
        message = "Batch is waiting to be submitted to Google Batch API"
    elif batch["status"] == "SUBMITTED":
        message = "Batch has been submitted to Google Batch API"
    elif batch["status"] == "PROCESSING":
        message = "Batch is being processed by Google Batch API"
    elif batch["status"] == "COMPLETED":
        message = f"Batch completed: {completed} tasks succeeded, {failed} failed"
    else:
        message = f"Batch status: {batch['status']}"
    
    # 5. Вернуть результат
    return {
        "batch_id": batch["id"],
        "status": batch["status"],
        "total_tasks": total,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "pending_tasks": pending,
        "progress_percent": progress_percent,
        "google_batch_id": batch.get("google_batch_id"),
        "created_at": batch["created_at"],
        "message": message
    }
```

---

## Интеграция в server.py

### Структура файла

**До интеграции (Фаза 2):**

```python
# server.py

from fastmcp import FastMCP
from database import DatabaseManager
from worker import WorkerManager

mcp = FastMCP("Gemini Media MCP")
db = DatabaseManager()
worker = None

# Старые инструменты (analyze_image, analyze_video, ...)
# ...

# Запуск сервера
if __name__ == "__main__":
    db.initialize()
    worker = WorkerManager(db)
    worker.start()
    mcp.run()
```

---

**После интеграции (Фаза 3):**

```python
# server.py

from fastmcp import FastMCP
from database import DatabaseManager
from worker import WorkerManager
from typing import List, Literal
from uuid import uuid4
import json

mcp = FastMCP("Gemini Media MCP")
db = DatabaseManager()
worker = None

# ============== СТАРЫЕ ИНСТРУМЕНТЫ ==============
# analyze_image, analyze_video, generate_audio_from_yaml, ...

# ============== НОВЫЕ ИНСТРУМЕНТЫ (Фаза 3) ==============

@mcp.tool()
async def batch_generate_images(...):
    # Реализация из примеров выше
    pass

@mcp.tool()
async def queue_generate_audio(...):
    # Реализация из примеров выше
    pass

@mcp.tool()
async def check_task_status(...):
    # Реализация из примеров выше
    pass

@mcp.tool()
async def check_batch_progress(...):
    # Реализация из примеров выше
    pass

# ============== ЗАПУСК СЕРВЕРА ==============

if __name__ == "__main__":
    db.initialize()
    worker = WorkerManager(db, tick_interval=30)
    worker.start()
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        worker.stop(timeout=10)
```

---

## Тестирование

### Вариант 1: Локальное тестирование (бесплатно)

**Проверка создания задач:**

```python
# scripts/test_mcp_tools.py

from server import batch_generate_images, queue_generate_audio
from server import check_task_status, check_batch_progress
import asyncio

async def test_batch_images():
    # 1. Создать batch
    result = await batch_generate_images(
        prompts=["A red car", "A blue house"],
        aspect_ratio="16:9"
    )
    
    print(f"Batch ID: {result['batch_id']}")
    print(f"Total tasks: {result['total_tasks']}")
    
    # 2. Проверить прогресс
    progress = await check_batch_progress(result["batch_id"])
    print(f"Progress: {progress}")

async def test_queue_audio():
    # 1. Создать TTS задачу
    result = await queue_generate_audio(
        text="Hello world",
        voice="Puck"
    )
    
    print(f"Task ID: {result['task_id']}")
    
    # 2. Проверить статус
    status = await check_task_status(result["task_id"])
    print(f"Status: {status}")

asyncio.run(test_batch_images())
asyncio.run(test_queue_audio())
```

**Стоимость:** $0.00 (только создание задач, не генерация)

---

### Вариант 2: E2E тест через MCP клиент

**Использование Claude Desktop:**

```json
// ~/.config/Claude/claude_desktop_config.json

{
  "mcpServers": {
    "gemini-media": {
      "command": "python",
      "args": ["C:\\PY\\gemini-media-mcp\\server.py"]
    }
  }
}
```

**Запрос к агенту:**

```
Создай 3 изображения: "красная машина", "синий дом", "зеленое дерево"
```

**Ожидаемое поведение:**

1. Агент вызывает `batch_generate_images(prompts=[...])`
2. Получает `batch_id`
3. Вызывает `check_batch_progress(batch_id)` через 30 секунд
4. Сообщает пользователю: "30% готово (1 из 3)"

---

## Проверка готовности

### Критерии успеха

- ✅ Все 4 инструмента зарегистрированы в FastMCP
- ✅ `batch_generate_images` создает batch в БД
- ✅ `queue_generate_audio` создает TTS задачу
- ✅ `check_task_status` возвращает корректный статус
- ✅ `check_batch_progress` возвращает корректную статистику
- ✅ Инструменты работают в Claude Desktop (или другом MCP клиенте)

### Проверочный тест

```bash
# 1. Запустить сервер
python server.py

# 2. В другом терминале запустить тест
python scripts/test_mcp_tools.py

# Ожидаемый вывод:
# Batch ID: uuid-here
# Total tasks: 2
# Progress: {'status': 'PENDING', 'total_tasks': 2, ...}
#
# Task ID: uuid-here
# Status: {'status': 'PENDING', ...}
```

---

## Следующий шаг

После успешной интеграции инструментов переходим к **Шагу 6: E2E Testing** → финальное тестирование всей системы.

**Файл:** `phase3_step6_testing.md`

---

**Версия:** 1.0  
**Дата:** 27 ноября 2025 г.
