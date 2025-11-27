# Фаза 1: Database Core — Реализация персистентного слоя

**Статус:** 🔴 В разработке  
**Дата начала:** 27 ноября 2025 г.  
**Предварительная оценка:** 1-2 дня

---

## Цель

Создать надёжный SQLite-слой для хранения задач, пакетов и операций с поддержкой:

- ACID-транзакций
- Thread-safety для фонового воркера
- Автоматической инициализации схемы
- Recovery зависших задач после сбоев

---

## Архитектура

```
database/
  __init__.py           ← Экспорт DatabaseManager
  manager.py            ← DatabaseManager (Singleton, thread-safe)
  schema.py             ← DDL запросы (CREATE TABLE, CREATE INDEX)
  queries.py            ← SQL запросы с плейсхолдерами
  seed_data.py          ← Seed данные для operation_types
  
gemini_tasks.db         ← SQLite файл (корень проекта)
```

**Зависимости:**

- `sqlite3` (встроенный)
- `threading.Lock` (для thread-safety)
- `json` (сериализация input_payload)

**Модульная структура:**

1. `schema.py` — только DDL (CREATE TABLE, CREATE INDEX, DROP)
2. `queries.py` — только SQL запросы с `?` плейсхолдерами
3. `seed_data.py` — только данные для справочников
4. `manager.py` — бизнес-логика + координация
5. `__init__.py` — публичный API (`from .manager import DatabaseManager`)

---

## Схема БД

### Таблица: `operation_types` (справочник)

```sql
CREATE TABLE IF NOT EXISTS operation_types (
    operation_type TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    execution_mode TEXT NOT NULL CHECK(execution_mode IN ('sync', 'batch', 'local_queue')),
    default_priority INTEGER DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Seed данные (на основе валидации 27.11.2025):**

```sql
INSERT OR IGNORE INTO operation_types (operation_type, display_name, execution_mode, description) VALUES
-- Синхронные операции (текущее поведение)
('IMG_GEN', 'Image Generation', 'sync', 'Текущая генерация изображений (полная цена)'),
('TTS_GEN', 'Audio Generation (TTS)', 'sync', 'Текущая генерация аудио (полная цена)'),
('IMG_ANALYZE', 'Image Analysis', 'sync', 'Текущий анализ изображений'),
('AUDIO_ANALYZE', 'Audio Analysis', 'sync', 'Текущий анализ аудио'),
('VIDEO_ANALYZE', 'Video Analysis', 'sync', 'Текущий анализ видео'),
('GIF_ANALYZE', 'GIF Analysis', 'sync', 'Текущий анализ GIF'),

-- Batch операции (50% скидка через Google Batch API)
('IMG_GEN_BATCH', 'Image Generation (Batch)', 'batch', 'Генерация изображений через Batch API (50% скидка)'),
('IMG_ANALYZE_BATCH', 'Image Analysis (Batch)', 'batch', 'Анализ изображений через Batch API'),
('VIDEO_ANALYZE_BATCH', 'Video Analysis (Batch)', 'batch', 'Анализ видео через Batch API'),
('GIF_ANALYZE_BATCH', 'GIF Analysis (Batch)', 'batch', 'Анализ GIF через Batch API');
```

**Примечание:** TTS очередь (`local_queue`) откладывается — нет экономии без Batch API.

---

### Таблица: `batches` (пакеты задач)

```sql
CREATE TABLE IF NOT EXISTS batches (
    id TEXT PRIMARY KEY,                          -- UUID (генерируется клиентом)
    google_batch_id TEXT,                         -- ID от Google Cloud (для batch mode)
    operation_type TEXT NOT NULL,                 -- FK -> operation_types.operation_type
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'SUBMITTED', 'PROCESSING', 'COMPLETED', 'FAILED')),
    total_tasks INTEGER DEFAULT 0,
    FOREIGN KEY (operation_type) REFERENCES operation_types(operation_type)
);

CREATE INDEX IF NOT EXISTS idx_batches_status ON batches(status);
CREATE INDEX IF NOT EXISTS idx_batches_google_id ON batches(google_batch_id);
```

**Статусы:**

- `PENDING` — создан, ждёт отправки в Batch API
- `SUBMITTED` — отправлен в Google Cloud
- `PROCESSING` — обрабатывается
- `COMPLETED` — все задачи завершены
- `FAILED` — ошибка на уровне пакета

---

### Таблица: `tasks` (единичные задачи)

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,                          -- UUID
    batch_id TEXT NOT NULL,                       -- FK -> batches.id
    operation_type TEXT NOT NULL,                 -- FK -> operation_types.operation_type
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'SUBMITTED', 'PROCESSING', 'COMPLETED', 'FAILED', 'DELIVERY_FAILED')),
    
    -- Критичные поля для retry/поиска
    input_payload TEXT NOT NULL,                  -- JSON: {"prompt": "...", "model": "...", ...}
    search_keywords TEXT,                         -- Денормализация для FTS
    
    -- Пути к файлам
    target_path TEXT NOT NULL,                    -- Куда пользователь хочет сохранить
    local_path TEXT,                              -- Где реально сохранено
    
    -- Ошибки
    error_details TEXT,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    FOREIGN KEY (batch_id) REFERENCES batches(id),
    FOREIGN KEY (operation_type) REFERENCES operation_types(operation_type)
);

CREATE INDEX IF NOT EXISTS idx_tasks_batch ON tasks(batch_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_operation ON tasks(operation_type);
CREATE INDEX IF NOT EXISTS idx_tasks_search ON tasks(search_keywords);
```

**Статусы:**

- `PENDING` — ждёт отправки
- `SUBMITTED` — в Google Batch
- `PROCESSING` — обрабатывается
- `COMPLETED` — успешно завершена
- `FAILED` — ошибка генерации
- `DELIVERY_FAILED` — файл есть, но не удалось сохранить в target_path (→ lost_and_found)

---

## API DatabaseManager

### Singleton Pattern + Thread-Safety

```python
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

---

### 1. Инициализация

```python
def initialize(db_path: str = "gemini_tasks.db") -> None:
    """
    Создаёт БД, таблицы и заполняет справочники.
    Вызывается один раз при старте server.py.
    
    Raises:
        RuntimeError: Если не удалось создать схему
    """
```

**Действия:**

1. Создать соединение с `check_same_thread=False`
2. `CREATE TABLE IF NOT EXISTS` для всех трёх таблиц
3. `INSERT OR IGNORE` seed данные в `operation_types`
4. Логировать результат

---

### 2. Operation Types (справочник)

```python
def get_operation_type(code: str) -> dict | None:
    """Получить operation_type по коду."""

def get_all_operation_types() -> list[dict]:
    """Весь справочник operation_types."""

def get_execution_mode(code: str) -> str:
    """
    Получить execution_mode для операции.
    
    Returns:
        'sync' | 'batch' | 'local_queue'
        
    Raises:
        ValueError: Если operation_type не найден
    """
```

---

### 3. Batches (пакеты)

```python
def create_batch(
    batch_id: str,
    operation_type: str,
    total_tasks: int
) -> None:
    """
    Создать новый пакет.
    
    Args:
        batch_id: UUID (генерируется вызывающим кодом)
        operation_type: Код операции из справочника
        total_tasks: Количество задач в пакете
        
    Raises:
        ValueError: Если operation_type не существует
    """

def get_batch(batch_id: str) -> dict | None:
    """Получить пакет по ID."""

def update_batch_status(
    batch_id: str,
    status: str,
    google_batch_id: str = None
) -> None:
    """
    Обновить статус пакета.
    
    Args:
        batch_id: ID пакета
        status: Новый статус
        google_batch_id: ID от Google (опционально)
    """

def update_batch_completed(batch_id: str) -> None:
    """
    Завершить пакет (completed_at = NOW(), status = COMPLETED).
    """

def get_pending_batches() -> list[dict]:
    """
    Получить активные пакеты для воркера.
    
    Returns:
        Пакеты со статусом PENDING, SUBMITTED, PROCESSING
    """

def get_batch_progress(batch_id: str) -> dict:
    """
    Прогресс выполнения пакета.
    
    Returns:
        {
            'total': int,
            'completed': int,
            'failed': int,
            'pending': int,
            'processing': int
        }
    """
```

---

### 4. Tasks (задачи)

#### CREATE

```python
def create_task(
    task_id: str,
    batch_id: str,
    operation_type: str,
    input_payload: dict,
    target_path: str,
    search_keywords: str = None
) -> None:
    """
    Создать задачу.
    
    Args:
        task_id: UUID
        batch_id: Родительский пакет
        operation_type: Тип операции
        input_payload: Параметры для retry (сериализуется в JSON)
        target_path: Куда сохранить результат
        search_keywords: Ключевые слова для поиска (опционально)
        
    Example:
        create_task(
            task_id=str(uuid.uuid4()),
            batch_id=batch_id,
            operation_type='IMG_GEN_BATCH',
            input_payload={
                'prompt': 'A cyberpunk city at night',
                'model': 'gemini-2.5-flash-image',
                'aspect_ratio': '16:9',
                'resolution': '1K'
            },
            target_path='/home/user/output/city.png',
            search_keywords='cyberpunk city night'
        )
    """
```

#### READ

```python
def get_task(task_id: str) -> dict | None:
    """Получить задачу по ID."""

def get_tasks_by_batch(batch_id: str) -> list[dict]:
    """Все задачи пакета."""

def get_pending_tasks(limit: int = 100) -> list[dict]:
    """
    Задачи в статусе PENDING (для воркера).
    
    Args:
        limit: Максимум задач за раз
        
    Returns:
        Список задач с полями из БД (+ десериализованный input_payload)
    """

def get_processing_tasks() -> list[dict]:
    """
    Задачи в статусе PROCESSING (для recovery после сбоя).
    """
```

#### UPDATE

```python
def update_task_status(
    task_id: str,
    status: str,
    error_details: str = None
) -> None:
    """
    Обновить статус задачи.
    
    Args:
        task_id: ID задачи
        status: Новый статус
        error_details: Текст ошибки (для FAILED/DELIVERY_FAILED)
    """

def update_task_completed(
    task_id: str,
    local_path: str
) -> None:
    """
    Завершить задачу успешно.
    
    Updates:
        - status = 'COMPLETED'
        - local_path = <путь>
        - completed_at = NOW()
    """

def update_task_failed(
    task_id: str,
    error: str
) -> None:
    """
    Пометить задачу как провалившуюся.
    
    Updates:
        - status = 'FAILED'
        - error_details = <ошибка>
        - completed_at = NOW()
    """
```

#### SEARCH

```python
def search_tasks(
    query: str,
    operation_type: str = None,
    limit: int = 10
) -> list[dict]:
    """
    Поиск по истории задач.
    
    Args:
        query: Строка поиска (ищет в search_keywords и input_payload)
        operation_type: Фильтр по типу операции (опционально)
        limit: Максимум результатов
        
    Returns:
        Список задач с релевантными полями
        
    Example:
        # "Найди картинку с киберпанк-городом"
        tasks = search_tasks(query='cyberpunk city', operation_type='IMG_GEN')
    """
```

---

### 5. Транзакции

```python
def create_batch_with_tasks(
    batch_id: str,
    operation_type: str,
    tasks: list[dict]
) -> None:
    """
    Атомарно создать пакет + задачи.
    
    Args:
        batch_id: UUID пакета
        operation_type: Тип операции
        tasks: Список словарей с ключами:
               - task_id (str)
               - input_payload (dict)
               - target_path (str)
               - search_keywords (str, optional)
               
    Example:
        create_batch_with_tasks(
            batch_id=str(uuid.uuid4()),
            operation_type='IMG_GEN_BATCH',
            tasks=[
                {
                    'task_id': str(uuid.uuid4()),
                    'input_payload': {'prompt': 'Cat in space', 'model': '...'},
                    'target_path': '/out/cat.png',
                    'search_keywords': 'cat space'
                },
                # ... ещё задачи
            ]
        )
        
    Raises:
        ValueError: Если operation_type не существует
        RuntimeError: Если транзакция не удалась
    """
```

---

### 6. Утилиты

```python
def get_stats() -> dict:
    """
    Статистика по БД.
    
    Returns:
        {
            'total_tasks': int,
            'pending': int,
            'processing': int,
            'completed': int,
            'failed': int,
            'batches_active': int,
            'batches_completed': int
        }
    """

def recover_stale_tasks(timeout_minutes: int = 30) -> int:
    """
    Recovery зависших задач.
    
    Переводит задачи со статусом PROCESSING, которые не обновлялись
    более timeout_minutes минут, обратно в PENDING.
    
    Args:
        timeout_minutes: Таймаут для определения "зависшей" задачи
        
    Returns:
        Количество восстановленных задач
        
    Note:
        Вызывается при старте воркера (Health Check)
    """

def cleanup_old_tasks(days: int = 30) -> int:
    """
    Удаление старых завершённых задач.
    
    Args:
        days: Возраст задач для удаления
        
    Returns:
        Количество удалённых записей
    """

def retry_task(task_id: str) -> None:
    """
    Перезапустить задачу.
    
    Переводит задачу из статуса FAILED обратно в PENDING,
    очищает error_details.
    
    Raises:
        ValueError: Если задача не в статусе FAILED
    """

def cancel_batch(batch_id: str) -> int:
    """
    Отменить пакет (только PENDING).
    
    Args:
        batch_id: ID пакета
        
    Returns:
        Количество отменённых задач
        
    Raises:
        ValueError: Если пакет не в статусе PENDING
    """

def close() -> None:
    """
    Закрыть соединение с БД.
    
    Вызывается при graceful shutdown сервера.
    """
```

---

## Интеграция в server.py

```python
# server.py (начало файла)

from database import DatabaseManager

# После импортов, перед mcp = FastMCP(...)
logger.info("Initializing database...")
db = DatabaseManager()
db.initialize()
logger.info("Database ready")

# ... регистрация инструментов ...

if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        db.close()
    except Exception as e:
        logger.exception(f"Critical error: {e}")
        db.close()
        sys.exit(1)
```

---

## Тестирование

### Запуск pytest тестов

```bash
# Запустить все тесты database
pytest tests/test_database.py -v

# Запустить конкретный тест-класс
pytest tests/test_database.py::TestBatches -v

# Запустить с покрытием
pytest tests/test_database.py --cov=database --cov-report=html
```

**Покрытие тестами:**

- ✅ Инициализация БД и seed данных (2 теста)
- ✅ Operation Types CRUD (5 тестов)
- ✅ Batches CRUD (6 тестов)
- ✅ Tasks CRUD (8 тестов)
- ✅ Транзакции (1 тест)
- ✅ Утилиты и recovery (5 тестов)

**Всего:** 27 тестов

---

## Критерии готовности

- ✅ `DatabaseManager` создаёт схему при старте
- ✅ Seed данные загружаются в `operation_types`
- ✅ Thread-safe (Lock + check_same_thread=False)
- ✅ Все CRUD методы работают
- ✅ `create_batch_with_tasks()` атомарна (транзакция)
- ✅ `recover_stale_tasks()` находит зависшие задачи
- ✅ Тестовый скрипт проходит без ошибок
- ✅ Интегрировано в `server.py` (инициализация + shutdown)

---

## Следующий шаг

**Фаза 2:** Worker Skeleton — фоновый поток, который берёт задачи из БД и отправляет в Batch API.
