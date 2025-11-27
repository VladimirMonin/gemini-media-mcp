"""
TaskUtilities — сервис для высокоуровневых операций с задачами.

Обеспечивает:
- Recovery зависших задач (health check)
- Cleanup старых задач
- Retry провалившихся задач
- Отмена пакетов
- Статистика по БД
"""

import json
from .connection_manager import ConnectionManager
from .batches_repository import BatchesRepository
from .tasks_repository import TasksRepository
from . import queries
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskUtilities:
    """
    Сервис для утилит и высокоуровневых операций с задачами.

    Содержит методы для восстановления, очистки, retry и статистики.
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        batches_repo: BatchesRepository,
        tasks_repo: TasksRepository,
    ):
        """
        Инициализация сервиса.

        Args:
            connection_manager: Менеджер соединения с БД
            batches_repo: Репозиторий пакетов
            tasks_repo: Репозиторий задач
        """
        self.conn_mgr = connection_manager
        self.batches = batches_repo
        self.tasks = tasks_repo

    # ========================================================================
    # Статистика
    # ========================================================================

    def get_stats(self) -> dict:
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
        cursor = self.conn_mgr.execute(queries.GET_STATS)
        row = cursor.fetchone()
        return dict(row)

    # ========================================================================
    # Recovery и Cleanup
    # ========================================================================

    def recover_stale_tasks(self, timeout_minutes: int = 30) -> int:
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
        # Сформировать параметр со знаком минус для SQLite datetime
        timeout_param = f"-{timeout_minutes}"

        # Сначала посчитать
        cursor = self.conn_mgr.execute(queries.GET_STALE_TASKS_COUNT, (timeout_param,))
        count_row = cursor.fetchone()
        count = count_row[0]

        if count == 0:
            return 0

        # Восстановить
        self.conn_mgr.execute(queries.RECOVER_STALE_TASKS, (timeout_param,))
        self.conn_mgr.commit()

        logger.warning(f"Recovered {count} stale tasks (timeout: {timeout_minutes}m)")
        return count

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        Удаление старых завершённых задач.

        Args:
            days: Возраст задач для удаления

        Returns:
            Количество удалённых записей
        """
        cursor = self.conn_mgr.execute(queries.CLEANUP_OLD_TASKS, (days,))
        deleted = cursor.rowcount
        self.conn_mgr.commit()

        logger.info(f"Cleaned up {deleted} old tasks (older than {days} days)")
        return deleted

    # ========================================================================
    # Retry и Cancel
    # ========================================================================

    def retry_task(self, task_id: str) -> None:
        """
        Перезапустить задачу.

        Переводит задачу из статуса FAILED обратно в PENDING,
        очищает error_details.

        Args:
            task_id: ID задачи

        Raises:
            ValueError: Если задача не в статусе FAILED
        """
        # Проверить статус
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        if task["status"] != "FAILED":
            raise ValueError(
                f"Task {task_id} is not FAILED (current status: {task['status']})"
            )

        self.conn_mgr.execute(queries.RETRY_TASK, (task_id,))
        self.conn_mgr.commit()

        logger.info(f"Task retried: {task_id}")

    def cancel_batch(self, batch_id: str) -> int:
        """
        Отменить пакет (только PENDING).

        Args:
            batch_id: ID пакета

        Returns:
            Количество отменённых задач

        Raises:
            ValueError: Если пакет не в статусе PENDING
        """
        # Проверить статус пакета
        batch = self.batches.get(batch_id)
        if batch is None:
            raise ValueError(f"Batch not found: {batch_id}")

        if batch["status"] != "PENDING":
            raise ValueError(
                f"Batch {batch_id} is not PENDING (current status: {batch['status']})"
            )

        # Отменить задачи
        cursor = self.conn_mgr.execute(queries.CANCEL_BATCH_TASKS, (batch_id,))
        cancelled_count = cursor.rowcount

        # Обновить статус пакета
        self.conn_mgr.execute(queries.UPDATE_BATCH_CANCELLED, (batch_id,))

        self.conn_mgr.commit()

        logger.info(f"Batch cancelled: {batch_id}, {cancelled_count} tasks affected")
        return cancelled_count

    # ========================================================================
    # Транзакции
    # ========================================================================

    def create_batch_with_tasks(
        self, batch_id: str, operation_type: str, tasks: list[dict]
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

        Raises:
            ValueError: Если operation_type не существует
            RuntimeError: Если транзакция не удалась
        """
        # Валидация operation_type (через batches репозиторий)
        if not self.batches.op_types.exists(operation_type):
            raise ValueError(f"Unknown operation_type: {operation_type}")

        try:
            # Начать транзакцию
            self.conn_mgr.begin_transaction()

            # Создать пакет
            self.conn_mgr.execute(
                queries.INSERT_BATCH, (batch_id, operation_type, len(tasks))
            )

            # Создать задачи
            for task in tasks:
                payload_json = json.dumps(task["input_payload"])
                self.conn_mgr.execute(
                    queries.INSERT_TASK,
                    (
                        task["task_id"],
                        batch_id,
                        operation_type,
                        payload_json,
                        task["target_path"],
                        task.get("search_keywords"),
                    ),
                )

            # Зафиксировать транзакцию
            self.conn_mgr.commit()

            logger.info(f"Batch with tasks created: {batch_id}, {len(tasks)} tasks")

        except Exception as e:
            self.conn_mgr.rollback()
            logger.exception(f"Failed to create batch with tasks: {e}")
            raise RuntimeError(f"Transaction failed: {e}")
