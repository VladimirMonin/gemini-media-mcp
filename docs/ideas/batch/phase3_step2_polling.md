# Шаг 2: Batch Polling — Отслеживание статуса выполнения

**Время выполнения:** 1-2 часа  
**Сложность:** Низкая  
**Стоимость тестирования:** $0.00 (чтение статуса бесплатно)

---

## Цель шага

Научить систему отслеживать статус **SUBMITTED пакетов** в Google Batch API. После этого шага:

- Worker периодически проверяет статус активных пакетов
- Пакеты автоматически переходят `SUBMITTED` → `PROCESSING` → `COMPLETED`
- Статусы синхронизируются между Google и нашей БД
- Система знает, когда пакет готов к скачиванию результатов

---

## Что происходит сейчас (Фаза 2)

**Файл:** `worker/processors/batch_processor.py`  
**Функция:** `poll_active_batches()`

```python
def poll_active_batches(db: DatabaseManager) -> int:
    """ЗАГЛУШКА для Фазы 2."""
    logger.debug("[MOCK] Would poll active batches")
    return 0  # Ничего не проверено
```

**Проблема:**

- Пакеты остаются в статусе SUBMITTED навсегда
- Мы не знаем, когда задачи завершились
- Результаты не скачиваются (Шаг 3 ждет статуса COMPLETED)

---

## Как работает статусная модель Google Batch API

Google Batch API имеет **5 статусов**:

| Google статус | Описание | Наш статус БД |
|--------------|----------|---------------|
| `STATE_UNSPECIFIED` | Неизвестный статус (редко) | `PENDING` |
| `STATE_IN_PROGRESS` | Batch обрабатывается | `PROCESSING` |
| `STATE_COMPLETED` | Все задачи завершены | `COMPLETED` |
| `STATE_FAILED` | Критическая ошибка | `FAILED` |
| `STATE_CANCELLING` | Отменяется пользователем | `FAILED` |

**Важно:** Google не возвращает `STATE_SUBMITTED`. После `batches.create()` сразу `STATE_IN_PROGRESS`.

---

## Что нужно сделать

### 1. Получить список активных пакетов

**Активные пакеты** = статус `SUBMITTED` или `PROCESSING`

```python
batches = db.get_pending_batches()
# Возвращает пакеты со статусами: PENDING, SUBMITTED, PROCESSING
```

**Фильтрация:**

```python
active_batches = [
    b for b in batches 
    if b["google_batch_id"] is not None  # Только отправленные
]
```

---

### 2. Запросить статус у Google

**API вызов:**

```python
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)

google_batch = client.batches.get(batch["google_batch_id"])
```

**Что возвращается:**

```python
google_batch.name   # "batches/abc123xyz"
google_batch.state  # "STATE_IN_PROGRESS" или "STATE_COMPLETED"
```

---

### 3. Маппинг статусов

**Таблица соответствия:**

```python
STATUS_MAP = {
    "STATE_UNSPECIFIED": "PENDING",
    "STATE_IN_PROGRESS": "PROCESSING",
    "STATE_COMPLETED": "COMPLETED",
    "STATE_FAILED": "FAILED",
    "STATE_CANCELLING": "FAILED"
}

new_status = STATUS_MAP.get(google_batch.state, "PENDING")
```

---

### 4. Обновить статус в БД (если изменился)

**Проверка изменений:**

```python
if new_status != batch["status"]:
    db.update_batch_status(batch["id"], new_status)
    logger.info(f"Batch {batch['id']} status: {batch['status']} → {new_status}")
```

**Зачем проверять изменение:**

- Избегаем лишних UPDATE запросов к БД
- Логируем только реальные изменения статуса

---

## Полный алгоритм

```
1. Получить активные батчи из БД
   └─ db.get_pending_batches()
   └─ Фильтровать по google_batch_id IS NOT NULL

2. Для каждого батча:
   
   a) Запросить статус у Google
      └─ client.batches.get(google_batch_id)
   
   b) Преобразовать статус
      └─ STATUS_MAP[google_batch.state]
   
   c) Обновить БД (если статус изменился)
      └─ db.update_batch_status(batch_id, new_status)
   
   d) Логировать изменения
      └─ logger.info("Status changed")

3. Вернуть количество обновленных батчей
```

---

## Пример реализации (концепт)

**Файл:** `worker/processors/batch_processor.py`

```python
def poll_active_batches(db: DatabaseManager) -> int:
    """
    Проверка статуса активных пакетов в Google Batch API.
    
    Returns:
        Количество пакетов с обновленным статусом
    """
    # 1. Получить активные пакеты
    batches = db.get_pending_batches()
    active_batches = [
        b for b in batches 
        if b["google_batch_id"] is not None
    ]
    
    if not active_batches:
        return 0
    
    # 2. Инициализация клиента
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 3. Маппинг статусов
    STATUS_MAP = {
        "STATE_UNSPECIFIED": "PENDING",
        "STATE_IN_PROGRESS": "PROCESSING",
        "STATE_COMPLETED": "COMPLETED",
        "STATE_FAILED": "FAILED",
        "STATE_CANCELLING": "FAILED"
    }
    
    updated_count = 0
    
    # 4. Проверить каждый пакет
    for batch in active_batches:
        try:
            # Запросить статус у Google
            google_batch = client.batches.get(batch["google_batch_id"])
            
            # Преобразовать статус
            new_status = STATUS_MAP.get(google_batch.state, "PENDING")
            
            # Обновить БД (если изменился)
            if new_status != batch["status"]:
                db.update_batch_status(batch["id"], new_status)
                logger.info(
                    f"Batch {batch['id']} status updated: "
                    f"{batch['status']} → {new_status}"
                )
                updated_count += 1
        
        except Exception as e:
            logger.error(f"Failed to poll batch {batch['id']}: {e}")
            # НЕ обновляем статус при ошибке — повторим в следующем цикле
    
    return updated_count
```

---

## Оптимизация: Пакетная проверка

**Проблема:** Если 100 пакетов → 100 API вызовов → медленно

**Решение:** Google Batch API поддерживает `batches.list()`:

```python
# Вместо:
for batch in batches:
    google_batch = client.batches.get(batch["google_batch_id"])

# Можно:
all_google_batches = client.batches.list()

# Создать lookup таблицу
google_lookup = {
    gb.name: gb for gb in all_google_batches
}

# Быстрый поиск
for batch in batches:
    google_batch = google_lookup.get(batch["google_batch_id"])
    if google_batch:
        # обработать
```

**Когда использовать:**

- Если активных пакетов > 10
- Если нужна максимальная производительность

---

## Частота polling

**Текущая настройка:** Worker tick = 30 секунд

**Рекомендации:**

- **Для разработки:** 10-30 секунд (быстрая обратная связь)
- **Для production:** 60-300 секунд (снижение API запросов)

**Настройка в `server.py`:**

```python
worker = WorkerManager(db, tick_interval=60)  # 1 минута
```

**Почему не чаще:**

- Google Batch API обрабатывает задачи **минутами**, не секундами
- Частые запросы не ускорят обработку
- Rate limits могут блокировать при слишком частых вызовах

---

## Обработка ошибок

### Ошибка 1: "Batch not found"

**Причина:** `google_batch_id` невалиден или batch был удален

**Решение:**

```python
try:
    google_batch = client.batches.get(batch["google_batch_id"])
except NotFound:
    logger.warning(f"Batch {batch['google_batch_id']} not found in Google")
    db.update_batch_status(batch["id"], "FAILED")
```

---

### Ошибка 2: Rate limit exceeded

**Причина:** Слишком частые запросы к API

**Решение:**

```python
import time

try:
    google_batch = client.batches.get(batch["google_batch_id"])
except RateLimitError:
    logger.warning("Rate limit exceeded, waiting 60 seconds")
    time.sleep(60)
    # Повторить в следующем цикле
```

---

### Ошибка 3: API key expired

**Причина:** Невалидный или истекший ключ

**Решение:**

```python
try:
    google_batch = client.batches.get(batch["google_batch_id"])
except AuthenticationError:
    logger.error("Invalid API key, stopping polling")
    # НЕ обновлять статусы, проверим в следующем цикле
    return 0
```

---

## Тестирование

### Вариант 1: Локальное тестирование с моками

**Эмуляция статусных переходов:**

```python
# В начале файла
FAKE_BATCH_STATUSES = {}  # {google_batch_id: state}

def poll_active_batches(db: DatabaseManager) -> int:
    if not ENABLE_REAL_BATCH_API:
        # МОК: эмуляция статусных переходов
        batches = db.get_pending_batches()
        
        for batch in batches:
            if not batch["google_batch_id"]:
                continue
            
            # Эмуляция перехода SUBMITTED → PROCESSING → COMPLETED
            current = FAKE_BATCH_STATUSES.get(batch["google_batch_id"], "STATE_IN_PROGRESS")
            
            if current == "STATE_IN_PROGRESS":
                new_state = "STATE_COMPLETED"  # Быстрая эмуляция
            else:
                new_state = current
            
            FAKE_BATCH_STATUSES[batch["google_batch_id"]] = new_state
            
            new_status = STATUS_MAP[new_state]
            if new_status != batch["status"]:
                db.update_batch_status(batch["id"], new_status)
        
        return len(batches)
    
    # Реальная логика (код выше)
    ...
```

---

### Вариант 2: Интеграционный тест

**Сценарий:**

1. Создать batch через Submission (Шаг 1)
2. Подождать 30 секунд
3. Вызвать `poll_active_batches()`
4. Проверить, что статус обновился

**Скрипт:**

```python
# scripts/test_batch_polling.py

from database import DatabaseManager
from worker.processors.batch_processor import submit_pending_batches, poll_active_batches
import time

db = DatabaseManager()
db.initialize()

# 1. Создать и отправить batch (из Шага 1)
# ... код создания batch ...

submitted = submit_pending_batches(db)
print(f"Submitted: {submitted}")

# 2. Подождать
print("Waiting 30 seconds...")
time.sleep(30)

# 3. Проверить статус
updated = poll_active_batches(db)
print(f"Updated: {updated}")

# 4. Проверить результат
batch = db.get_batch(batch_id)
print(f"New status: {batch['status']}")
```

**Ожидаемый вывод:**

```
Submitted: 1
Waiting 30 seconds...
Updated: 1
New status: PROCESSING  (или COMPLETED, если быстро обработалось)
```

---

## Проверка готовности

### Критерии успеха

- ✅ Функция `poll_active_batches()` вызывает `client.batches.get()`
- ✅ Статусы корректно маппятся (Google → БД)
- ✅ БД обновляется только при изменении статуса
- ✅ Логи показывают переходы статусов
- ✅ При ошибке пакет не переходит в неправильный статус

### Проверочный тест

```bash
# 1. Создать и отправить batch (Шаг 1)
# 2. Запустить воркер на 2 минуты
python scripts/demo_worker.py

# 3. Проверить в БД
sqlite3 gemini_tasks.db "SELECT id, status FROM batches WHERE google_batch_id IS NOT NULL;"

# Ожидаемый результат:
# uuid|PROCESSING  (или COMPLETED)
```

---

## Следующий шаг

После успешного отслеживания статусов переходим к **Шагу 3: Batch Retrieval** → скачивание и обработка результатов.

**Файл:** `phase3_step3_retrieval.md`

---

**Версия:** 1.0  
**Дата:** 27 ноября 2025 г.
