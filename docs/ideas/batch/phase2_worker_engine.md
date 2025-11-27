# Фаза 2: Worker Engine — Фоновый обработчик задач

**Статус:** 🟡 В планировании  
**Дата начала:** 27 ноября 2025 г.  
**Предварительная оценка:** 2-3 дня  
**Зависимости:** ✅ Фаза 1 (Database Core) завершена

---

## Цель

Создать **автономный фоновый процесс**, который живёт параллельно с MCP-сервером и обрабатывает очередь задач из БД. Воркер должен:

1. **Не блокировать главный поток** — работает в отдельном daemon-потоке
2. **Поддерживать два режима** — `batch` (Google Batch API) и `local_queue` (последовательная обработка)
3. **Восстанавливаться после сбоев** — Health Check при старте находит зависшие задачи
4. **Graceful shutdown** — корректно завершаться при остановке сервера

---

## Архитектура

```
worker/
  __init__.py           ← Экспорт WorkerManager
  manager.py            ← Основной класс воркера
  processors/
    __init__.py
    batch_processor.py  ← Обработка batch-режима (Google Batch API)
    queue_processor.py  ← Обработка local_queue режима (TTS)
  
server.py               ← Интеграция: запуск/остановка воркера
```

**Зависимости:**

- `threading` (daemon-поток)
- `time` (sleep между циклами)
- `database.DatabaseManager` (взаимодействие с БД)
- `google.genai.Client` (для Batch API, будет добавлено в Фазе 3)

---

## Компоненты системы

### 1. WorkerManager — Главный оркестратор

**Роль:** Управляет жизненным циклом воркера (старт, остановка, главный цикл).

**Ключевые атрибуты:**

```python
class WorkerManager:
    _thread: threading.Thread          # daemon=True
    _stop_event: threading.Event       # для graceful shutdown
    _db: DatabaseManager               # ссылка на БД
    _tick_interval: int = 30           # секунд между циклами
    _health_check_on_start: bool = True
```

**Методы:**

- `start()` → запускает daemon-поток с `_worker_loop()`
- `stop()` → устанавливает `_stop_event`, ждёт завершения потока
- `_worker_loop()` → **бесконечный цикл** с 3 фазами обработки
- `_health_check()` → восстановление зависших задач при старте

---

### 2. Batch Processor — Обработка через Google Batch API

**Режим работы:** `execution_mode='batch'`  
**Применяется к:** IMG_GEN_BATCH, IMG_ANALYZE_BATCH, VIDEO_ANALYZE_BATCH, GIF_ANALYZE_BATCH

**Фазы обработки:**

#### Фаза 1: Submission (Отправка)

```
1. Получить pending задачи:
   tasks = db.get_pending_tasks(limit=100)
   
2. Группировать по batch_id:
   batches_map = group_by_batch(tasks)
   
3. Для каждого batch:
   - Сформировать inline_requests (список JSON с contents)
   - Вызвать client.batches.create(model, src=inline_requests)
   - Получить google_batch_id
   - Обновить статус: batch → SUBMITTED, tasks → SUBMITTED
```

**Структура inline_request:**

```json
{
  "custom_id": "task_uuid_here",
  "contents": {
    "parts": [{"text": "Generate image: cyberpunk city"}]
  },
  "generationConfig": {
    "response_modalities": ["IMAGE"],
    "response_mime_type": "image/png"
  }
}
```

#### Фаза 2: Polling (Мониторинг)

```
1. Получить активные пакеты:
   batches = db.get_pending_batches()  # SUBMITTED, PROCESSING
   
2. Для каждого batch с google_batch_id:
   - batch_status = client.batches.get(google_batch_id)
   - Проверить batch_status.state:
     * JOB_STATE_PENDING → ничего не делать
     * JOB_STATE_RUNNING → обновить статус на PROCESSING
     * JOB_STATE_SUCCEEDED → перейти к Retrieval
     * JOB_STATE_FAILED → пометить все задачи как FAILED
```

#### Фаза 3: Retrieval (Скачивание результатов)

```
1. Получить результаты:
   results = batch_status.results  # List[BatchResult]
   
2. Для каждого result:
   - Найти задачу по custom_id (это task_id из БД)
   - Если result.response.candidates[0].content.parts[0].inline_data:
     * Извлечь bytes изображения
     * Сохранить в target_path из task
     * db.update_task_completed(task_id, local_path)
   - Если result.error:
     * db.update_task_failed(task_id, error_message)
     
3. Проверить прогресс пакета:
   progress = db.get_batch_progress(batch_id)
   if progress['pending'] == 0 and progress['processing'] == 0:
       db.update_batch_completed(batch_id)
```

---

### 3. Queue Processor — Последовательная обработка

**Режим работы:** `execution_mode='local_queue'`  
**Применяется к:** TTS_GEN (Batch API не работает из-за бага Google)

**Особенности:**

- Задачи обрабатываются **по одной** (rate limiting)
- Нет группировки в пакеты Google
- Статус сразу PENDING → PROCESSING → COMPLETED

**Псевдокод:**

```python
def process_local_queue(db: DatabaseManager):
    tasks = db.get_pending_tasks(limit=1)  # Только 1 задача!
    
    if not tasks:
        return
    
    task = tasks[0]
    db.update_task_status(task['id'], 'PROCESSING')
    
    try:
        # Десериализовать параметры
        payload = task['input_payload']  # уже dict после get_task
        
        # Вызвать РЕАЛЬНЫЙ генератор (в Фазе 3)
        # result_path = generate_audio_from_yaml(**payload)
        
        # ЗАГЛУШКА для Фазы 2:
        time.sleep(2)  # имитация работы API
        result_path = task['target_path']
        
        db.update_task_completed(task['id'], result_path)
        
    except Exception as e:
        db.update_task_failed(task['id'], str(e))
```

**Rate Limiting:**

- Интервал между задачами: 6-20 секунд (соблюдение лимита 3-10 RPM для TTS)
- Реализация: `time.sleep(10)` после каждой обработанной задачи

---

## Главный цикл воркера (_worker_loop)

```python
def _worker_loop(self):
    """
    Бесконечный цикл, который просыпается каждые tick_interval секунд.
    
    Этапы обработки:
    1. Health Check (только при первом запуске)
    2. Batch Submission (отправка pending задач в Google)
    3. Batch Polling (проверка статусов активных пакетов)
    4. Batch Retrieval (скачивание готовых результатов)
    5. Local Queue Processing (TTS задачи)
    6. Sleep до следующего тика
    """
    
    # Health Check при старте
    if self._health_check_on_start:
        recovered = self._db.recover_stale_tasks(timeout_minutes=30)
        if recovered > 0:
            logger.warning(f"Health Check: recovered {recovered} stale tasks")
        self._health_check_on_start = False
    
    while not self._stop_event.is_set():
        try:
            # === BATCH MODE ===
            # 1. Submission Phase
            self._submit_pending_batches()
            
            # 2. Polling Phase
            self._poll_active_batches()
            
            # 3. Retrieval Phase
            self._retrieve_completed_batches()
            
            # === LOCAL QUEUE MODE ===
            # 4. Process TTS tasks sequentially
            self._process_local_queue()
            
            # 5. Sleep
            logger.debug(f"Worker cycle complete, sleeping {self._tick_interval}s")
            self._stop_event.wait(timeout=self._tick_interval)
            
        except Exception as e:
            logger.exception(f"Worker loop error: {e}")
            # Продолжить работу после ошибки (не падать)
            time.sleep(5)
```

**Почему `_stop_event.wait()` вместо `time.sleep()`?**

- Позволяет **немедленно** прервать цикл при вызове `stop()`
- `time.sleep(30)` заставил бы ждать до 30 секунд для завершения
- `wait(timeout=30)` прерывается сразу при `set()`

---

## Интеграция в server.py

**ДО (текущее состояние):**

```python
# server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gemini-media-analyzer")
# ... регистрация инструментов ...
mcp.run(transport="stdio")
```

**ПОСЛЕ (с воркером):**

```python
# server.py
from mcp.server.fastmcp import FastMCP
from database import DatabaseManager
from worker import WorkerManager

# Инициализация БД
logger.info("Initializing database...")
db = DatabaseManager()
db.initialize()
logger.info("Database ready")

# Инициализация воркера
logger.info("Starting background worker...")
worker = WorkerManager(db, tick_interval=30)
worker.start()
logger.info("Worker started")

# Регистрация MCP инструментов
mcp = FastMCP("gemini-media-analyzer")
# ... регистрация инструментов ...

# Запуск сервера с graceful shutdown
if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception(f"Critical error: {e}")
    finally:
        # Graceful shutdown
        logger.info("Stopping worker...")
        worker.stop()  # Ждёт завершения текущего цикла
        logger.info("Closing database...")
        db.close()
        logger.info("Shutdown complete")
```

---

## Реализация: Этап за этапом

### Этап 2.1: Создать WorkerManager (заглушки)

**Файл:** `worker/manager.py`

**Что реализовать:**

- Класс `WorkerManager` с `__init__(db, tick_interval)`
- Методы `start()`, `stop()`, `_worker_loop()`
- `_health_check()` — вызов `db.recover_stale_tasks()`
- **ЗАГЛУШКИ** для всех фаз (просто `logger.debug()` и `pass`)

**Критерий готовности:**

```python
# Тест: воркер запускается и останавливается без ошибок
db = DatabaseManager()
db.initialize()

worker = WorkerManager(db, tick_interval=5)
worker.start()
time.sleep(15)  # 3 цикла должны пройти
worker.stop()

# В логах должно быть:
# Worker started
# Worker cycle complete, sleeping 5s
# Worker cycle complete, sleeping 5s
# Worker cycle complete, sleeping 5s
# Worker stopped
```

---

### Этап 2.2: Реализовать Local Queue Processor

**Файл:** `worker/processors/queue_processor.py`

**Функция:**

```python
def process_local_queue_tasks(db: DatabaseManager) -> int:
    """
    Обработать 1 задачу из local_queue (TTS).
    
    Returns:
        1 если задача обработана, 0 если очередь пуста
    """
    tasks = db.get_pending_tasks(limit=1)
    
    if not tasks:
        return 0
    
    task = tasks[0]
    
    # Проверить execution_mode
    op_type = db.get_operation_type(task['operation_type'])
    if op_type['execution_mode'] != 'local_queue':
        return 0  # Это не наша задача
    
    # Обработать с ЗАГЛУШКОЙ
    db.update_task_status(task['id'], 'PROCESSING')
    
    try:
        # ЗАГЛУШКА: имитация генерации
        time.sleep(2)
        result_path = task['target_path']
        
        db.update_task_completed(task['id'], result_path)
        logger.info(f"Task {task['id'][:8]} completed (mock)")
        return 1
        
    except Exception as e:
        db.update_task_failed(task['id'], str(e))
        logger.error(f"Task {task['id'][:8]} failed: {e}")
        return 1
```

**Интеграция в `_worker_loop()`:**

```python
def _worker_loop(self):
    # ...
    
    # Local Queue Phase
    processed = process_local_queue_tasks(self._db)
    if processed:
        time.sleep(10)  # Rate limiting для TTS
```

---

### Этап 2.3: Создать Batch Processor (заглушки)

**Файл:** `worker/processors/batch_processor.py`

**Функции (все с заглушками):**

```python
def submit_pending_batches(db: DatabaseManager) -> int:
    """Фаза 1: Отправка PENDING задач в Google Batch API."""
    # ЗАГЛУШКА: просто вывести количество pending задач
    tasks = db.get_pending_tasks(limit=100)
    batch_tasks = [t for t in tasks if db.get_operation_type(t['operation_type'])['execution_mode'] == 'batch']
    
    if batch_tasks:
        logger.info(f"[MOCK] Would submit {len(batch_tasks)} batch tasks")
    
    return len(batch_tasks)

def poll_active_batches(db: DatabaseManager) -> int:
    """Фаза 2: Проверка статусов активных пакетов."""
    batches = db.get_pending_batches()
    
    if batches:
        logger.info(f"[MOCK] Would poll {len(batches)} active batches")
    
    return len(batches)

def retrieve_completed_batches(db: DatabaseManager) -> int:
    """Фаза 3: Скачивание готовых результатов."""
    # ЗАГЛУШКА: в реальности здесь будет поиск SUBMITTED/PROCESSING пакетов
    # и проверка их статуса через client.batches.get()
    logger.debug("[MOCK] No completed batches to retrieve yet")
    return 0
```

**Интеграция в `_worker_loop()`:**

```python
def _worker_loop(self):
    # ...
    
    # Batch Phases
    submit_pending_batches(self._db)
    poll_active_batches(self._db)
    retrieve_completed_batches(self._db)
    
    # ...
```

---

## Тестирование

### Pytest тесты (`tests/test_worker.py`)

**Что тестировать:**

1. **Инициализация и старт/стоп:**

   ```python
   def test_worker_start_stop(temp_db):
       worker = WorkerManager(temp_db, tick_interval=1)
       worker.start()
       time.sleep(3)  # 3 цикла
       worker.stop()
       # Проверить, что поток завершился
   ```

2. **Health Check:**

   ```python
   def test_health_check_recovers_stale_tasks(temp_db):
       # Создать задачу со статусом PROCESSING и старой updated_at
       # Запустить воркер
       # Проверить, что задача стала PENDING
   ```

3. **Local Queue обработка:**

   ```python
   def test_local_queue_processes_one_task(temp_db):
       # Создать TTS задачу
       # Запустить 1 цикл воркера
       # Проверить, что статус стал COMPLETED
   ```

4. **Graceful shutdown:**

   ```python
   def test_worker_graceful_shutdown(temp_db):
       worker = WorkerManager(temp_db, tick_interval=10)
       worker.start()
       time.sleep(0.5)  # Воркер в середине цикла
       worker.stop()  # Должен дождаться конца цикла
       # Проверить, что поток завершился корректно
   ```

---

### Интеграционный тест (`scripts/demo_worker.py`)

**Цель:** Визуально показать, как воркер разгребает очередь.

```python
"""
Демонстрация работы воркера с реальной БД.

Создаёт 5 тестовых задач и запускает воркер на 60 секунд.
Показывает прогресс в реальном времени.
"""

from database import DatabaseManager
from worker import WorkerManager
from uuid import uuid4
import time

def main():
    print("=" * 60)
    print("Demo: Worker Engine")
    print("=" * 60)
    
    # Инициализация
    db = DatabaseManager()
    db.initialize()
    
    # Создать тестовый batch с задачами
    batch_id = str(uuid4())
    
    print(f"\n[1] Creating test batch {batch_id[:8]}...")
    db.create_batch_with_tasks(
        batch_id=batch_id,
        operation_type='TTS_GEN',  # local_queue режим
        tasks=[
            {
                'task_id': str(uuid4()),
                'input_payload': {'script': f'Test audio {i}', 'voice': 'Kore'},
                'target_path': f'output/test_{i}.wav',
                'search_keywords': f'test audio {i}'
            }
            for i in range(5)
        ]
    )
    print(f"✅ Created 5 tasks")
    
    # Запустить воркер
    print(f"\n[2] Starting worker (tick_interval=10s)...")
    worker = WorkerManager(db, tick_interval=10)
    worker.start()
    print("✅ Worker started")
    
    # Мониторинг прогресса
    print(f"\n[3] Monitoring progress for 60 seconds...")
    print("-" * 60)
    
    for i in range(6):  # 60 секунд / 10 секунд = 6 итераций
        time.sleep(10)
        
        progress = db.get_batch_progress(batch_id)
        stats = db.get_stats()
        
        print(f"T+{(i+1)*10}s | Batch: {progress['completed']}/{progress['total']} completed | "
              f"DB: {stats['pending']} pending, {stats['processing']} processing")
    
    print("-" * 60)
    
    # Остановить воркер
    print(f"\n[4] Stopping worker...")
    worker.stop()
    print("✅ Worker stopped")
    
    # Финальная статистика
    print(f"\n[5] Final stats:")
    final_progress = db.get_batch_progress(batch_id)
    print(f"   Completed: {final_progress['completed']}")
    print(f"   Failed: {final_progress['failed']}")
    print(f"   Pending: {final_progress['pending']}")
    
    db.close()
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

**Ожидаемый вывод:**

```
============================================================
Demo: Worker Engine
============================================================

[1] Creating test batch 7a3f2b1c...
✅ Created 5 tasks

[2] Starting worker (tick_interval=10s)...
✅ Worker started

[3] Monitoring progress for 60 seconds...
------------------------------------------------------------
T+10s | Batch: 1/5 completed | DB: 4 pending, 0 processing
T+20s | Batch: 2/5 completed | DB: 3 pending, 0 processing
T+30s | Batch: 3/5 completed | DB: 2 pending, 0 processing
T+40s | Batch: 4/5 completed | DB: 1 pending, 0 processing
T+50s | Batch: 5/5 completed | DB: 0 pending, 0 processing
T+60s | Batch: 5/5 completed | DB: 0 pending, 0 processing
------------------------------------------------------------

[4] Stopping worker...
✅ Worker stopped

[5] Final stats:
   Completed: 5
   Failed: 0
   Pending: 0

============================================================
Demo complete!
============================================================
```

---

## Критерии готовности Фазы 2

- ✅ `WorkerManager` запускается в daemon-потоке
- ✅ Health Check восстанавливает зависшие задачи при старте
- ✅ Local Queue Processor обрабатывает TTS задачи по одной
- ✅ Batch Processor имеет заглушки для 3 фаз (submission, polling, retrieval)
- ✅ Graceful shutdown корректно завершает воркер при остановке сервера
- ✅ Pytest тесты проходят (минимум 4 теста)
- ✅ Интеграционный demo-скрипт показывает работу воркера визуально
- ✅ Интегрировано в `server.py` (инициализация + shutdown)

---

## Известные ограничения (будут решены в Фазе 3)

1. **Batch Processor — заглушки:** Реальные вызовы Google Batch API будут добавлены в Фазе 3
2. **Local Queue — заглушки:** Реальные вызовы `generate_audio_from_yaml()` будут в Фазе 3
3. **Уведомления:** Toast-уведомления о завершении batch отложены на Фазу 4
4. **Метрики:** Подсчёт стоимости операций и статистика будут в Фазе 5

---

## Следующий шаг

**Фаза 3:** Batch API Integration — подключение реальных вызовов Google Batch API вместо заглушек.
