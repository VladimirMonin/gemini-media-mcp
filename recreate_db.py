"""Скрипт пересоздания базы данных с новой схемой."""

import os
from pathlib import Path
from database import DatabaseManager

db_path = Path("gemini_tasks.db")

if db_path.exists():
    print(f"Removing old DB: {db_path}")
    os.remove(db_path)
    print("OK: Old DB deleted")
else:
    print("INFO: Old DB not found")

print("Creating new DB...")
db = DatabaseManager()
db.initialize(str(db_path))
print(f"OK: New DB created: {db_path}")

op_types = db.get_all_operation_types()
print("\nOperation Types with rpm_limit:")
for op in op_types:
    rpm = op.get("rpm_limit")
    rpm_str = str(rpm) if rpm is not None else "NULL"
    print(
        f"  {op['operation_type']:25s} | mode={op['execution_mode']:12s} | rpm={rpm_str}"
    )

db.close()
print("\nDatabase ready!")
