"""
SQL запросы с плейсхолдерами для CRUD операций.

Все запросы используют `?` для параметризации (защита от SQL-инъекций).
Группировка по сущностям: operation_types, batches, tasks, stats, recovery.
"""

# ============================================================================
# Operation Types (справочник)
# ============================================================================

GET_OPERATION_TYPE = """
SELECT operation_type, display_name, description, execution_mode, default_priority, created_at
FROM operation_types
WHERE operation_type = ?
"""

GET_ALL_OPERATION_TYPES = """
SELECT operation_type, display_name, description, execution_mode, default_priority, created_at
FROM operation_types
ORDER BY operation_type
"""

GET_EXECUTION_MODE = """
SELECT execution_mode
FROM operation_types
WHERE operation_type = ?
"""

# ============================================================================
# Batches (CREATE)
# ============================================================================

INSERT_BATCH = """
INSERT INTO batches (id, operation_type, total_tasks)
VALUES (?, ?, ?)
"""

# ============================================================================
# Batches (READ)
# ============================================================================

GET_BATCH = """
SELECT id, google_batch_id, operation_type, created_at, completed_at, status, total_tasks
FROM batches
WHERE id = ?
"""

GET_PENDING_BATCHES = """
SELECT id, google_batch_id, operation_type, created_at, completed_at, status, total_tasks
FROM batches
WHERE status IN ('PENDING', 'SUBMITTED', 'PROCESSING')
ORDER BY created_at ASC
"""

# ============================================================================
# Batches (UPDATE)
# ============================================================================

UPDATE_BATCH_STATUS = """
UPDATE batches
SET status = ?, google_batch_id = ?
WHERE id = ?
"""

UPDATE_BATCH_COMPLETED = """
UPDATE batches
SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP
WHERE id = ?
"""

# ============================================================================
# Batches (STATS)
# ============================================================================

GET_BATCH_PROGRESS = """
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
    SUM(CASE WHEN status = 'PROCESSING' THEN 1 ELSE 0 END) as processing
FROM tasks
WHERE batch_id = ?
"""

# ============================================================================
# Tasks (CREATE)
# ============================================================================

INSERT_TASK = """
INSERT INTO tasks (id, batch_id, operation_type, input_payload, target_path, search_keywords)
VALUES (?, ?, ?, ?, ?, ?)
"""

# ============================================================================
# Tasks (READ)
# ============================================================================

GET_TASK = """
SELECT id, batch_id, operation_type, status, input_payload, search_keywords, 
       target_path, local_path, error_details, created_at, updated_at, completed_at
FROM tasks
WHERE id = ?
"""

GET_TASKS_BY_BATCH = """
SELECT id, batch_id, operation_type, status, input_payload, search_keywords,
       target_path, local_path, error_details, created_at, updated_at, completed_at
FROM tasks
WHERE batch_id = ?
ORDER BY created_at ASC
"""

GET_PENDING_TASKS = """
SELECT id, batch_id, operation_type, status, input_payload, search_keywords,
       target_path, local_path, error_details, created_at, updated_at, completed_at
FROM tasks
WHERE status = 'PENDING'
ORDER BY created_at ASC
LIMIT ?
"""

GET_PROCESSING_TASKS = """
SELECT id, batch_id, operation_type, status, input_payload, search_keywords,
       target_path, local_path, error_details, created_at, updated_at, completed_at
FROM tasks
WHERE status = 'PROCESSING'
ORDER BY updated_at ASC
"""

# ============================================================================
# Tasks (UPDATE)
# ============================================================================

UPDATE_TASK_STATUS = """
UPDATE tasks
SET status = ?, error_details = ?, updated_at = CURRENT_TIMESTAMP
WHERE id = ?
"""

UPDATE_TASK_COMPLETED = """
UPDATE tasks
SET status = 'COMPLETED', local_path = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
WHERE id = ?
"""

UPDATE_TASK_FAILED = """
UPDATE tasks
SET status = 'FAILED', error_details = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
WHERE id = ?
"""

# ============================================================================
# Tasks (SEARCH)
# ============================================================================

SEARCH_TASKS = """
SELECT id, batch_id, operation_type, status, input_payload, search_keywords,
       target_path, local_path, error_details, created_at, updated_at, completed_at
FROM tasks
WHERE (search_keywords LIKE ? OR input_payload LIKE ?)
  AND (? IS NULL OR operation_type = ?)
ORDER BY created_at DESC
LIMIT ?
"""

# ============================================================================
# Recovery (зависшие задачи)
# ============================================================================

RECOVER_STALE_TASKS = """
UPDATE tasks
SET status = 'PENDING', updated_at = CURRENT_TIMESTAMP
WHERE status = 'PROCESSING'
  AND updated_at < datetime('now', '-' || ? || ' minutes')
"""

GET_STALE_TASKS_COUNT = """
SELECT COUNT(*)
FROM tasks
WHERE status = 'PROCESSING'
  AND updated_at < datetime('now', '-' || ? || ' minutes')
"""

# ============================================================================
# Retry
# ============================================================================

RETRY_TASK = """
UPDATE tasks
SET status = 'PENDING', error_details = NULL, updated_at = CURRENT_TIMESTAMP
WHERE id = ? AND status = 'FAILED'
"""

# ============================================================================
# Cancel Batch
# ============================================================================

CANCEL_BATCH_TASKS = """
UPDATE tasks
SET status = 'FAILED', error_details = 'Cancelled by user', updated_at = CURRENT_TIMESTAMP, completed_at = CURRENT_TIMESTAMP
WHERE batch_id = ? AND status = 'PENDING'
"""

UPDATE_BATCH_CANCELLED = """
UPDATE batches
SET status = 'FAILED', completed_at = CURRENT_TIMESTAMP
WHERE id = ? AND status = 'PENDING'
"""

# ============================================================================
# Cleanup
# ============================================================================

CLEANUP_OLD_TASKS = """
DELETE FROM tasks
WHERE status IN ('COMPLETED', 'FAILED')
  AND completed_at < datetime('now', '-' || ? || ' days')
"""

# ============================================================================
# Statistics
# ============================================================================

GET_STATS = """
SELECT 
    (SELECT COUNT(*) FROM tasks) as total_tasks,
    (SELECT COUNT(*) FROM tasks WHERE status = 'PENDING') as pending,
    (SELECT COUNT(*) FROM tasks WHERE status = 'PROCESSING') as processing,
    (SELECT COUNT(*) FROM tasks WHERE status = 'COMPLETED') as completed,
    (SELECT COUNT(*) FROM tasks WHERE status = 'FAILED') as failed,
    (SELECT COUNT(*) FROM batches WHERE status IN ('PENDING', 'SUBMITTED', 'PROCESSING')) as batches_active,
    (SELECT COUNT(*) FROM batches WHERE status = 'COMPLETED') as batches_completed
"""
