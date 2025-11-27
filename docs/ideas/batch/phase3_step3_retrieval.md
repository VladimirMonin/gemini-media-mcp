# Шаг 3: Batch Retrieval — Получение результатов

**Время выполнения:** 2-3 часа  
**Сложность:** Высокая  
**Стоимость тестирования:** ~$0.005 (скачивание результатов бесплатно, но задачи платные)

---

## Цель шага

Научить систему скачивать и обрабатывать **результаты COMPLETED пакетов**. После этого шага:

- Система автоматически скачивает JSONL файл с результатами
- Каждый результат сопоставляется с задачей по `custom_id`
- Изображения декодируются из base64 и сохраняются на диск
- Задачи переходят в статус `COMPLETED` или `FAILED`
- Пакет закрывается со статусом `COMPLETED`

---

## Что происходит сейчас (Фаза 2)

**Файл:** `worker/processors/batch_processor.py`  
**Функция:** `retrieve_completed_batches()`

```python
def retrieve_completed_batches(db: DatabaseManager) -> int:
    """ЗАГЛУШКА для Фазы 2."""
    logger.debug("[MOCK] Would retrieve completed batches")
    return 0  # Ничего не скачано
```

**Проблема:**

- Результаты лежат в Google Cloud, но не скачиваются
- Задачи остаются в статусе SUBMITTED/PROCESSING навсегда
- Пакет никогда не переходит в COMPLETED

---

## Структура результатов Google Batch API

После завершения обработки Google создает **JSONL файл** (JSON Lines):

```jsonl
{"custom_id":"task_uuid_1","response":{"candidates":[{"content":{"parts":[{"inline_data":{"mime_type":"image/png","data":"iVBORw0KGgoAAAA..."}}]}}]}}
{"custom_id":"task_uuid_2","error":{"code":400,"message":"Invalid prompt"}}
```

**Каждая строка = 1 задача:**

- **Успех:** `response.candidates[0].content.parts[0].inline_data.data` (base64)
- **Ошибка:** `error.code` + `error.message`

---

## Что нужно сделать

### 1. Найти COMPLETED пакеты

**Запрос к БД:**

```python
batches = db.get_pending_batches()
completed_batches = [
    b for b in batches
    if b["status"] == "COMPLETED" and b["google_batch_id"]
]
```

**Почему проверяем `google_batch_id`:**

- Защита от пакетов, которые завершились локально (не через Batch API)

---

### 2. Получить ссылку на файл результатов

**API вызов:**

```python
google_batch = client.batches.get(batch["google_batch_id"])
```

**Что возвращается:**

```python
google_batch.output_file_uri
# Пример: "https://generativelanguage.googleapis.com/v1/files/abc123xyz"
```

---

### 3. Скачать JSONL файл

**HTTP запрос (httpx):**

```python
import httpx

# httpx обычно уже установлен (зависимость google-genai)
response = httpx.get(google_batch.output_file_uri)
response.raise_for_status()  # Проверка на ошибки

jsonl_content = response.text
```

**Альтернатива (стандартная библиотека):**

```python
import urllib.request

with urllib.request.urlopen(google_batch.output_file_uri) as response:
    jsonl_content = response.read().decode('utf-8')
```

**Что получаем:**

```
{"custom_id":"uuid1","response":{...}}
{"custom_id":"uuid2","error":{...}}
...
```

---

### 4. Распарсить JSONL

**Парсинг построчно:**

```python
import json

results = []
for line in jsonl_content.strip().split("\n"):
    if line:
        results.append(json.loads(line))
```

**Структура результата:**

```python
result = {
    "custom_id": "task_uuid_here",
    "response": {...},  # Если успех
    "error": {...}      # Если ошибка
}
```

---

### 5. Сопоставить результаты с задачами

**Для каждого результата:**

```python
for result in results:
    task_id = result["custom_id"]
    
    if "error" in result:
        # Задача провалилась
        error_msg = result["error"]["message"]
        db.update_task_failed(task_id, error=error_msg)
    else:
        # Задача успешна — нужно сохранить изображение
        image_data = extract_image_data(result)
        local_path = save_image(task_id, image_data)
        db.update_task_completed(task_id, local_path)
```

---

### 6. Извлечь изображение из base64

**Путь к данным:**

```python
def extract_image_data(result: dict) -> str:
    """
    Извлечь base64 данные изображения из результата.
    
    Returns:
        Base64 строка (без префикса data:image/png;base64,)
    """
    candidate = result["response"]["candidates"][0]
    part = candidate["content"]["parts"][0]
    return part["inline_data"]["data"]
```

---

### 7. Сохранить изображение на диск

**Декодирование base64:**

```python
import base64
from pathlib import Path

def save_image(task_id: str, base64_data: str) -> str:
    """
    Сохранить изображение из base64.
    
    Args:
        task_id: UUID задачи (для имени файла)
        base64_data: Base64 строка
    
    Returns:
        Абсолютный путь к сохраненному файлу
    """
    # Декодировать base64
    image_bytes = base64.b64decode(base64_data)
    
    # Определить путь для сохранения
    output_dir = Path("output/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    local_path = output_dir / f"{task_id}.png"
    
    # Записать файл
    with open(local_path, "wb") as f:
        f.write(image_bytes)
    
    return str(local_path.absolute())
```

---

### 8. Обновить статусы в БД

**Успешная задача:**

```python
db.update_task_completed(task_id, local_path)
# Обновляет:
# - status = 'COMPLETED'
# - local_path = '/path/to/image.png'
# - completed_at = NOW()
```

**Провалившаяся задача:**

```python
db.update_task_failed(task_id, error="Invalid prompt")
# Обновляет:
# - status = 'FAILED'
# - error_details = 'Invalid prompt'
# - completed_at = NOW()
```

---

### 9. Закрыть пакет

**После обработки всех результатов:**

```python
db.update_batch_completed(batch["id"])
# Обновляет:
# - status = 'COMPLETED'
# - completed_at = NOW()
```

---

## Полный алгоритм

```
1. Найти COMPLETED батчи в БД
   └─ Фильтр: status='COMPLETED' AND google_batch_id IS NOT NULL

2. Для каждого батча:
   
   a) Получить ссылку на файл результатов
      └─ client.batches.get(google_batch_id)
      └─ Извлечь output_file_uri
   
   b) Скачать JSONL файл
      └─ requests.get(output_file_uri)
   
   c) Распарсить результаты
      └─ Построчно: json.loads(line)
   
   d) Для каждого результата:
      
      Если есть ошибка:
        └─ db.update_task_failed(task_id, error)
      
      Если успех:
        └─ Извлечь base64 данные
        └─ Декодировать в байты
        └─ Сохранить на диск
        └─ db.update_task_completed(task_id, local_path)
   
   e) Закрыть пакет
      └─ db.update_batch_completed(batch_id)

3. Вернуть количество обработанных батчей
```

---

## Пример реализации (концепт)

**Файл:** `worker/processors/batch_processor.py`

```python
def retrieve_completed_batches(db: DatabaseManager) -> int:
    """
    Скачивание и обработка результатов COMPLETED пакетов.
    
    Returns:
        Количество обработанных пакетов
    """
    # 1. Найти COMPLETED пакеты
    batches = db.get_pending_batches()
    completed_batches = [
        b for b in batches
        if b["status"] == "COMPLETED" and b["google_batch_id"]
    ]
    
    if not completed_batches:
        return 0
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    processed_count = 0
    
    for batch in completed_batches:
        try:
            # 2. Получить ссылку на файл
            google_batch = client.batches.get(batch["google_batch_id"])
            
            if not google_batch.output_file_uri:
                logger.warning(f"Batch {batch['id']} has no output_file_uri")
                continue
            
            # 3. Скачать JSONL (httpx вместо requests)
            import httpx
            response = httpx.get(google_batch.output_file_uri)
            response.raise_for_status()
            
            # 4. Распарсить результаты
            results = [
                json.loads(line)
                for line in response.text.strip().split("\n")
                if line
            ]
            
            # 5. Обработать каждый результат
            for result in results:
                task_id = result["custom_id"]
                
                if "error" in result:
                    # Ошибка
                    error_msg = result["error"]["message"]
                    db.update_task_failed(task_id, error=error_msg)
                    logger.warning(f"Task {task_id} failed: {error_msg}")
                else:
                    # Успех — сохранить изображение
                    task = db.get_task(task_id)
                    base64_data = _extract_image_data(result)
                    # ✅ Передаем target_path из задачи
                    local_path = _save_image(task_id, base64_data, task.get("target_path"))
                    db.update_task_completed(task_id, local_path)
                    logger.info(f"Task {task_id} completed: {local_path}")
            
            # 6. Закрыть пакет
            db.update_batch_completed(batch["id"])
            logger.info(f"Batch {batch['id']} processed: {len(results)} tasks")
            processed_count += 1
        
        except Exception as e:
            logger.error(f"Failed to retrieve batch {batch['id']}: {e}")
            # НЕ закрываем пакет — повторим в следующем цикле
    
    return processed_count


def _extract_image_data(result: dict) -> str:
    """Извлечь base64 данные изображения."""
    candidate = result["response"]["candidates"][0]
    part = candidate["content"]["parts"][0]
    return part["inline_data"]["data"]


def _save_image(task_id: str, base64_data: str, target_path: str = None) -> str:
    """
    Сохранить изображение из base64.
    
    ✅ ПРИОРИТЕТ: target_path из задачи
    ❌ FALLBACK: output/images/{task_id}.png
    """
    import base64
    from pathlib import Path
    
    image_bytes = base64.b64decode(base64_data)
    
    # Приоритет target_path
    if target_path:
        local_path = Path(target_path)
    else:
        output_dir = Path("output/images")
        output_dir.mkdir(parents=True, exist_ok=True)
        local_path = output_dir / f"{task_id}.png"
    
    # Создать директории
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(local_path, "wb") as f:
            f.write(image_bytes)
    except IOError as e:
        # Fallback если target_path недоступен
        logger.warning(f"Failed to save to {local_path}: {e}")
        output_dir = Path("output/images")
        output_dir.mkdir(parents=True, exist_ok=True)
        local_path = output_dir / f"{task_id}.png"
        
        with open(local_path, "wb") as f:
            f.write(image_bytes)
    
    return str(local_path.absolute())
```

---

## Обработка ошибок

### Ошибка 1: "output_file_uri is None"

**Причина:** Batch еще не обработан полностью

**Решение:**

```python
if not google_batch.output_file_uri:
    logger.warning(f"Batch {batch['id']} has no output file yet")
    # НЕ закрывать пакет, проверим в следующем цикле
    continue
```

---

### Ошибка 2: HTTP 404 при скачивании

**Причина:** Файл результатов удален или недоступен

**Решение:**

```python
try:
    response = requests.get(google_batch.output_file_uri)
    response.raise_for_status()
except requests.HTTPError as e:
    if e.response.status_code == 404:
        logger.error(f"Output file not found for batch {batch['id']}")
        db.update_batch_status(batch["id"], "FAILED")
    raise
```

---

### Ошибка 3: Невалидный JSON

**Причина:** Поврежденный JSONL файл

**Решение:**

```python
try:
    results = [json.loads(line) for line in response.text.strip().split("\n") if line]
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in batch {batch['id']}: {e}")
    db.update_batch_status(batch["id"], "FAILED")
    continue
```

---

### Ошибка 4: Файл не сохраняется на диск

**Причина:** Нет прав на запись или полный диск

**Решение:**

```python
try:
    with open(local_path, "wb") as f:
        f.write(image_bytes)
except IOError as e:
    logger.error(f"Failed to save image {task_id}: {e}")
    db.update_task_failed(task_id, error=f"Disk error: {e}")
```

---

## Оптимизация: Использование target_path

**Проблема:** Сейчас все изображения сохраняются в `output/images/{task_id}.png`

**Решение:** Использовать `target_path` из задачи:

```python
def _save_image_to_target(task: dict, base64_data: str) -> str:
    """Сохранить изображение в target_path из задачи."""
    target_path = Path(task["target_path"])
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    image_bytes = base64.b64decode(base64_data)
    
    with open(target_path, "wb") as f:
        f.write(image_bytes)
    
    return str(target_path.absolute())
```

**Использование:**

```python
# Получить задачу из БД
task = db.get_task(task_id)

# Сохранить в нужное место
local_path = _save_image_to_target(task, base64_data)
```

---

## Тестирование

### Вариант 1: E2E тест (платный, ~$0.005)

**Полный цикл:**

1. Создать batch с 2 задачами
2. Отправить (Шаг 1)
3. Дождаться COMPLETED (Шаг 2)
4. Скачать результаты (Шаг 3)

**Скрипт:**

```python
# scripts/test_full_cycle.py

from database import DatabaseManager
from worker import WorkerManager
from uuid import uuid4
import time

db = DatabaseManager()
db.initialize()

# 1. Создать batch
batch_id = str(uuid4())
tasks = [
    {
        "task_id": str(uuid4()),
        "input_payload": {"prompt": "A red car"},
        "target_path": f"/tmp/car.png"
    },
    {
        "task_id": str(uuid4()),
        "input_payload": {"prompt": "A blue house"},
        "target_path": f"/tmp/house.png"
    }
]

db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks)

# 2. Запустить воркер
worker = WorkerManager(db, tick_interval=30)
worker.start()

# 3. Ждать завершения (max 5 минут)
timeout = 300
start = time.time()

while time.time() - start < timeout:
    batch = db.get_batch(batch_id)
    print(f"Status: {batch['status']}")
    
    if batch["status"] == "COMPLETED":
        print("✅ Batch completed!")
        break
    
    time.sleep(10)

worker.stop(timeout=5)

# 4. Проверить результаты
tasks_result = db.get_tasks_by_batch(batch_id)
for task in tasks_result:
    print(f"Task {task['id']}: {task['status']} → {task.get('local_path')}")
    
    if task["status"] == "COMPLETED":
        import os
        assert os.path.exists(task["local_path"]), "File not found!"
        print(f"✅ Image saved: {task['local_path']}")
```

**Стоимость:** ~$0.005 (2 изображения × $0.0025)

---

## Проверка готовности

### Критерии успеха

- ✅ Функция скачивает JSONL файл из `output_file_uri`
- ✅ Результаты корректно парсятся (JSON Lines)
- ✅ Изображения декодируются из base64
- ✅ Файлы сохраняются на диск
- ✅ Задачи переходят в COMPLETED/FAILED
- ✅ Пакет закрывается после обработки всех результатов

### Проверочный тест

```bash
# 1. Запустить полный E2E цикл
python scripts/test_full_cycle.py

# 2. Проверить БД
sqlite3 gemini_tasks.db "SELECT status, local_path FROM tasks WHERE batch_id='...'"

# Ожидаемый результат:
# COMPLETED|/tmp/car.png
# COMPLETED|/tmp/house.png

# 3. Проверить файлы
ls -lh /tmp/*.png
```

---

## Следующий шаг

После успешного получения результатов переходим к **Шагу 4: TTS Queue Integration** → интеграция реального TTS вместо моков.

**Файл:** `phase3_step4_tts_queue.md`

---

**Версия:** 1.0  
**Дата:** 27 ноября 2025 г.
