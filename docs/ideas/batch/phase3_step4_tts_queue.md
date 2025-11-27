# Шаг 4: TTS Queue Integration — Интеграция голосового синтеза

**Время выполнения:** 2-3 часа  
**Сложность:** Средняя  
**Стоимость тестирования:** ~$0.01-0.05 (зависит от длины текста и голоса)

---

## Цель шага

Заменить мок в `process_local_queue_tasks()` на **реальную генерацию аудио** через Google Gemini TTS API. После этого шага:

- Задачи типа `TTS_GEN_QUEUE` обрабатываются реальным синтезом речи
- Аудио файлы сохраняются в формате WAV
- Применяется rate limiting (1.8 секунды между запросами)
- Ошибки корректно обрабатываются (невалидный голос, слишком длинный текст)

---

## Что происходит сейчас (Фаза 2)

**Файл:** `worker/processors/queue_processor.py`  
**Функция:** `process_local_queue_tasks()`

```python
def process_local_queue_tasks(db: DatabaseManager) -> int:
    """ЗАГЛУШКА для Фазы 2."""
    tasks = db.get_pending_local_queue_tasks(limit=1)
    
    if not tasks:
        return 0
    
    task = tasks[0]
    time.sleep(2)  # Эмуляция TTS
    db.mark_task_completed(task["id"], local_path=f"/fake/{task['id']}.wav")
    logger.debug(f"[MOCK] Processed TTS task {task['id']}")
    
    return 1
```

**Проблема:**

- `time.sleep(2)` вместо реального синтеза
- Файлы не создаются
- Нет валидации входных данных (prompt, voice, model)

---

## Структура задачи TTS_GEN_QUEUE

**В БД хранится:**

```python
task = {
    "id": "uuid-here",
    "operation_type": "TTS_GEN_QUEUE",
    "input_payload": {
        "text": "Hello world",
        "voice": "Puck",  # Необязательно
        "model": "gemini-2.5-flash-preview-tts"  # Необязательно
    },
    "target_path": "/path/to/output.wav"
}
```

**Обязательные поля:**

- `input_payload.text` — текст для синтеза

**Необязательные поля (с дефолтами):**

- `input_payload.voice` → `"Puck"` (по умолчанию)
- `input_payload.model` → `"gemini-2.5-flash-preview-tts"` (по умолчанию)

---

## Как работает Gemini TTS API

### Синхронный синтез речи

**API вызов:**

```python
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents="Hello world",
    config={
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {"prebuilt_voice_config": {"voice_name": "Puck"}}
        }
    }
)
```

**Что возвращается:**

```python
response.candidates[0].content.parts[0].inline_data
# {
#   "mime_type": "audio/wav",
#   "data": "UklGRiQAAABXQVZFZm10..."  # base64
# }
```

---

## Что нужно сделать

### 1. Получить задачи из очереди

**Лимит:** Обрабатывать по 1 задаче за раз (rate limiting)

```python
tasks = db.get_pending_local_queue_tasks(limit=1)

if not tasks:
    return 0

task = tasks[0]
```

---

### 2. Извлечь параметры из input_payload

**С дефолтами:**

```python
payload = task["input_payload"]

text = payload.get("text")
voice = payload.get("voice", "Puck")
model = payload.get("model", "gemini-2.5-flash-preview-tts")
```

**Валидация:**

```python
if not text:
    raise ValueError("Missing 'text' in input_payload")

if len(text) > 5000:
    raise ValueError("Text too long (max 5000 characters)")
```

---

### 3. Вызвать TTS API

**Синтез речи:**

```python
response = client.models.generate_content(
    model=model,
    contents=text,
    config={
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": voice}
            }
        }
    }
)
```

---

### 4. Извлечь аудио данные

**Путь к данным:**

```python
audio_part = response.candidates[0].content.parts[0]

if not hasattr(audio_part, "inline_data"):
    raise ValueError("No audio data returned")

audio_data_base64 = audio_part.inline_data.data
mime_type = audio_part.inline_data.mime_type  # "audio/wav"
```

---

### 5. Сохранить аудио файл

**Декодирование base64:**

```python
import base64
from pathlib import Path

def save_audio(task_id: str, base64_data: str, target_path: str) -> str:
    """
    Сохранить аудио из base64.
    
    Args:
        task_id: UUID задачи
        base64_data: Base64 строка
        target_path: Путь из задачи или None
    
    Returns:
        Абсолютный путь к сохраненному файлу
    """
    # Декодировать base64
    audio_bytes = base64.b64decode(base64_data)
    
    # Определить путь
    if target_path:
        local_path = Path(target_path)
    else:
        output_dir = Path("output_audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        local_path = output_dir / f"{task_id}.wav"
    
    # Создать директории
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Записать файл
    with open(local_path, "wb") as f:
        f.write(audio_bytes)
    
    return str(local_path.absolute())
```

---

### 6. Обновить задачу в БД

**Успех:**

```python
db.mark_task_completed(task["id"], local_path=local_path)
```

**Ошибка:**

```python
db.mark_task_failed(task["id"], error=str(e))
```

---

### 7. Rate Limiting

**Почему важно:**

- Google TTS имеет лимиты: **20 запросов в минуту**
- Слишком частые запросы → `429 Too Many Requests`

**Решение:**

```python
import time

RATE_LIMIT_DELAY = 1.8  # 60 секунд / 20 запросов = 3 секунды (запас: 1.8)

# После каждой задачи
time.sleep(RATE_LIMIT_DELAY)
```

**Альтернатива (более точная):**

```python
from time import time

last_request_time = 0

def process_tts_task(task):
    global last_request_time
    
    # Проверить, сколько времени прошло с последнего запроса
    elapsed = time() - last_request_time
    
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    
    # Вызвать TTS API
    # ...
    
    last_request_time = time()
```

---

## Полный алгоритм

```
1. Получить 1 задачу из очереди
   └─ db.get_pending_local_queue_tasks(limit=1)

2. Извлечь параметры
   └─ text, voice, model (с дефолтами)

3. Валидация
   └─ text не пустой
   └─ text длиной < 5000 символов

4. Вызвать TTS API
   └─ client.models.generate_content(...)

5. Извлечь аудио данные
   └─ response.candidates[0].content.parts[0].inline_data.data

6. Сохранить аудио файл
   └─ Декодировать base64
   └─ Записать в target_path или output_audio/{task_id}.wav

7. Обновить задачу
   └─ db.mark_task_completed(task_id, local_path)

8. Rate Limiting
   └─ time.sleep(1.8 секунд)

9. Вернуть количество обработанных задач (1)
```

---

## Пример реализации (концепт)

**Файл:** `worker/processors/queue_processor.py`

```python
import base64
import time
from pathlib import Path
from google import genai

def process_local_queue_tasks(db: DatabaseManager) -> int:
    """
    Обработка TTS задач из очереди.
    
    Returns:
        Количество обработанных задач (0 или 1)
    """
    # 1. Получить 1 задачу
    tasks = db.get_pending_local_queue_tasks(limit=1)
    
    if not tasks:
        return 0
    
    task = tasks[0]
    
    try:
        # 2. Извлечь параметры
        payload = task["input_payload"]
        text = payload.get("text")
        voice = payload.get("voice", "Puck")
        model = payload.get("model", "gemini-2.5-flash-preview-tts")
        target_path = task.get("target_path")
        
        # 3. Валидация
        if not text:
            raise ValueError("Missing 'text' in input_payload")
        
        if len(text) > 5000:
            raise ValueError(f"Text too long: {len(text)} > 5000")
        
        # 4. Вызвать TTS API
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model=model,
            contents=text,
            config={
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {"voice_name": voice}
                    }
                }
            }
        )
        
        # 5. Извлечь аудио данные
        audio_part = response.candidates[0].content.parts[0]
        
        if not hasattr(audio_part, "inline_data"):
            raise ValueError("No audio data returned from TTS API")
        
        audio_data_base64 = audio_part.inline_data.data
        
        # 6. Сохранить аудио файл
        local_path = _save_audio(task["id"], audio_data_base64, target_path)
        
        # 7. Обновить задачу
        db.mark_task_completed(task["id"], local_path=local_path)
        logger.info(f"TTS task {task['id']} completed: {local_path}")
        
        # 8. Rate Limiting (динамически из БД)
        delay = _get_rate_limit_delay(db, "TTS_GEN_QUEUE")
        logger.debug(f"Rate limit delay: {delay:.1f} seconds")
        time.sleep(delay)
        
        return 1
    
    except Exception as e:
        logger.error(f"TTS task {task['id']} failed: {e}")
        db.mark_task_failed(task["id"], error=str(e))
        return 0


def _get_rate_limit_delay(db: DatabaseManager, operation_type: str) -> float:
    """
    Получить задержку из operation_types.
    
    Returns:
        Задержка в секундах (60 / rpm_limit)
    """
    op_type = db.get_operation_type(operation_type)
    rpm_limit = op_type.get("rpm_limit", 3)  # Дефолт: Free Tier (3 RPM)
    
    return 60.0 / rpm_limit


def _save_audio(task_id: str, base64_data: str, target_path: str = None) -> str:
    """Сохранить аудио из base64."""
    audio_bytes = base64.b64decode(base64_data)
    
    if target_path:
        local_path = Path(target_path)
    else:
        output_dir = Path("output_audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        local_path = output_dir / f"{task_id}.wav"
    
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(local_path, "wb") as f:
        f.write(audio_bytes)
    
    return str(local_path.absolute())
```

---

## Обработка ошибок

### Ошибка 1: "Invalid voice name"

**Причина:** Невалидный голос в `input_payload.voice`

**Доступные голоса:**

- Aoede, Charon, Fenrir, Kore, Puck (английский)
- Другие языки: см. `docs/gem/voices.md`

**Решение:**

```python
VALID_VOICES = ["Aoede", "Charon", "Fenrir", "Kore", "Puck"]

if voice not in VALID_VOICES:
    raise ValueError(f"Invalid voice: {voice}. Valid: {VALID_VOICES}")
```

---

### Ошибка 2: Rate Limit Exceeded

**Причина:** Слишком частые запросы к TTS API

**Решение:**

```python
try:
    response = client.models.generate_content(...)
except RateLimitError:
    logger.warning("Rate limit exceeded, will retry in next cycle")
    # НЕ помечать задачу как FAILED — она обработается в следующем цикле
    return 0
```

---

### Ошибка 3: "Text is empty"

**Причина:** Пустой `input_payload.text`

**Решение:**

```python
if not text or text.strip() == "":
    raise ValueError("Text is empty")
```

---

### Ошибка 4: Файл не сохраняется

**Причина:** Нет прав на запись или полный диск

**Решение:**

```python
try:
    with open(local_path, "wb") as f:
        f.write(audio_bytes)
except IOError as e:
    raise RuntimeError(f"Failed to save audio file: {e}")
```

---

## Тестирование

### Вариант 1: Локальное тестирование (платное, ~$0.01)

**Создать тестовую задачу:**

```python
# scripts/test_tts_queue.py

from database import DatabaseManager
from worker.processors.queue_processor import process_local_queue_tasks
from uuid import uuid4
import json

db = DatabaseManager()
db.initialize()

# Создать TTS задачу
task_id = str(uuid4())
db.create_task(
    task_id=task_id,
    operation_type="TTS_GEN_QUEUE",
    input_payload=json.dumps({
        "text": "Hello from Gemini TTS!",
        "voice": "Puck"
    }),
    target_path=f"output_audio/{task_id}.wav"
)

# Обработать
processed = process_local_queue_tasks(db)
print(f"Processed: {processed}")

# Проверить результат
task = db.get_task(task_id)
print(f"Status: {task['status']}")
print(f"Local path: {task.get('local_path')}")

# Проверить файл
import os
assert os.path.exists(task["local_path"]), "Audio file not found!"
print(f"✅ Audio saved: {task['local_path']}")
```

**Стоимость:** ~$0.01 (зависит от длины текста)

---

### Вариант 2: Интеграция с Worker

**Полный цикл:**

```python
# scripts/test_worker_tts.py

from database import DatabaseManager
from worker import WorkerManager
from uuid import uuid4
import json
import time

db = DatabaseManager()
db.initialize()

# Создать 3 TTS задачи
for i in range(3):
    task_id = str(uuid4())
    db.create_task(
        task_id=task_id,
        operation_type="TTS_GEN_QUEUE",
        input_payload=json.dumps({
            "text": f"Test message number {i+1}",
            "voice": "Puck"
        })
    )

# Запустить воркер
worker = WorkerManager(db, tick_interval=5)  # Быстрый режим
worker.start()

# Ждать завершения (max 2 минуты)
timeout = 120
start = time.time()

while time.time() - start < timeout:
    pending = db.get_pending_local_queue_tasks(limit=10)
    print(f"Pending tasks: {len(pending)}")
    
    if len(pending) == 0:
        print("✅ All tasks completed!")
        break
    
    time.sleep(5)

worker.stop(timeout=5)
```

**Ожидаемое время:** ~10-15 секунд (3 задачи × 1.8 сек rate limit + API время)

---

## Проверка готовности

### Критерии успеха

- ✅ Функция вызывает `client.models.generate_content()` с TTS конфигом
- ✅ Аудио данные декодируются из base64
- ✅ Файлы сохраняются в WAV формате
- ✅ Применяется rate limiting (1.8 сек между запросами)
- ✅ Задачи переходят в COMPLETED с local_path
- ✅ Ошибки корректно обрабатываются (невалидный голос, пустой текст)

### Проверочный тест

```bash
# 1. Запустить тест
python scripts/test_tts_queue.py

# 2. Проверить БД
sqlite3 gemini_tasks.db "SELECT status, local_path FROM tasks WHERE operation_type='TTS_GEN_QUEUE';"

# Ожидаемый результат:
# COMPLETED|C:\PY\gemini-media-mcp\output_audio\uuid.wav

# 3. Проверить файл
ls -lh output_audio/
# Должен быть WAV файл

# 4. Прослушать аудио
# (в Windows: start output_audio/*.wav)
```

---

## Следующий шаг

После успешной интеграции TTS переходим к **Шагу 5: MCP Tools Integration** → создание инструментов для агента.

**Файл:** `phase3_step5_mcp_tools.md`

---

**Версия:** 1.0  
**Дата:** 27 ноября 2025 г.
