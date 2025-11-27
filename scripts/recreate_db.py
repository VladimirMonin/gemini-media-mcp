"""
Пересоздание БД с новой схемой (rpm_limit).
"""

import os
from pathlib import Path
from database import DatabaseManager

# Проверить наличие старой БД
db_path = Path("gemini_tasks.db")

if db_path.exists():
    print(f"Removing old DB: {db_path}")
    os.remove(db_path)
    print("OK: Old DB deleted")
else:
    print("INFO: Old DB not found, creating new one")

# Создать новую БД
db = DatabaseManager()
db.initialize(str(db_path))

print(f"OK: New DB created: {db_path}")

# Проверить, что rpm_limit добавлен
op_types = db.get_all_operation_types()

print("\nOperation Types with rpm_limit:")
for op_type in op_types:
    rpm = op_type.get("rpm_limit")
    rpm_str = str(rpm) if rpm is not None else "NULL"
    print(
        f"  - {op_type['name']:25s} | mode={op_type['execution_mode']:12s} | rpm_limit={rpm_str}"
    )

db.close()
print("\nOK: Database ready!")
