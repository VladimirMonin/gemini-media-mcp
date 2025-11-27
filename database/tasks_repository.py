"""
TasksRepository — репозиторий для работы с tasks.

Обеспечивает:
- CRUD операции для задач
- Получение задач по batch_id и статусу
- Обновление статуса, завершение, ошибки
- Поиск по ключевым словам
"""

import json
from typing import Optional
from .connection_manager import ConnectionManager
from . import queries
from utils.logger import get_logger

logger = get_logger(__name__)


class TasksRepository:
    """
    Репозиторий для работы с задачами (tasks).

    Содержит методы для создания, чтения и обновления задач.
    """

    def __init__(self, connection_manager: ConnectionManager):
        """
        Инициализация репозитория.

        Args:
            connection_manager: Менеджер соединения с БД
        """
        self.conn_mgr = connection_manager

    # ========================================================================
    # CREATE
    # ========================================================================

    def create(
        self,
        task_id: str,
        batch_id: str,
        operation_type: str,
        input_payload: dict,
        target_path: str,
        search_keywords: Optional[str] = None,
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
        """
        payload_json = json.dumps(input_payload)

        self.conn_mgr.execute(
            queries.INSERT_TASK,
            (
                task_id,
                batch_id,
                operation_type,
                payload_json,
                target_path,
                search_keywords,
            ),
        )
        self.conn_mgr.commit()

        logger.debug(
            f"Task created: {task_id}, batch={batch_id}, operation={operation_type}"
        )

    # ========================================================================
    # READ
    # ========================================================================

    def get(self, task_id: str) -> Optional[dict]:
        """
        Получить задачу по ID.

        Args:
            task_id: UUID задачи

        Returns:
            dict с полями id, batch_id, status, input_payload (десериализованный), etc.
            или None если не найден
        """
        cursor = self.conn_mgr.execute(queries.GET_TASK, (task_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        task = dict(row)
        # Десериализовать input_payload
        task["input_payload"] = json.loads(task["input_payload"])
        return task

    def get_by_batch(self, batch_id: str) -> list[dict]:
        """
        Все задачи пакета.

        Args:
            batch_id: UUID пакета

        Returns:
            Список задач с десериализованными input_payload
        """
        cursor = self.conn_mgr.execute(queries.GET_TASKS_BY_BATCH, (batch_id,))
        rows = cursor.fetchall()

        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task["input_payload"])
            tasks.append(task)

        return tasks

    def get_pending(self, limit: int = 100) -> list[dict]:
        """
        Задачи в статусе PENDING (для воркера).

        Args:
            limit: Максимум задач за раз

        Returns:
            Список задач с полями из БД (+ десериализованный input_payload)
        """
        cursor = self.conn_mgr.execute(queries.GET_PENDING_TASKS, (limit,))
        rows = cursor.fetchall()

        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task["input_payload"])
            tasks.append(task)

        return tasks

    def get_processing(self) -> list[dict]:
        """
        Задачи в статусе PROCESSING (для recovery после сбоя).

        Returns:
            Список задач с десериализованными input_payload
        """
        cursor = self.conn_mgr.execute(queries.GET_PROCESSING_TASKS)
        rows = cursor.fetchall()

        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task["input_payload"])
            tasks.append(task)

        return tasks

    # ========================================================================
    # UPDATE
    # ========================================================================

    def update_status(
        self, task_id: str, status: str, error_details: Optional[str] = None
    ) -> None:
        """
        Обновить статус задачи.

        Args:
            task_id: ID задачи
            status: Новый статус
            error_details: Текст ошибки (для FAILED/DELIVERY_FAILED)
        """
        self.conn_mgr.execute(
            queries.UPDATE_TASK_STATUS, (status, error_details, task_id)
        )
        self.conn_mgr.commit()

        logger.debug(f"Task {task_id} updated: status={status}")

    def mark_completed(self, task_id: str, local_path: str) -> None:
        """
        Завершить задачу успешно.

        Updates:
            - status = 'COMPLETED'
            - local_path = <путь>
            - completed_at = NOW()

        Args:
            task_id: ID задачи
            local_path: Путь к сохранённому файлу
        """
        self.conn_mgr.execute(queries.UPDATE_TASK_COMPLETED, (local_path, task_id))
        self.conn_mgr.commit()

        logger.info(f"Task completed: {task_id} -> {local_path}")

    def mark_failed(self, task_id: str, error: str) -> None:
        """
        Пометить задачу как провалившуюся.

        Updates:
            - status = 'FAILED'
            - error_details = <ошибка>
            - completed_at = NOW()

        Args:
            task_id: ID задачи
            error: Текст ошибки
        """
        self.conn_mgr.execute(queries.UPDATE_TASK_FAILED, (error, task_id))
        self.conn_mgr.commit()

        logger.warning(f"Task failed: {task_id} - {error}")

    # ========================================================================
    # SEARCH
    # ========================================================================

    def search(
        self, query: str, operation_type: Optional[str] = None, limit: int = 10
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
            tasks = search(query='cyberpunk city', operation_type='IMG_GEN')
        """
        # Для LIKE запроса
        like_pattern = f"%{query}%"

        cursor = self.conn_mgr.execute(
            queries.SEARCH_TASKS,
            (like_pattern, like_pattern, operation_type, operation_type, limit),
        )
        rows = cursor.fetchall()

        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task["input_payload"])
            tasks.append(task)

        return tasks
