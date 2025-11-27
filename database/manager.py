"""
DatabaseManager — Singleton для управления БД задач.

Обеспечивает:
- Thread-safety через threading.Lock
- ACID-транзакции
- Автоматическую инициализацию схемы
- CRUD операции для operation_types, batches, tasks
- Recovery зависших задач
"""

import sqlite3
import threading
import json
from typing import Optional

from . import schema
from . import queries
from . import seed_data
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Singleton менеджер для работы с БД задач.

    Thread-safe благодаря threading.Lock и check_same_thread=False.
    Все SQL запросы вынесены в queries.py для переиспользования.
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
        if self._initialized:
            return

        self._conn: Optional[sqlite3.Connection] = None
        self._db_path: Optional[str] = None
        self._initialized = True

    # ========================================================================
    # Инициализация
    # ========================================================================

    def initialize(self, db_path: str = "gemini_tasks.db") -> None:
        """
        Создаёт БД, таблицы и заполняет справочники.

        Args:
            db_path: Путь к файлу БД (по умолчанию в корне проекта)

        Raises:
            RuntimeError: Если не удалось создать схему
        """
        if self._conn is not None:
            logger.warning("Database already initialized")
            return

        try:
            self._db_path = db_path
            self._conn = sqlite3.connect(
                db_path,
                check_same_thread=False,
                isolation_level=None,  # Autocommit mode для простых операций
            )
            self._conn.row_factory = sqlite3.Row  # Доступ по именам столбцов

            # Создать таблицы
            with self._lock:
                cursor = self._conn.cursor()

                for table_ddl in schema.ALL_TABLES:
                    cursor.execute(table_ddl)

                for index_ddl in schema.ALL_INDEXES:
                    cursor.execute(index_ddl)

                # Заполнить справочники
                cursor.executemany(
                    seed_data.INSERT_OPERATION_TYPES_QUERY,
                    seed_data.OPERATION_TYPES_SEED,
                )

                self._conn.commit()

            logger.info(f"Database initialized: {db_path}")

        except Exception as e:
            logger.exception("Failed to initialize database")
            raise RuntimeError(f"Database initialization failed: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """
        Получить соединение с БД.

        Returns:
            sqlite3.Connection

        Raises:
            RuntimeError: Если БД не инициализирована
        """
        if self._conn is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._conn

    def close(self) -> None:
        """Закрыть соединение с БД (при graceful shutdown)."""
        if self._conn is not None:
            with self._lock:
                self._conn.close()
                self._conn = None
            logger.info("Database connection closed")

    # ========================================================================
    # Operation Types (справочник)
    # ========================================================================

    def get_operation_type(self, code: str) -> Optional[dict]:
        """
        Получить operation_type по коду.

        Args:
            code: Код операции (например, 'IMG_GEN_BATCH')

        Returns:
            dict с полями operation_type, display_name, description, execution_mode
            или None если не найден
        """
        cursor = self.get_connection().cursor()
        row = cursor.execute(queries.GET_OPERATION_TYPE, (code,)).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_all_operation_types(self) -> list[dict]:
        """
        Получить весь справочник operation_types.

        Returns:
            Список словарей с operation_type, display_name, execution_mode, etc.
        """
        cursor = self.get_connection().cursor()
        rows = cursor.execute(queries.GET_ALL_OPERATION_TYPES).fetchall()
        return [dict(row) for row in rows]

    def get_execution_mode(self, code: str) -> str:
        """
        Получить execution_mode для операции.

        Args:
            code: Код операции

        Returns:
            'sync' | 'batch' | 'local_queue'

        Raises:
            ValueError: Если operation_type не найден
        """
        cursor = self.get_connection().cursor()
        row = cursor.execute(queries.GET_EXECUTION_MODE, (code,)).fetchone()

        if row is None:
            raise ValueError(f"Unknown operation_type: {code}")

        return row[0]

    # ========================================================================
    # Batches (CREATE)
    # ========================================================================

    def create_batch(
        self, batch_id: str, operation_type: str, total_tasks: int
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
        # Валидация operation_type
        if self.get_operation_type(operation_type) is None:
            raise ValueError(f"Unknown operation_type: {operation_type}")

        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(
                queries.INSERT_BATCH, (batch_id, operation_type, total_tasks)
            )
            self.get_connection().commit()

        logger.debug(
            f"Batch created: {batch_id}, operation={operation_type}, tasks={total_tasks}"
        )

    # ========================================================================
    # Batches (READ)
    # ========================================================================

    def get_batch(self, batch_id: str) -> Optional[dict]:
        """
        Получить пакет по ID.

        Args:
            batch_id: UUID пакета

        Returns:
            dict с полями id, google_batch_id, operation_type, status, etc.
            или None если не найден
        """
        cursor = self.get_connection().cursor()
        row = cursor.execute(queries.GET_BATCH, (batch_id,)).fetchone()

        if row is None:
            return None

        return dict(row)

    def get_pending_batches(self) -> list[dict]:
        """
        Получить активные пакеты для воркера.

        Returns:
            Пакеты со статусом PENDING, SUBMITTED, PROCESSING
        """
        cursor = self.get_connection().cursor()
        rows = cursor.execute(queries.GET_PENDING_BATCHES).fetchall()
        return [dict(row) for row in rows]

    # ========================================================================
    # Batches (UPDATE)
    # ========================================================================

    def update_batch_status(
        self, batch_id: str, status: str, google_batch_id: Optional[str] = None
    ) -> None:
        """
        Обновить статус пакета.

        Args:
            batch_id: ID пакета
            status: Новый статус (PENDING, SUBMITTED, PROCESSING, COMPLETED, FAILED)
            google_batch_id: ID от Google Cloud (опционально)
        """
        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(
                queries.UPDATE_BATCH_STATUS, (status, google_batch_id, batch_id)
            )
            self.get_connection().commit()

        logger.debug(
            f"Batch {batch_id} updated: status={status}, google_id={google_batch_id}"
        )

    def update_batch_completed(self, batch_id: str) -> None:
        """
        Завершить пакет (completed_at = NOW(), status = COMPLETED).

        Args:
            batch_id: ID пакета
        """
        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(queries.UPDATE_BATCH_COMPLETED, (batch_id,))
            self.get_connection().commit()

        logger.info(f"Batch completed: {batch_id}")

    # ========================================================================
    # Batches (STATS)
    # ========================================================================

    def get_batch_progress(self, batch_id: str) -> dict:
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
        cursor = self.get_connection().cursor()
        row = cursor.execute(queries.GET_BATCH_PROGRESS, (batch_id,)).fetchone()

        return {
            "total": row["total"],
            "completed": row["completed"],
            "failed": row["failed"],
            "pending": row["pending"],
            "processing": row["processing"],
        }

    # ========================================================================
    # Tasks (CREATE)
    # ========================================================================

    def create_task(
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

        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(
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
            self.get_connection().commit()

        logger.debug(
            f"Task created: {task_id}, batch={batch_id}, operation={operation_type}"
        )

    # ========================================================================
    # Tasks (READ)
    # ========================================================================

    def get_task(self, task_id: str) -> Optional[dict]:
        """
        Получить задачу по ID.

        Args:
            task_id: UUID задачи

        Returns:
            dict с полями id, batch_id, status, input_payload (десериализованный), etc.
            или None если не найден
        """
        cursor = self.get_connection().cursor()
        row = cursor.execute(queries.GET_TASK, (task_id,)).fetchone()

        if row is None:
            return None

        task = dict(row)
        # Десериализовать input_payload
        task["input_payload"] = json.loads(task["input_payload"])
        return task

    def get_tasks_by_batch(self, batch_id: str) -> list[dict]:
        """
        Все задачи пакета.

        Args:
            batch_id: UUID пакета

        Returns:
            Список задач с десериализованными input_payload
        """
        cursor = self.get_connection().cursor()
        rows = cursor.execute(queries.GET_TASKS_BY_BATCH, (batch_id,)).fetchall()

        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task["input_payload"])
            tasks.append(task)

        return tasks

    def get_pending_tasks(self, limit: int = 100) -> list[dict]:
        """
        Задачи в статусе PENDING (для воркера).

        Args:
            limit: Максимум задач за раз

        Returns:
            Список задач с полями из БД (+ десериализованный input_payload)
        """
        cursor = self.get_connection().cursor()
        rows = cursor.execute(queries.GET_PENDING_TASKS, (limit,)).fetchall()

        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task["input_payload"])
            tasks.append(task)

        return tasks

    def get_processing_tasks(self) -> list[dict]:
        """
        Задачи в статусе PROCESSING (для recovery после сбоя).

        Returns:
            Список задач с десериализованными input_payload
        """
        cursor = self.get_connection().cursor()
        rows = cursor.execute(queries.GET_PROCESSING_TASKS).fetchall()

        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task["input_payload"])
            tasks.append(task)

        return tasks

    # ========================================================================
    # Tasks (UPDATE)
    # ========================================================================

    def update_task_status(
        self, task_id: str, status: str, error_details: Optional[str] = None
    ) -> None:
        """
        Обновить статус задачи.

        Args:
            task_id: ID задачи
            status: Новый статус
            error_details: Текст ошибки (для FAILED/DELIVERY_FAILED)
        """
        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(queries.UPDATE_TASK_STATUS, (status, error_details, task_id))
            self.get_connection().commit()

        logger.debug(f"Task {task_id} updated: status={status}")

    def update_task_completed(self, task_id: str, local_path: str) -> None:
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
        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(queries.UPDATE_TASK_COMPLETED, (local_path, task_id))
            self.get_connection().commit()

        logger.info(f"Task completed: {task_id} -> {local_path}")

    def update_task_failed(self, task_id: str, error: str) -> None:
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
        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(queries.UPDATE_TASK_FAILED, (error, task_id))
            self.get_connection().commit()

        logger.warning(f"Task failed: {task_id} - {error}")

    # ========================================================================
    # Tasks (SEARCH)
    # ========================================================================

    def search_tasks(
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
            tasks = search_tasks(query='cyberpunk city', operation_type='IMG_GEN')
        """
        cursor = self.get_connection().cursor()

        # Для LIKE запроса
        like_pattern = f"%{query}%"

        rows = cursor.execute(
            queries.SEARCH_TASKS,
            (like_pattern, like_pattern, operation_type, operation_type, limit),
        ).fetchall()

        tasks = []
        for row in rows:
            task = dict(row)
            task["input_payload"] = json.loads(task["input_payload"])
            tasks.append(task)

        return tasks

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
        # Валидация operation_type
        if self.get_operation_type(operation_type) is None:
            raise ValueError(f"Unknown operation_type: {operation_type}")

        with self._lock:
            conn = self.get_connection()
            cursor = conn.cursor()

            try:
                # Начать транзакцию
                conn.execute("BEGIN")

                # Создать пакет
                cursor.execute(
                    queries.INSERT_BATCH, (batch_id, operation_type, len(tasks))
                )

                # Создать задачи
                for task in tasks:
                    payload_json = json.dumps(task["input_payload"])
                    cursor.execute(
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
                conn.commit()

                logger.info(f"Batch with tasks created: {batch_id}, {len(tasks)} tasks")

            except Exception as e:
                conn.rollback()
                logger.exception(f"Failed to create batch with tasks: {e}")
                raise RuntimeError(f"Transaction failed: {e}")

    # ========================================================================
    # Утилиты
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
        cursor = self.get_connection().cursor()
        row = cursor.execute(queries.GET_STATS).fetchone()
        return dict(row)

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
        with self._lock:
            cursor = self.get_connection().cursor()

            # Сначала посчитать
            count_row = cursor.execute(
                queries.GET_STALE_TASKS_COUNT, (timeout_minutes,)
            ).fetchone()
            count = count_row[0]

            if count == 0:
                return 0

            # Восстановить
            cursor.execute(queries.RECOVER_STALE_TASKS, (timeout_minutes,))
            self.get_connection().commit()

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
        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(queries.CLEANUP_OLD_TASKS, (days,))
            deleted = cursor.rowcount
            self.get_connection().commit()

        logger.info(f"Cleaned up {deleted} old tasks (older than {days} days)")
        return deleted

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
        task = self.get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        if task["status"] != "FAILED":
            raise ValueError(
                f"Task {task_id} is not FAILED (current status: {task['status']})"
            )

        with self._lock:
            cursor = self.get_connection().cursor()
            cursor.execute(queries.RETRY_TASK, (task_id,))
            self.get_connection().commit()

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
        batch = self.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch not found: {batch_id}")

        if batch["status"] != "PENDING":
            raise ValueError(
                f"Batch {batch_id} is not PENDING (current status: {batch['status']})"
            )

        with self._lock:
            cursor = self.get_connection().cursor()

            # Отменить задачи
            cursor.execute(queries.CANCEL_BATCH_TASKS, (batch_id,))
            cancelled_count = cursor.rowcount

            # Обновить статус пакета
            cursor.execute(queries.UPDATE_BATCH_CANCELLED, (batch_id,))

            self.get_connection().commit()

        logger.info(f"Batch cancelled: {batch_id}, {cancelled_count} tasks affected")
        return cancelled_count
