"""
Скрипт для исследования структуры ответов Google Batch API.
Используется для отладки inline responses.
"""

import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai
import config

client = genai.Client(api_key=config.GEMINI_API_KEY)
batches = list(client.batches.list())

print("=== Available batches ===")
for i, batch in enumerate(batches[:5]):
    print(f"{i}: {batch.name} - {batch.state}")

# Найдём успешный батч
succeeded = [b for b in batches if str(b.state) == "JobState.JOB_STATE_SUCCEEDED"]
if not succeeded:
    print("\nNo succeeded batches found!")
    exit(1)

batch = succeeded[0]
print(f"\n=== Analyzing batch: {batch.name} ===")
print(f"State: {batch.state}")
print(f"\nAll batch attrs: {[a for a in dir(batch) if not a.startswith('_')]}")

# Попробуем to_json_dict
try:
    json_dict = batch.to_json_dict()
    print(f"\nJSON dict keys: {json_dict.keys()}")
    print(f"\nFull JSON:\n{json_dict}")
except Exception as e:
    print(f"to_json_dict failed: {e}")
