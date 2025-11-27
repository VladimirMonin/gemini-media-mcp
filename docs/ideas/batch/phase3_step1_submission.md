# Шаг 1: Batch Submission — Отправка пакетов в Google Batch API

**Время выполнения:** 2-3 часа  
**Сложность:** Средняя  
**Стоимость тестирования:** $0.00 (можно использовать моки)

---

## Цель шага

Научить систему отправлять **pending задачи** из БД в Google Batch API. После этого шага:

- Пакеты переходят из статуса `PENDING` в `SUBMITTED`
- Задачи переходят из статуса `PENDING` в `SUBMITTED`
- В БД сохраняется `google_batch_id` для дальнейшего tracking
- Worker автоматически обрабатывает новые пакеты каждые 30 секунд

---

## Что происходит сейчас (Фаза 2)

**Файл:** `worker/processors/batch_processor.py`  
**Функция:** `submit_pending_batches()`

```python
def submit_pending_batches(db: DatabaseManager) -> int:
    """ЗАГЛУШКА для Фазы 2."""
    pending = db.get_pending_batches()
    logger.debug(f"[MOCK] Would submit {len(pending)} batches to Google Batch API")
    return 0  # Ничего не отправлено
```

**Проблема:**

- Задачи остаются в статусе PENDING навсегда
- `google_batch_id` остается NULL
- Никакие изображения не генерируются

---

## Что нужно сделать

### 1. Понять структуру Batch API запроса

Google Batch API принимает массив `inline_requests`:

```json
[
  {
    "custom_id": "task_uuid_1",
    "contents": {
      "parts": [
        {"text": "Generate image: A cyberpunk city"}
      ]
    }
  },
  {
    "custom_id": "task_uuid_2",
    "contents": {
      "parts": [
        {"text": "Generate image: A fantasy forest"}
      ]
    }
  }
]
```

**Ключевые поля:**

- `custom_id` — UUID задачи из БД (для сопоставления результатов)
- `contents.parts[0].text` — промпт из `input_payload`

---

### 2. Извлечь промпт из input_payload

**В БД хранится:**

```python
task["input_payload"] = {
    "prompt": "A cyberpunk city",
    "aspect_ratio": "16:9",
    "resolution": "1K"
}
```

**Нужно получить:**

```python
prompt = task["input_payload"]["prompt"]
# "A cyberpunk city"
```

---

### 3. Сформировать inline_requests

**Псевдокод:**

```python
tasks = db.get_tasks_by_batch(batch["id"])
inline_requests = []

for task in tasks:
    inline_requests.append({
        "custom_id": task["id"],
        "contents": {
            "parts": [
                {"text": task["input_payload"]["prompt"]}
            ]
        }
    })
```

---

### 4. Вызвать Batch API

**Инициализация клиента:**

```python
from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
```

**Создание batch:**

```python
result = client.batches.create(
    model="gemini-2.0-flash-exp",  # Модель для генерации изображений
    src=inline_requests
)
```

**Что возвращается:**

```python
result.name  # "batches/abc123xyz" — это google_batch_id
result.state # "STATE_IN_PROGRESS" — начальный статус
```

---

### 5. Обновить статусы в БД

**После успешной отправки:**

```python
# 1. Обновить batch
db.update_batch_status(
    batch["id"], 
    status="SUBMITTED",
    google_batch_id=result.name
)

# 2. Обновить все задачи пакета
for task in tasks:
    db.update_task_status(task["id"], "SUBMITTED")
```

---

### 6. Обработка ошибок

**Возможные ошибки:**

1. **API ключ невалиден** → логировать и пропустить batch
2. **Rate limit превышен** → подождать и повторить
3. **Невалидный промпт** → пометить batch как FAILED

**Рекомендуемая обработка:**

```python
try:
    result = client.batches.create(...)
    # успех
except Exception as e:
    logger.error(f"Failed to submit batch {batch['id']}: {e}")
    db.update_batch_status(batch["id"], "FAILED")
    # НЕ обновлять задачи — они останутся PENDING для retry
    continue
```

---

## Полный алгоритм

```
1. Получить pending батчи из БД
   └─ db.get_pending_batches()
   
2. Для каждого батча:
   
   a) Получить задачи батча
      └─ db.get_tasks_by_batch(batch_id)
   
   b) Сформировать inline_requests
      └─ Извлечь промпт из каждой задачи
      └─ Добавить custom_id (UUID задачи)
   
   c) Отправить в Batch API
      └─ client.batches.create(model, src=inline_requests)
   
   d) Обновить статусы
      └─ batch → SUBMITTED
      └─ tasks → SUBMITTED
      └─ Сохранить google_batch_id
   
   e) Обработать ошибки
      └─ При ошибке → batch FAILED
      └─ Задачи остаются PENDING для retry

3. Вернуть количество отправленных батчей
```

---

## Пример реализации (концепт)

**Файл:** `worker/processors/batch_processor.py`

```python
def submit_pending_batches(db: DatabaseManager) -> int:
    """
    Отправка pending пакетов в Google Batch API.
    
    Returns:
        Количество успешно отправленных пакетов
    """
    pending = db.get_pending_batches()
    
    if not pending:
        return 0
    
    # Инициализация клиента
    client = genai.Client(api_key=GEMINI_API_KEY)
    submitted_count = 0
    
    for batch in pending:
        try:
            # 1. Получить задачи пакета
            tasks = db.get_tasks_by_batch(batch["id"])
            
            # 2. Сформировать inline_requests
            inline_requests = []
            for task in tasks:
                inline_requests.append({
                    "custom_id": task["id"],
                    "contents": {
                        "parts": [
                            {"text": task["input_payload"]["prompt"]}
                        ]
                    }
                })
            
            # 3. Отправить в Batch API
            result = client.batches.create(
                model="gemini-2.0-flash-exp",
                src=inline_requests
            )
            
            # 4. Обновить статусы
            db.update_batch_status(
                batch["id"],
                status="SUBMITTED",
                google_batch_id=result.name
            )
            
            for task in tasks:
                db.update_task_status(task["id"], "SUBMITTED")
            
            logger.info(f"Batch {batch['id']} submitted: {result.name}")
            submitted_count += 1
            
        except Exception as e:
            logger.error(f"Failed to submit batch {batch['id']}: {e}")
            db.update_batch_status(batch["id"], "FAILED")
    
    return submitted_count
```

---

## Тестирование

### Вариант 1: Локальное тестирование с моками

**Не вызывать реальный API**, использовать заглушку:

```python
# В начале файла
ENABLE_REAL_BATCH_API = os.getenv("ENABLE_BATCH_API", "false").lower() == "true"

def submit_pending_batches(db: DatabaseManager) -> int:
    if not ENABLE_REAL_BATCH_API:
        # МОК для локального тестирования
        pending = db.get_pending_batches()
        for batch in pending:
            fake_google_id = f"batches/mock_{batch['id'][:8]}"
            db.update_batch_status(batch["id"], "SUBMITTED", fake_google_id)
            
            tasks = db.get_tasks_by_batch(batch["id"])
            for task in tasks:
                db.update_task_status(task["id"], "SUBMITTED")
        
        return len(pending)
    
    # Реальная логика (код выше)
    ...
```

**Запуск:**

```bash
# Локально (бесплатно)
pytest tests/test_worker.py -v

# С реальным API (платно)
ENABLE_BATCH_API=true pytest tests/test_worker.py -v
```

---

### Вариант 2: Интеграционный тест с реальным API

**Создать тестовый batch вручную:**

```python
# scripts/test_batch_submission.py

from database import DatabaseManager
from worker.processors.batch_processor import submit_pending_batches
from uuid import uuid4

db = DatabaseManager()
db.initialize()

# Создать тестовый batch
batch_id = str(uuid4())
tasks = [
    {
        "task_id": str(uuid4()),
        "input_payload": {"prompt": "Test image 1"},
        "target_path": "/tmp/test1.png"
    },
    {
        "task_id": str(uuid4()),
        "input_payload": {"prompt": "Test image 2"},
        "target_path": "/tmp/test2.png"
    }
]

db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", tasks)

# Отправить
submitted = submit_pending_batches(db)
print(f"Submitted: {submitted}")

# Проверить статус
batch = db.get_batch(batch_id)
print(f"Status: {batch['status']}")
print(f"Google ID: {batch['google_batch_id']}")
```

**Запуск:**

```bash
python scripts/test_batch_submission.py
```

**Ожидаемый вывод:**

```
Submitted: 1
Status: SUBMITTED
Google ID: batches/abc123xyz
```

---

## Частые ошибки

### Ошибка 1: "API key not found"

**Причина:** Не загружен `.env` файл

**Решение:**

```python
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")
```

---

### Ошибка 2: "Model not found for batches"

**Причина:** Неправильное имя модели

**Решение:**
Использовать только модели, поддерживающие Batch API:

- ✅ `gemini-2.0-flash-exp` (изображения)
- ✅ `gemini-2.5-flash` (текст)
- ❌ `gemini-2.5-flash-preview-tts` (НЕ поддерживает Batch API)

---

### Ошибка 3: Tasks остаются PENDING

**Причина:** Забыли обновить статусы задач

**Решение:**

```python
# ОБЯЗАТЕЛЬНО после успешной отправки
for task in tasks:
    db.update_task_status(task["id"], "SUBMITTED")
```

---

## Проверка готовности

### Критерии успеха

- ✅ Функция `submit_pending_batches()` вызывает `client.batches.create()`
- ✅ Batch переходит в статус `SUBMITTED`
- ✅ `google_batch_id` сохраняется в БД
- ✅ Все задачи пакета переходят в `SUBMITTED`
- ✅ При ошибке batch переходит в `FAILED`
- ✅ Логи показывают результаты отправки

### Проверочный тест

```bash
# 1. Создать тестовый batch через БД
# 2. Запустить воркер
python scripts/demo_worker.py

# 3. Проверить в БД
sqlite3 gemini_tasks.db "SELECT status, google_batch_id FROM batches;"

# Ожидаемый результат:
# SUBMITTED|batches/abc123xyz
```

---

## Следующий шаг

После успешной отправки пакетов переходим к **Шагу 2: Batch Polling** → отслеживание статуса выполнения.

**Файл:** `phase3_step2_polling.md`

---

**Версия:** 1.0  
**Дата:** 27 ноября 2025 г.
