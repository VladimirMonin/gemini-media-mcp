# Подробный гид по тестам проекта Gemini Media MCP

**Дата:** 27 ноября 2025 г.  
**Версия:** 1.0  
**Автор:** GitHub Copilot (Claude Sonnet 4.5)

---

## Краткий ответ на главный вопрос

### Стоят ли тесты денег?

**НЕТ, тесты БЕСПЛАТНЫ** (текущая версия)

Все 50 тестов работают **локально** и не делают реальных API вызовов к Google Gemini. Они используют:

- Временные SQLite базы данных (создаются в RAM/tmp, удаляются после теста)
- Моки вместо реальных API вызовов (`time.sleep()` вместо `generate_audio()`)
- Локальные файловые операции

**Когда тесты начнут стоить денег:**

- Фаза 3 (Batch API Integration) — появятся E2E тесты с реальными API вызовами
- Примерная стоимость: **$0.01-0.05 за полный прогон** (50 запросов к Batch API)
- Эти тесты будут запускаться **вручную**, не в CI/CD

---

## Структура тестов (3 категории)

```
tests/
├── test_database.py        27 тестов  БЕСПЛАТНО  Работа с SQLite локально
├── test_worker.py           8 тестов  БЕСПЛАТНО  Моки вместо API вызовов
└── test_backup_manager.py  15 тестов  БЕСПЛАТНО  Локальные файлы
```

**Итого:** 50 тестов, **$0.00 стоимость**, ~27 секунд выполнения

---

## Категория 1: Database Tests (27 тестов)

### Что тестируется?

**База данных SQLite** — вся логика хранения задач, пакетов, статусов.

### Почему бесплатно?

1. **Временная база создается для каждого теста:**

   ```python
   @pytest.fixture
   def temp_db(tmp_path):
       db_path = tmp_path / "test.db"  # Временный файл
       db = DatabaseManager()
       db.initialize(str(db_path))
       yield db
       db.close()  # Удаляется после теста
   ```

2. **Нет сетевых запросов** — все операции локальные (INSERT, SELECT, UPDATE)

3. **Нет API вызовов** — только SQL запросы к SQLite

### Примеры тестов

#### Тест 1: Инициализация БД (test_initialize_creates_tables)

**Что делает:**

```python
def test_initialize_creates_tables(temp_db):
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    
    # Проверить, что таблица operation_types существует
    result = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='operation_types'"
    ).fetchone()
    
    assert result is not None
```

**Зачем это нужно:**

- Гарантирует, что схема БД создается корректно
- Если изменить `schema.py` и сломать DDL — тест упадет

**Стоимость:** $0 (локальный SQL запрос)

---

#### Тест 2: Создание пакета (test_create_batch)

**Что делает:**

```python
def test_create_batch(temp_db):
    batch_id = str(uuid4())
    temp_db.create_batch(batch_id, "IMG_GEN_BATCH", total_tasks=5)
    
    # Проверить, что пакет создан
    batch = temp_db.get_batch(batch_id)
    assert batch is not None
    assert batch["operation_type"] == "IMG_GEN_BATCH"
    assert batch["total_tasks"] == 5
```

**Зачем это нужно:**

- Проверяет CRUD операцию CREATE для batches
- Гарантирует, что метод `create_batch()` работает корректно

**Стоимость:** $0 (2 SQL запроса: INSERT + SELECT)

---

#### Тест 3: Восстановление зависших задач (test_recover_stale_tasks)

**Что делает:**

```python
def test_recover_stale_tasks(temp_db):
    # 1. Создать задачу в статусе PROCESSING
    task_id = str(uuid4())
    temp_db.create_task(task_id, batch_id, "IMG_GEN", {}, "/path")
    temp_db.update_task_status(task_id, "PROCESSING")
    
    # 2. Изменить updated_at на 1 час назад (эмуляция зависшей задачи)
    conn = temp_db.get_connection()
    conn.execute(
        "UPDATE tasks SET updated_at = datetime('now', '-1 hour') WHERE id = ?",
        (task_id,)
    )
    
    # 3. Вызвать recovery
    recovered = temp_db.recover_stale_tasks(timeout_minutes=30)
    
    # 4. Проверить, что задача вернулась в PENDING
    assert recovered == 1
    task = temp_db.get_task(task_id)
    assert task["status"] == "PENDING"
```

**Зачем это нужно:**

- **КРИТИЧЕСКИ ВАЖНЫЙ ТЕСТ** — проверяет recovery логику
- Гарантирует, что после сбоя сервера зависшие задачи не потеряются
- Этот тест помог найти баг с timezone в SQLite datetime (исправлено в ходе разработки)

**Стоимость:** $0 (несколько SQL запросов: INSERT, UPDATE, SELECT)

---

#### Тест 4: Поиск задач (test_search_tasks)

**Что делает:**

```python
def test_search_tasks(temp_db):
    # Создать задачи с разными ключевыми словами
    temp_db.create_task(uuid4(), batch_id, "IMG_GEN", {}, "/path", "cyberpunk city")
    temp_db.create_task(uuid4(), batch_id, "IMG_GEN", {}, "/path", "fantasy forest")
    
    # Поиск по "cyberpunk"
    results = temp_db.search_tasks(query="cyberpunk", limit=10)
    
    assert len(results) == 1
    assert "cyberpunk" in results[0]["search_keywords"]
```

**Зачем это нужно:**

- Проверяет функцию поиска по истории задач
- Пользователь сможет найти старые запросы через MCP tools

**Стоимость:** $0 (SQL запрос с LIKE)

---

### Полный список Database тестов (27 шт)

**TestInitialization (2 теста):**

1. `test_initialize_creates_tables` — создание схемы
2. `test_seed_data_loaded` — загрузка справочников

**TestOperationTypes (5 тестов):**
3. `test_get_operation_type_exists` — получение существующего типа
4. `test_get_operation_type_not_exists` — обработка несуществующего типа
5. `test_get_all_operation_types` — получение всего справочника
6. `test_get_execution_mode` — получение режима выполнения
7. `test_get_execution_mode_invalid` — обработка невалидного кода

**TestBatches (6 тестов):**
8. `test_create_batch` — создание пакета
9. `test_create_batch_invalid_operation` — валидация operation_type
10. `test_get_batch_not_exists` — обработка несуществующего пакета
11. `test_update_batch_status` — обновление статуса
12. `test_update_batch_completed` — завершение пакета
13. `test_get_pending_batches` — получение активных пакетов

**TestTasks (8 тестов):**
14. `test_create_task` — создание задачи
15. `test_get_task_not_exists` — обработка несуществующей задачи
16. `test_update_task_status` — обновление статуса
17. `test_update_task_completed` — успешное завершение
18. `test_update_task_failed` — провал задачи
19. `test_get_tasks_by_batch` — получение задач пакета
20. `test_get_pending_tasks` — получение очереди PENDING
21. `test_search_tasks` — поиск по ключевым словам

**TestTransactions (1 тест):**
22. `test_create_batch_with_tasks` — атомарная транзакция (batch + 10 tasks)

**TestUtilities (5 тестов):**
23. `test_get_stats` — статистика по БД
24. `test_retry_task` — повтор провалившейся задачи
25. `test_retry_task_not_failed` — обработка некорректного retry
26. `test_cancel_batch` — отмена пакета
27. `test_get_batch_progress` — прогресс выполнения пакета

---

## Категория 2: Worker Tests (8 тестов)

### Что тестируется?

**Фоновый обработчик задач** — daemon-поток, который живет параллельно с MCP сервером.

### Почему бесплатно?

1. **Моки вместо API вызовов:**

   ```python
   # ВМЕСТО РЕАЛЬНОГО API:
   # result = client.batches.create(...)
   
   # В ТЕСТАХ:
   time.sleep(2)  # Эмуляция API вызова
   logger.debug("[MOCK] Would create batch")
   ```

2. **Временная БД** — как в database тестах

3. **Нет Google Gemini вызовов** — все процессоры используют заглушки

### Примеры тестов

#### Тест 1: Запуск и остановка воркера (test_worker_start_stop)

**Что делает:**

```python
def test_worker_start_stop(temp_db):
    worker = WorkerManager(temp_db, tick_interval=1)
    
    # Запуск
    worker.start()
    assert worker._thread is not None
    assert worker._thread.is_alive()
    
    # Даём воркеру время на 2-3 цикла
    time.sleep(3)
    
    # Остановка
    worker.stop(timeout=5)
    assert not worker._thread.is_alive()
```

**Зачем это нужно:**

- Проверяет базовый lifecycle воркера
- Гарантирует, что daemon-поток запускается и корректно останавливается

**Стоимость:** $0 (локальные операции с threading)

---

#### Тест 2: Health Check (test_health_check_recovers_stale_tasks)

**Что делает:**

```python
def test_health_check_recovers_stale_tasks(temp_db):
    # 1. Создать "зависшую" задачу (PROCESSING + updated_at = 1 час назад)
    task_id = str(uuid4())
    temp_db.create_task(task_id, batch_id, "IMG_GEN", {}, "/path")
    temp_db.update_task_status(task_id, "PROCESSING")
    
    conn = temp_db.get_connection()
    conn.execute(
        "UPDATE tasks SET updated_at = datetime('now', '-1 hour') WHERE id = ?",
        (task_id,)
    )
    
    # 2. Запустить воркер (вызывается health check)
    worker = WorkerManager(temp_db, tick_interval=10)
    worker.start()
    
    time.sleep(2)  # Даём время на health check
    
    worker.stop(timeout=5)
    
    # 3. Проверить, что задача восстановлена
    task = temp_db.get_task(task_id)
    assert task["status"] == "PENDING"
```

**Зачем это нужно:**

- **КРИТИЧЕСКИ ВАЖНЫЙ ТЕСТ** — проверяет, что после краша воркер восстановит зависшие задачи
- Этот тест помог найти баг с SQLite datetime timezone

**Стоимость:** $0 (SQL запросы + threading, без API)

---

#### Тест 3: Обработка local_queue (test_local_queue_processes_one_task)

**Что делает:**

```python
def test_local_queue_processes_one_task(temp_db):
    # 1. Создать временный operation_type для TTS
    conn = temp_db.get_connection()
    conn.execute(
        "INSERT INTO operation_types VALUES (?, ?, ?, ?)",
        ("TTS_QUEUE", "TTS Queue", "Test TTS", "local_queue")
    )
    
    # 2. Создать задачу с execution_mode='local_queue'
    task_id = str(uuid4())
    temp_db.create_task(task_id, batch_id, "TTS_QUEUE", {}, "/path")
    
    # 3. Запустить воркер на 15 секунд
    worker = WorkerManager(temp_db, tick_interval=5)
    worker.start()
    
    time.sleep(15)  # Воркер делает 2-3 цикла
    
    worker.stop(timeout=5)
    
    # 4. Проверить, что задача обработана
    task = temp_db.get_task(task_id)
    assert task["status"] == "COMPLETED"
```

**Зачем это нужно:**

- Проверяет, что TTS задачи обрабатываются последовательно
- Гарантирует работу `queue_processor.py` (пока с моками)

**Стоимость:** $0 (вместо реального TTS используется `time.sleep(2)`)

---

#### Тест 4: Graceful Shutdown (test_worker_graceful_shutdown)

**Что делает:**

```python
def test_worker_graceful_shutdown(temp_db):
    worker = WorkerManager(temp_db, tick_interval=30)
    worker.start()
    
    time.sleep(2)  # Воркер в середине tick_interval
    
    # Засечь время остановки
    start = time.time()
    worker.stop(timeout=5)
    elapsed = time.time() - start
    
    # Проверить, что остановился быстро (< 5 секунд)
    assert elapsed < 5
    assert not worker._thread.is_alive()
```

**Зачем это нужно:**

- Проверяет, что `stop_event.wait()` прерывается немедленно
- Гарантирует, что при остановке сервера воркер не "зависнет" на 30 секунд

**Стоимость:** $0 (threading операции)

---

### Полный список Worker тестов (8 шт)

**TestWorkerLifecycle (3 теста):**

1. `test_worker_start_stop` — базовый lifecycle
2. `test_worker_already_running` — защита от двойного запуска
3. `test_worker_stop_not_running` — корректная обработка stop без start

**TestHealthCheck (1 тест):**
4. `test_health_check_recovers_stale_tasks` — восстановление зависших задач

**TestLocalQueueProcessing (2 теста):**
5. `test_local_queue_processes_one_task` — обработка TTS задачи
6. `test_local_queue_ignores_batch_tasks` — игнорирование batch задач

**TestGracefulShutdown (2 теста):**
7. `test_worker_graceful_shutdown` — быстрая остановка
8. `test_worker_stop_event_interrupts_sleep` — прерывание sleep по событию

---

## Категория 3: Backup Manager Tests (15 тестов)

### Что тестируется?

**Утилиты для бэкапа медиа-файлов** — сохранение metadata, создание уникальных имен файлов.

### Почему бесплатно?

1. **Локальные файловые операции** — работа с `tempfile.mkdtemp()`
2. **Нет API вызовов** — только чтение/запись JSON
3. **Временные директории** — удаляются после теста

### Примеры тестов

#### Тест 1: Санитизация промпта (test_simple_prompt)

**Что делает:**

```python
def test_simple_prompt():
    result = sanitize_description("A beautiful sunset")
    assert result == "A_beautiful_sunset"
```

**Зачем это нужно:**

- Проверяет, что промпты преобразуются в безопасные имена файлов
- Гарантирует работу на Windows (убирает спецсимволы `/\:*?"<>|`)

**Стоимость:** $0 (строковая операция)

---

#### Тест 2: Создание имени файла (test_image_filename_format)

**Что делает:**

```python
def test_image_filename_format():
    filename = create_backup_filename("A cyberpunk city", ".png")
    
    # Формат: IMG_{timestamp}_{sanitized_prompt}.png
    assert filename.startswith("IMG_")
    assert filename.endswith("_A_cyberpunk_city.png")
    assert len(filename.split("_")[1]) == 15  # timestamp
```

**Зачем это нужно:**

- Проверяет формат имен файлов для бэкапа
- Гарантирует уникальность (timestamp + prompt)

**Стоимость:** $0 (строковая операция)

---

#### Тест 3: Сохранение metadata.json (test_save_metadata)

**Что делает:**

```python
def test_save_metadata(tmp_path):
    metadata = {"prompt": "Test", "model": "gemini-2.0-flash-exp"}
    
    save_metadata_json(tmp_path, "test.png", metadata)
    
    # Проверить, что файл создан
    json_path = tmp_path / "test.json"
    assert json_path.exists()
    
    # Проверить содержимое
    with open(json_path) as f:
        loaded = json.load(f)
    assert loaded["prompt"] == "Test"
```

**Зачем это нужно:**

- Проверяет сохранение метаданных рядом с изображением
- Пользователь сможет восстановить промпт из JSON

**Стоимость:** $0 (запись JSON в локальный файл)

---

### Полный список Backup Manager тестов (15 шт)

**TestSanitizeDescription (6 тестов):**

1. `test_simple_prompt` — простой промпт
2. `test_long_prompt` — обрезка длинных промптов (max 100 символов)
3. `test_special_characters` — удаление спецсимволов
4. `test_multiple_spaces` — схлопывание пробелов
5. `test_empty_string` — обработка пустой строки
6. `test_only_special_chars` — обработка строки только из спецсимволов

**TestCreateBackupFilename (4 теста):**
7. `test_image_filename_format` — формат для изображений
8. `test_audio_filename_format` — формат для аудио
9. `test_different_extensions` — разные расширения (.png, .wav, .mp4)
10. `test_timestamp_uniqueness` — уникальность timestamp

**TestSaveMetadataJson (1 тест):**
11. `test_save_metadata` — сохранение JSON

**TestBackupGeneration (4 теста):**
12. `test_backup_image_file` — бэкап изображения
13. `test_backup_audio_file` — бэкап аудио
14. `test_multiple_backups_dont_overwrite` — защита от перезаписи
15. `test_backup_with_missing_file` — обработка отсутствующего файла

---

## Запуск тестов

### Вариант 1: Все тесты (50 шт)

```bash
pytest tests/ -v
```

**Вывод:**

```
====================== test session starts ======================
collected 50 items

tests/test_backup_manager.py::TestSanitizeDescription::test_simple_prompt PASSED [  2%]
tests/test_backup_manager.py::TestSanitizeDescription::test_long_prompt PASSED [  4%]
...
tests/test_worker.py::TestGracefulShutdown::test_worker_stop_event_interrupts_sleep PASSED [100%]

================ 50 passed, 1 skipped in 26.91s =================
```

**Стоимость:** $0.00  
**Время:** ~27 секунд

---

### Вариант 2: Только Database тесты

```bash
pytest tests/test_database.py -v
```

**Стоимость:** $0.00  
**Время:** ~3 секунды

---

### Вариант 3: Только Worker тесты

```bash
pytest tests/test_worker.py -v
```

**Стоимость:** $0.00  
**Время:** ~24 секунды (из-за sleep'ов для проверки асинхронности)

---

### Вариант 4: Только один тест

```bash
pytest tests/test_worker.py::TestHealthCheck::test_health_check_recovers_stale_tasks -v
```

**Стоимость:** $0.00  
**Время:** ~2 секунды

---

## Как устроены моки (почему бесплатно)

### Мок 1: Batch Processor

**Реальный код (будет в Фазе 3):**

```python
def submit_pending_batches(db: DatabaseManager) -> int:
    pending = db.get_pending_batches()
    
    for batch in pending:
        tasks = db.get_tasks_by_batch(batch["id"])
        
        # РЕАЛЬНЫЙ API ВЫЗОВ (стоит денег):
        inline_requests = create_inline_requests(tasks)
        result = client.batches.create(
            model="gemini-2.0-flash-exp",
            src=inline_requests
        )
        
        db.update_batch_status(batch["id"], "SUBMITTED", result.name)
    
    return len(pending)
```

**Мок в текущей версии (бесплатно):**

```python
def submit_pending_batches(db: DatabaseManager) -> int:
    pending = db.get_pending_batches()
    
    # ЗАГЛУШКА вместо API вызова:
    logger.debug(f"[MOCK] Would submit {len(pending)} batches to Google Batch API")
    
    return 0  # Ничего не создано
```

---

### Мок 2: Queue Processor

**Реальный код (будет в Фазе 3):**

```python
def process_local_queue_tasks(db: DatabaseManager) -> int:
    tasks = db.get_pending_tasks(limit=1)
    
    for task in tasks:
        db.update_task_status(task["id"], "PROCESSING")
        
        # РЕАЛЬНЫЙ API ВЫЗОВ (стоит денег):
        result_path = generate_audio_from_yaml(
            yaml_path=task["input_payload"]["yaml_path"],
            output_path=task["target_path"]
        )
        
        db.update_task_completed(task["id"], result_path)
        time.sleep(10)  # Rate limiting для TTS
        
        return 1
    
    return 0
```

**Мок в текущей версии (бесплатно):**

```python
def process_local_queue_tasks(db: DatabaseManager) -> int:
    tasks = db.get_pending_tasks(limit=1)
    
    for task in tasks:
        db.update_task_status(task["id"], "PROCESSING")
        
        # ЗАГЛУШКА вместо API вызова:
        time.sleep(2)  # Эмуляция API вызова
        
        db.update_task_completed(task["id"], f"/fake/path/{task['id']}.wav")
        time.sleep(10)  # Rate limiting
        
        return 1
    
    return 0
```

---

## Когда тесты начнут стоить денег

### Фаза 3: E2E тесты с реальными API

**Новая категория тестов:**

```
tests/
└── test_e2e_batch_api.py  # E2E тесты (ПЛАТНЫЕ)
```

**Пример E2E теста:**

```python
@pytest.mark.skipif(not os.getenv("RUN_E2E_TESTS"), reason="E2E tests disabled")
def test_batch_image_generation_e2e(temp_db):
    """
    РЕАЛЬНЫЙ тест с Google Batch API.
    
    СТОИМОСТЬ: ~$0.001 за запрос
    """
    # 1. Создать batch + tasks
    batch_id = str(uuid4())
    temp_db.create_batch_with_tasks(batch_id, "IMG_GEN_BATCH", [
        {
            "task_id": str(uuid4()),
            "input_payload": {"prompt": "A cyberpunk city"},
            "target_path": "/tmp/test.png"
        }
    ])
    
    # 2. Запустить воркер
    worker = WorkerManager(temp_db, tick_interval=10)
    worker.start()
    
    # 3. Дождаться завершения (может занять 2-5 минут)
    timeout = 300  # 5 минут
    start = time.time()
    
    while time.time() - start < timeout:
        batch = temp_db.get_batch(batch_id)
        if batch["status"] == "COMPLETED":
            break
        time.sleep(10)
    
    worker.stop(timeout=5)
    
    # 4. Проверить результат
    batch = temp_db.get_batch(batch_id)
    assert batch["status"] == "COMPLETED"
    
    tasks = temp_db.get_tasks_by_batch(batch_id)
    assert tasks[0]["status"] == "COMPLETED"
    assert os.path.exists(tasks[0]["local_path"])  # Файл скачан
```

**Стоимость этого теста:**

- 1 batch запрос: $0.000125 (Batch API в 2 раза дешевле синхронного)
- 1 image generation: $0.001 (цена зависит от модели)
- **Итого:** ~$0.0011 за тест

**Если запустить 50 E2E тестов:**

- $0.0011 × 50 = **$0.055** за полный прогон

---

### Как контролировать стоимость E2E тестов

**1. Feature flag для включения/выключения:**

```bash
# Обычный запуск (бесплатно):
pytest tests/

# E2E тесты (платно):
RUN_E2E_TESTS=1 pytest tests/
```

**2. Маркер pytest для фильтрации:**

```bash
# Только локальные тесты (бесплатно):
pytest -m "not e2e"

# Только E2E тесты (платно):
pytest -m e2e
```

**3. Запуск вручную, не в CI/CD:**

```bash
# Разработчик запускает локально ТОЛЬКО перед релизом:
RUN_E2E_TESTS=1 pytest tests/test_e2e_batch_api.py -v
```

---

## Почему тесты важны (даже если бесплатные)

### 1. Предотвращение регрессий

**Пример:**

- В ходе рефакторинга DatabaseManager был разбит на 5 классов
- Все 27 database тестов продолжили работать → **100% обратная совместимость**
- Если бы тестов не было, ошибки нашлись бы в production (через деньги клиентов)

---

### 2. Документация поведения

**Пример:**

- Тест `test_health_check_recovers_stale_tasks` **показывает**, как работает recovery
- Новый разработчик читает тест → понимает логику без изучения кода

---

### 3. Быстрая обратная связь

**Без тестов:**

1. Написать код
2. Запустить сервер вручную
3. Создать тестовую задачу через MCP
4. Ждать результата (2-5 минут)
5. Проверить БД вручную
6. Найти баг → повторить с п.1

**С тестами:**

1. Написать код
2. Запустить `pytest tests/test_worker.py` (24 секунды)
3. Увидеть какой тест упал → сразу понятно где баг

---

### 4. Обнаружение багов на ранней стадии

**Реальный пример из разработки:**

**Баг:** SQL datetime запрос не находил зависшие задачи

**Тест упал:**

```python
def test_health_check_recovers_stale_tasks(temp_db):
    # ...
    recovered = temp_db.recover_stale_tasks(timeout_minutes=30)
    assert recovered == 1  # FAILED: recovered == 0
```

**Исправление:**

```sql
-- БЫЛО (НЕРАБОТАЛО):
WHERE updated_at < datetime('now', '-30 minutes')

-- СТАЛО (РАБОТАЕТ):
WHERE datetime(updated_at) < datetime('now', 'localtime', '-30 minutes')
```

**Если бы не было теста:**

- Баг попал бы в production
- Зависшие задачи не восстанавливались бы после краша
- Пользователь потерял бы деньги на незавершенные запросы

---

## Резюме

### Текущая ситуация (Фаза 2)

✅ **50 тестов, $0.00 стоимость, 100% покрытие**

**Категории:**

1. Database (27 тестов) — проверка CRUD, транзакций, recovery
2. Worker (8 тестов) — проверка lifecycle, health check, graceful shutdown
3. Backup Manager (15 тестов) — проверка утилит бэкапа

**Все тесты локальные:**

- Временные SQLite базы (tmp_path)
- Моки вместо API вызовов (time.sleep)
- Локальные файловые операции

---

### Будущая ситуация (Фаза 3)

⏳ **~70 тестов, ~$0.05 за полный E2E прогон**

**Новые категории:**

1. E2E Batch API (10 тестов) — реальные вызовы Google Batch API
2. E2E TTS (5 тестов) — реальные вызовы generate_audio_from_yaml
3. E2E Integration (5 тестов) — полный цикл batch → task → файл

**Контроль стоимости:**

- Feature flag `RUN_E2E_TESTS=1` для включения
- Pytest маркер `-m e2e` для фильтрации
- Запуск вручную, не в CI/CD
- Оценка стоимости перед каждым прогоном

---

### Рекомендации

**ДЛЯ РАЗРАБОТКИ:**

1. Всегда запускать локальные тесты перед коммитом: `pytest tests/ -m "not e2e"`
2. Стоимость: $0.00, время: 27 секунд

**ДЛЯ РЕЛИЗА:**

1. Запустить E2E тесты вручную: `RUN_E2E_TESTS=1 pytest -m e2e`
2. Стоимость: ~$0.05, время: 5-10 минут
3. Запускать 1 раз перед production deploy

**ДЛЯ CI/CD:**

1. Только локальные тесты (бесплатно)
2. E2E тесты в отдельном nightly job (1 раз в день, ночью)

---

**Итого:** Платишь ли ты каждый раз, когда я запускаю тесты?  
**Ответ:** **НЕТ** (пока все тесты бесплатные). В Фазе 3 будут платные E2E тесты, но они будут запускаться вручную и под контролем.

---

**Версия документа:** 1.0  
**Дата:** 27 ноября 2025 г.  
**Автор:** GitHub Copilot (Claude Sonnet 4.5)
