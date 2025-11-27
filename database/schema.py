"""
DDL запросы для создания схемы БД.

Содержит только CREATE TABLE, CREATE INDEX, DROP операции.
Все запросы идемпотентны (используют IF NOT EXISTS).
"""

# ============================================================================
# Таблицы
# ============================================================================

CREATE_OPERATION_TYPES_TABLE = """
CREATE TABLE IF NOT EXISTS operation_types (
    operation_type TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    execution_mode TEXT NOT NULL CHECK(execution_mode IN ('sync', 'batch', 'local_queue')),
    default_priority INTEGER DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_BATCHES_TABLE = """
CREATE TABLE IF NOT EXISTS batches (
    id TEXT PRIMARY KEY,
    google_batch_id TEXT,
    operation_type TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'SUBMITTED', 'PROCESSING', 'COMPLETED', 'FAILED')),
    total_tasks INTEGER DEFAULT 0,
    FOREIGN KEY (operation_type) REFERENCES operation_types(operation_type)
)
"""

CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'SUBMITTED', 'PROCESSING', 'COMPLETED', 'FAILED', 'DELIVERY_FAILED')),
    input_payload TEXT NOT NULL,
    search_keywords TEXT,
    target_path TEXT NOT NULL,
    local_path TEXT,
    error_details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (batch_id) REFERENCES batches(id),
    FOREIGN KEY (operation_type) REFERENCES operation_types(operation_type)
)
"""

# ============================================================================
# Индексы
# ============================================================================

CREATE_BATCHES_STATUS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_batches_status ON batches(status)
"""

CREATE_BATCHES_GOOGLE_ID_INDEX = """
CREATE INDEX IF NOT EXISTS idx_batches_google_id ON batches(google_batch_id)
"""

CREATE_TASKS_BATCH_INDEX = """
CREATE INDEX IF NOT EXISTS idx_tasks_batch ON tasks(batch_id)
"""

CREATE_TASKS_STATUS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
"""

CREATE_TASKS_OPERATION_INDEX = """
CREATE INDEX IF NOT EXISTS idx_tasks_operation ON tasks(operation_type)
"""

CREATE_TASKS_SEARCH_INDEX = """
CREATE INDEX IF NOT EXISTS idx_tasks_search ON tasks(search_keywords)
"""

# ============================================================================
# Группировка для массового выполнения
# ============================================================================

ALL_TABLES = [
    CREATE_OPERATION_TYPES_TABLE,
    CREATE_BATCHES_TABLE,
    CREATE_TASKS_TABLE,
]

ALL_INDEXES = [
    CREATE_BATCHES_STATUS_INDEX,
    CREATE_BATCHES_GOOGLE_ID_INDEX,
    CREATE_TASKS_BATCH_INDEX,
    CREATE_TASKS_STATUS_INDEX,
    CREATE_TASKS_OPERATION_INDEX,
    CREATE_TASKS_SEARCH_INDEX,
]
