"""
Database package for async task management.

Exports:
    DatabaseManager: Singleton для работы с БД задач
"""

from .manager import DatabaseManager

__all__ = ["DatabaseManager"]
