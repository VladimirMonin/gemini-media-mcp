"""
DatabaseManager — Singleton фасад для работы с БД задач (РЕФАКТОРИНГ).

Делегирует вызовы специализированным репозиториям:
- ConnectionManager — управление соединением, транзакциями
- OperationTypesRepository — справочник operation_types
- BatchesRepository — CRUD для batches
- TasksRepository — CRUD для tasks
- TaskUtilities — recovery, cleanup, retry, stats

Сохраняет обратную совместимость со старым API (все методы работают как раньше).
"""

import threading
from typing import Optional

from .connection_manager import ConnectionManager
from .operation_types_repository import OperationTypesRepository
from .batches_repository import BatchesRepository
from .tasks_repository import TasksRepository
from .task_utilities import TaskUtilities
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Singleton фасад для работы с БД задач.

    Внутренне использует репозитории, но сохраняет старый API
    для совместимости с тестами и WorkerManager.
    """

    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Конструктор вызывается каждый раз, но инициализация только один раз."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Создать репозитории
        self._conn = ConnectionManager()
        self._op_types = OperationTypesRepository(self._conn)
        self._batches = BatchesRepository(self._conn, self._op_types)
        self._tasks = TasksRepository(self._conn)
        self._utils = TaskUtilities(self._conn, self._batches, self._tasks)

        self._initialized = True

    # ========================================================================
    # Инициализация (делегирование в ConnectionManager)
    # ========================================================================

    def initialize(self, db_path: str = "gemini_tasks.db") -> None:
        """
        Создаёт БД, таблицы и заполняет справочники.

        Args:
            db_path: Путь к файлу БД (по умолчанию в корне проекта)

        Raises:
            RuntimeError: Если не удалось создать схему
        """
        self._conn.initialize(db_path)

    def get_connection(self):
        """Получить соединение с БД (для обратной совместимости)."""
        return self._conn.connection

    def close(self) -> None:
        """Закрыть соединение с БД (при graceful shutdown)."""
        self._conn.close()

    # ========================================================================
    # Operation Types (делегирование в OperationTypesRepository)
    # ========================================================================

    def get_operation_type(self, code: str) -> Optional[dict]:
        """Получить operation_type по коду."""
        return self._op_types.get(code)

    def get_all_operation_types(self) -> list[dict]:
        """Получить весь справочник operation_types."""
        return self._op_types.get_all()

    def get_execution_mode(self, code: str) -> str:
        """Получить execution_mode для операции."""
        return self._op_types.get_execution_mode(code)

    # ========================================================================
    # Batches (делегирование в BatchesRepository)
    # ========================================================================

    def create_batch(
        self, batch_id: str, operation_type: str, total_tasks: int
    ) -> None:
        """Создать новый пакет."""
        self._batches.create(batch_id, operation_type, total_tasks)

    def get_batch(self, batch_id: str) -> Optional[dict]:
        """Получить пакет по ID."""
        return self._batches.get(batch_id)

    def get_pending_batches(self) -> list[dict]:
        """Получить активные пакеты для воркера."""
        return self._batches.get_pending()

    def update_batch_status(
        self, batch_id: str, status: str, google_batch_id: Optional[str] = None
    ) -> None:
        """Обновить статус пакета."""
        self._batches.update_status(batch_id, status, google_batch_id)

    def update_batch_completed(self, batch_id: str) -> None:
        """Завершить пакет (completed_at = NOW(), status = COMPLETED)."""
        self._batches.mark_completed(batch_id)

    def get_batch_progress(self, batch_id: str) -> dict:
        """Прогресс выполнения пакета."""
        return self._batches.get_progress(batch_id)

    # ========================================================================
    # Tasks (делегирование в TasksRepository)
    # ========================================================================

    def create_task(
        self,
        task_id: str,
        batch_id: str,
        operation_type: str,
        input_payload: dict,
        target_path: Optional[str] = None,
        search_keywords: Optional[str] = None,
    ) -> None:
        """Создать задачу."""
        self._tasks.create(
            task_id,
            batch_id,
            operation_type,
            input_payload,
            target_path,
            search_keywords,
        )

    def get_task(self, task_id: str) -> Optional[dict]:
        """Получить задачу по ID."""
        return self._tasks.get(task_id)

    def get_tasks_by_batch(self, batch_id: str) -> list[dict]:
        """Все задачи пакета."""
        return self._tasks.get_by_batch(batch_id)

    def get_pending_tasks(self, limit: int = 100) -> list[dict]:
        """Задачи в статусе PENDING (для воркера)."""
        return self._tasks.get_pending(limit)

    def get_processing_tasks(self) -> list[dict]:
        """Задачи в статусе PROCESSING (для recovery после сбоя)."""
        return self._tasks.get_processing()

    def get_pending_local_queue_tasks(self, limit: int = 1) -> list[dict]:
        """
        Задачи в статусе PENDING с execution_mode='local_queue'.

        Используется для TTS и других операций, не поддерживающих Batch API.

        Args:
            limit: Максимум задач за раз (дефолт=1 для rate limiting)

        Returns:
            Список задач с десериализованными input_payload
        """
        return self._tasks.get_pending_local_queue(limit)

    def update_task_status(
        self, task_id: str, status: str, error_details: Optional[str] = None
    ) -> None:
        """Обновить статус задачи."""
        self._tasks.update_status(task_id, status, error_details)

    def update_task_completed(self, task_id: str, local_path: str) -> None:
        """Завершить задачу успешно."""
        self._tasks.mark_completed(task_id, local_path)

    def update_task_failed(self, task_id: str, error: str) -> None:
        """Пометить задачу как провалившуюся."""
        self._tasks.mark_failed(task_id, error)

    def search_tasks(
        self, query: str, operation_type: Optional[str] = None, limit: int = 10
    ) -> list[dict]:
        """Поиск по истории задач."""
        return self._tasks.search(query, operation_type, limit)

    # ========================================================================
    # Утилиты (делегирование в TaskUtilities)
    # ========================================================================

    def get_stats(self) -> dict:
        """Статистика по БД."""
        return self._utils.get_stats()

    def recover_stale_tasks(self, timeout_minutes: int = 30) -> int:
        """Recovery зависших задач."""
        return self._utils.recover_stale_tasks(timeout_minutes)

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """Удаление старых завершённых задач."""
        return self._utils.cleanup_old_tasks(days)

    def retry_task(self, task_id: str) -> None:
        """Перезапустить задачу."""
        self._utils.retry_task(task_id)

    def cancel_batch(self, batch_id: str) -> int:
        """Отменить пакет (только PENDING)."""
        return self._utils.cancel_batch(batch_id)

    def create_batch_with_tasks(
        self, batch_id: str, operation_type: str, tasks: list[dict]
    ) -> None:
        """Атомарно создать пакет + задачи."""
        self._utils.create_batch_with_tasks(batch_id, operation_type, tasks)
