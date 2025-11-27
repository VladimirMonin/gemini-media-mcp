"""
BatchesRepository — репозиторий для работы с batches.

Обеспечивает:
- CRUD операции для пакетов задач
- Получение пакетов по статусу
- Обновление статуса и google_batch_id
- Статистика по пакетам
"""

from typing import Optional
from .connection_manager import ConnectionManager
from .operation_types_repository import OperationTypesRepository
from . import queries
from utils.logger import get_logger

logger = get_logger(__name__)


class BatchesRepository:
    """
    Репозиторий для работы с пакетами задач (batches).

    Содержит методы для создания, чтения и обновления пакетов.
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        operation_types_repo: OperationTypesRepository,
    ):
        """
        Инициализация репозитория.

        Args:
            connection_manager: Менеджер соединения с БД
            operation_types_repo: Репозиторий operation_types для валидации
        """
        self.conn_mgr = connection_manager
        self.op_types = operation_types_repo

    # ========================================================================
    # CREATE
    # ========================================================================

    def create(self, batch_id: str, operation_type: str, total_tasks: int) -> None:
        """
        Создать новый пакет.

        Args:
            batch_id: UUID (генерируется вызывающим кодом)
            operation_type: Код операции из справочника
            total_tasks: Количество задач в пакете

        Raises:
            ValueError: Если operation_type не существует
        """
        # Валидация operation_type
        if not self.op_types.exists(operation_type):
            raise ValueError(f"Unknown operation_type: {operation_type}")

        self.conn_mgr.execute(
            queries.INSERT_BATCH, (batch_id, operation_type, total_tasks)
        )
        self.conn_mgr.commit()

        logger.debug(
            f"Batch created: {batch_id}, operation={operation_type}, tasks={total_tasks}"
        )

    # ========================================================================
    # READ
    # ========================================================================

    def get(self, batch_id: str) -> Optional[dict]:
        """
        Получить пакет по ID.

        Args:
            batch_id: UUID пакета

        Returns:
            dict с полями id, google_batch_id, operation_type, status, etc.
            или None если не найден
        """
        cursor = self.conn_mgr.execute(queries.GET_BATCH, (batch_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def get_pending(self) -> list[dict]:
        """
        Получить активные пакеты для воркера.

        Returns:
            Пакеты со статусом PENDING, SUBMITTED, PROCESSING
        """
        cursor = self.conn_mgr.execute(queries.GET_PENDING_BATCHES)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_by_status(self, status: str) -> list[dict]:
        """
        Получить пакеты по статусу.

        Args:
            status: Статус (PENDING, SUBMITTED, PROCESSING, COMPLETED, FAILED)

        Returns:
            Список пакетов с указанным статусом
        """
        query = "SELECT * FROM batches WHERE status = ? ORDER BY created_at DESC"
        cursor = self.conn_mgr.execute(query, (status,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ========================================================================
    # UPDATE
    # ========================================================================

    def update_status(
        self, batch_id: str, status: str, google_batch_id: Optional[str] = None
    ) -> None:
        """
        Обновить статус пакета.

        Args:
            batch_id: ID пакета
            status: Новый статус (PENDING, SUBMITTED, PROCESSING, COMPLETED, FAILED)
            google_batch_id: ID от Google Cloud (опционально)
        """
        self.conn_mgr.execute(
            queries.UPDATE_BATCH_STATUS, (status, google_batch_id, batch_id)
        )
        self.conn_mgr.commit()

        logger.debug(
            f"Batch {batch_id} updated: status={status}, google_id={google_batch_id}"
        )

    def mark_completed(self, batch_id: str) -> None:
        """
        Завершить пакет (completed_at = NOW(), status = COMPLETED).

        Args:
            batch_id: ID пакета
        """
        self.conn_mgr.execute(queries.UPDATE_BATCH_COMPLETED, (batch_id,))
        self.conn_mgr.commit()

        logger.info(f"Batch completed: {batch_id}")

    # ========================================================================
    # STATS
    # ========================================================================

    def get_progress(self, batch_id: str) -> dict:
        """
        Прогресс выполнения пакета.

        Args:
            batch_id: ID пакета

        Returns:
            {
                'total': int,
                'completed': int,
                'failed': int,
                'pending': int,
                'processing': int
            }
        """
        cursor = self.conn_mgr.execute(queries.GET_BATCH_PROGRESS, (batch_id,))
        row = cursor.fetchone()

        return {
            "total": row["total"],
            "completed": row["completed"],
            "failed": row["failed"],
            "pending": row["pending"],
            "processing": row["processing"],
        }
