"""
OperationTypesRepository — репозиторий для работы с operation_types.

Обеспечивает:
- CRUD операции для справочника типов операций
- Получение execution_mode для операции
- Валидацию кодов операций
"""

from typing import Optional
from .connection_manager import ConnectionManager
from . import queries
from utils.logger import get_logger

logger = get_logger(__name__)


class OperationTypesRepository:
    """
    Репозиторий для работы со справочником operation_types.

    Содержит методы для чтения типов операций и их режимов выполнения.
    """

    def __init__(self, connection_manager: ConnectionManager):
        """
        Инициализация репозитория.

        Args:
            connection_manager: Менеджер соединения с БД
        """
        self.conn_mgr = connection_manager

    def get(self, code: str) -> Optional[dict]:
        """
        Получить operation_type по коду.

        Args:
            code: Код операции (например, 'IMG_GEN_BATCH')

        Returns:
            dict с полями operation_type, display_name, description, execution_mode
            или None если не найден
        """
        cursor = self.conn_mgr.execute(queries.GET_OPERATION_TYPE, (code,))
        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    def get_all(self) -> list[dict]:
        """
        Получить весь справочник operation_types.

        Returns:
            Список словарей с operation_type, display_name, execution_mode, etc.
        """
        cursor = self.conn_mgr.execute(queries.GET_ALL_OPERATION_TYPES)
        rows = cursor.fetchall()
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
        cursor = self.conn_mgr.execute(queries.GET_EXECUTION_MODE, (code,))
        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Unknown operation_type: {code}")

        return row[0]

    def exists(self, code: str) -> bool:
        """
        Проверить существование operation_type.

        Args:
            code: Код операции

        Returns:
            True если операция существует, иначе False
        """
        return self.get(code) is not None
