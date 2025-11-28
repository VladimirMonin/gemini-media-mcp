"""E2E Test Configuration — Real API, Real Files, Real Fun.

Этот conftest.py настраивает изолированное окружение для E2E тестов:
- Отдельная БД с WAL режимом (конкурентный доступ)
- Папка output для результатов (не удаляется после теста)
- Реальный WorkerManager с быстрым tick_interval
- Маркер @pytest.mark.paid для защиты от случайного запуска
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Устанавливаем переменные окружения ДО импорта модулей
# чтобы config.py подхватил правильные пути
E2E_OUTPUT_DIR = Path(__file__).parent / "output"


@pytest.fixture(scope="session", autouse=True)
def e2e_output_dir() -> Generator[Path, None, None]:
    """
    Создаёт папку tests/e2e/output/ для результатов тестов.

    Очищает папку в начале сессии, но НЕ удаляет после.
    Так ты сможешь посмотреть что получилось!
    """
    # Очистить папку если существует
    if E2E_OUTPUT_DIR.exists():
        shutil.rmtree(E2E_OUTPUT_DIR)

    # Создать свежую
    E2E_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (E2E_OUTPUT_DIR / "images").mkdir(exist_ok=True)
    (E2E_OUTPUT_DIR / "audio").mkdir(exist_ok=True)

    print(f"\n[DIR] E2E Output Directory: {E2E_OUTPUT_DIR}")

    yield E2E_OUTPUT_DIR

    # НЕ удаляем после — пусть пользователь посмотрит результаты!
    print(f"\n[OK] Results saved to: {E2E_OUTPUT_DIR}")


@pytest.fixture(scope="function")
def e2e_db(tmp_path: Path, monkeypatch):
    """
    Изолированная БД для E2E теста с WAL режимом.

    WAL (Write-Ahead Logging) нужен для конкурентного доступа:
    - Test script читает статус (SELECT)
    - Worker пишет обновления (UPDATE)
    - Server создаёт задачи (INSERT)

    Без WAL получим "database is locked".

    ВАЖНО: monkeypatch подменяет singleton в batch_tools.py,
    чтобы инструменты использовали тестовую БД!
    """
    # Reset singleton для изоляции тестов
    from database.manager import DatabaseManager

    DatabaseManager._instance = None

    # Создать новую БД во временной папке
    db_path = tmp_path / "e2e_test.db"

    db = DatabaseManager()
    db.initialize(str(db_path))

    # Включить WAL для конкурентного доступа
    db.execute_pragma("journal_mode=WAL")

    # КРИТИЧНО: Патчим singleton в batch_tools.py!
    # Иначе инструменты будут использовать свой неинициализированный экземпляр
    import tools.batch_tools as batch_tools_module

    monkeypatch.setattr(batch_tools_module, "db", db)

    print(f"[DB] E2E Database: {db_path} (WAL mode)")
    print("[PATCH] Patched batch_tools.db -> test database")

    yield db

    # Cleanup
    db.close()
    DatabaseManager._instance = None


@pytest.fixture(scope="function")
def e2e_worker(e2e_db):
    """
    Реальный WorkerManager с быстрым tick_interval для E2E.

    tick_interval=5 сек — чтобы тесты не ждали 30 сек между проверками.
    """
    from worker.manager import WorkerManager

    worker = WorkerManager(e2e_db, tick_interval=5)
    worker.start()

    print("[WORKER] E2E Worker started (tick_interval=5s)")

    yield worker

    # Graceful shutdown
    worker.stop(timeout=15)
    print("[WORKER] E2E Worker stopped")


@pytest.fixture
def rick_and_morty_prompts() -> list[str]:
    """
    Креативные промпты для batch image generation.

    Минимум 2 картинки — это порог для batch API.
    Используем нейтральные описания без известных персонажей,
    чтобы избежать safety filter от Google.
    """
    return [
        (
            "A mad scientist in a messy garage laboratory, surrounded by bubbling "
            "green portals and strange gadgets, dramatic lighting, cartoon style, "
            "highly detailed, vibrant neon colors"
        ),
        (
            "A nervous teenager floating through colorful interdimensional space, "
            "surrounded by friendly alien creatures and cosmic nebulae, "
            "cartoon style, dynamic pose, galaxies in background"
        ),
    ]


@pytest.fixture
def rick_tts_text() -> str:
    """
    Текст для TTS теста.

    Короткий текст чтобы не тратить много денег.
    """
    return (
        "Listen, I turned myself into a pickle! I am Pickle! This is amazing science!"
    )


def pytest_configure(config):
    """Регистрация кастомного маркера paid."""
    config.addinivalue_line(
        "markers", "paid: marks tests as requiring real API calls (costs money!)"
    )
