"""
Демонстрация работы воркера с реальной БД.

Создаёт 5 тестовых задач и запускает воркер на 60 секунд.
Показывает прогресс в реальном времени.
"""

from database import DatabaseManager
from worker import WorkerManager
from uuid import uuid4
import time


def main():
    print("=" * 60)
    print("Demo: Worker Engine")
    print("=" * 60)

    # Инициализация
    db = DatabaseManager()
    db.initialize()

    # Создать тестовый batch с задачами
    batch_id = str(uuid4())

    print(f"\n[1] Creating test batch {batch_id[:8]}...")

    # Добавить тестовый operation_type для local_queue
    db._conn.execute("""
        INSERT OR IGNORE INTO operation_types (operation_type, display_name, execution_mode, description)
        VALUES ('TTS_QUEUE', 'TTS Local Queue', 'local_queue', 'Test operation for local queue')
    """)
    db._conn.commit()

    db.create_batch_with_tasks(
        batch_id=batch_id,
        operation_type="TTS_QUEUE",  # local_queue режим
        tasks=[
            {
                "task_id": str(uuid4()),
                "input_payload": {"script": f"Test audio {i}", "voice": "Kore"},
                "target_path": f"output/test_{i}.wav",
                "search_keywords": f"test audio {i}",
            }
            for i in range(5)
        ],
    )
    print(f"✅ Created 5 tasks")

    # Запустить воркер
    print(f"\n[2] Starting worker (tick_interval=10s)...")
    worker = WorkerManager(db, tick_interval=10)
    worker.start()
    print("✅ Worker started")

    # Мониторинг прогресса
    print(f"\n[3] Monitoring progress for 60 seconds...")
    print("-" * 60)

    for i in range(6):  # 60 секунд / 10 секунд = 6 итераций
        time.sleep(10)

        progress = db.get_batch_progress(batch_id)
        stats = db.get_stats()

        print(
            f"T+{(i + 1) * 10}s | Batch: {progress['completed']}/{progress['total']} completed | "
            f"DB: {stats['pending']} pending, {stats['processing']} processing"
        )

    print("-" * 60)

    # Остановить воркер
    print(f"\n[4] Stopping worker...")
    worker.stop()
    print("✅ Worker stopped")

    # Финальная статистика
    print(f"\n[5] Final stats:")
    final_progress = db.get_batch_progress(batch_id)
    print(f"   Completed: {final_progress['completed']}")
    print(f"   Failed: {final_progress['failed']}")
    print(f"   Pending: {final_progress['pending']}")

    db.close()
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
