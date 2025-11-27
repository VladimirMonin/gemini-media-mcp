"""
ConnectionManager — базовый класс для управления SQLite соединением.

Обеспечивает:
- Thread-safety через threading.Lock
- Подключение к БД с check_same_thread=False
- Инициализация схемы и seed data
- Методы для транзакций
"""

import sqlite3
import threading
from typing import Optional

from . import schema
from . import seed_data
from utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Базовый менеджер SQLite соединения.

    Используется как основа для всех репозиториев.
    Обеспечивает потокобезопасность и управление транзакциями.
    """

    def __init__(self):
        """Инициализация без подключения (lazy initialization)."""
        self._conn: Optional[sqlite3.Connection] = None
        self._db_path: Optional[str] = None
        self._lock = threading.Lock()

    def initialize(self, db_path: str = "gemini_tasks.db") -> None:
        """
        Создаёт подключение к БД, таблицы и заполняет справочники.

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
                    seed_data.INSERT_OPERATION_TYPES,
                    seed_data.OPERATION_TYPES_SEED,
                )

                self._conn.commit()

            logger.info(f"Database initialized: {db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            if self._conn:
                self._conn.close()
                self._conn = None
            raise RuntimeError(f"Database initialization failed: {e}")

    def close(self) -> None:
        """Закрывает соединение с БД."""
        if self._conn:
            with self._lock:
                self._conn.close()
                self._conn = None
            logger.info("Database connection closed")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Выполняет SQL запрос с параметрами (thread-safe).

        Args:
            query: SQL запрос
            params: Параметры запроса

        Returns:
            Cursor с результатами

        Raises:
            RuntimeError: Если БД не инициализирована
        """
        if not self._conn:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            return cursor

    def execute_many(self, query: str, params_list: list) -> None:
        """
        Выполняет SQL запрос с множественными параметрами (thread-safe).

        Args:
            query: SQL запрос
            params_list: Список кортежей параметров

        Raises:
            RuntimeError: Если БД не инициализирована
        """
        if not self._conn:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        with self._lock:
            cursor = self._conn.cursor()
            cursor.executemany(query, params_list)
            self._conn.commit()

    def begin_transaction(self) -> None:
        """Начинает транзакцию (меняет isolation_level на DEFERRED)."""
        if not self._conn:
            raise RuntimeError("Database not initialized.")

        with self._lock:
            if self._conn.isolation_level is None:
                self._conn.isolation_level = "DEFERRED"
            self._conn.execute("BEGIN")

    def commit(self) -> None:
        """Фиксирует транзакцию."""
        if not self._conn:
            raise RuntimeError("Database not initialized.")

        with self._lock:
            self._conn.commit()

    def rollback(self) -> None:
        """Откатывает транзакцию."""
        if not self._conn:
            raise RuntimeError("Database not initialized.")

        with self._lock:
            self._conn.rollback()

    @property
    def connection(self) -> sqlite3.Connection:
        """Возвращает текущее соединение (для прямого доступа)."""
        if not self._conn:
            raise RuntimeError("Database not initialized.")
        return self._conn
