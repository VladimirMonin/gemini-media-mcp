# Отчёт: Исправление E2E тестов для Async Task System

**Дата:** 28 ноября 2025  
**Ветка:** `async_task`  
**Автор:** GitHub Copilot + Vladimir Monin

---

## 1. Исходное состояние

### Запущенные тесты

```
tests/e2e/test_full_system.py — 7 тестов
```

### Начальные проблемы

| Тест | Статус | Ошибка |
|------|--------|--------|
| `test_batch_images_rick_and_morty` | ❌ FAILED | "Batch has no tasks, skipping" + `'BatchJob' object has no attribute 'output_file_uri'` |
| `test_tts_queue_pickle_rick` | ⚠️ PASSED | Тест проходил, но аудиофайл был битый (не воспроизводился) |

---

## 2. Решённые проблемы

### 2.1. TTS: Битый аудиофайл (RAW PCM вместо WAV)

**Симптом:** Файл `pickle_rick.wav` создавался, но не воспроизводился в плеерах.

**Причина:** Gemini TTS API возвращает **RAW PCM данные** (24000 Hz, 16-bit, mono), а не готовый WAV файл. Код просто декодировал base64 и записывал байты напрямую — без WAV заголовка.

**Исправление в** `worker/processors/queue_processor.py`:

```python
# БЫЛО (неправильно):
audio_bytes = base64.b64decode(audio_base64)
with open(output_path, "wb") as f:
    f.write(audio_bytes)

# СТАЛО (правильно):
import wave
pcm_data = base64.b64decode(audio_base64)
with wave.open(output_path, "wb") as wav_file:
    wav_file.setnchannels(1)        # Mono
    wav_file.setsampwidth(2)        # 16-bit = 2 bytes
    wav_file.setframerate(24000)    # Gemini TTS sample rate
    wav_file.writeframes(pcm_data)
```

**Результат:** Аудиофайл теперь корректный WAV (343 KB), воспроизводится нормально.

---

### 2.2. Batch: "Batch has no tasks, skipping"

**Симптом:** При попытке отправить batch в Google API, система не находила задачи.

**Причина:** Использовался `db.get_pending_tasks()` с фильтрацией по статусу, вместо `db.get_tasks_by_batch()` который возвращает ВСЕ задачи пакета.

**Исправление в** `worker/processors/batch_processor.py`:

```python
# БЫЛО:
tasks_in_batch = [t for t in db.get_pending_tasks() if t["batch_id"] == batch_id]

# СТАЛО:
all_batch_tasks = db.get_tasks_by_batch(batch["id"])
tasks_in_batch = [t for t in all_batch_tasks if t.get("status") == "PENDING"]
```

---

### 2.3. Batch: `'BatchJob' object has no attribute 'output_file_uri'`

**Симптом:** После polling, при попытке скачать результаты batch, код падал.

**Причина:** Изначально использовался **inline режим** для batch запросов. Проблемы:

1. Для генерации изображений inline режим **не сохраняет результаты** после завершения
2. При повторном `client.batches.get()` поле `dest` возвращает `None`
3. Атрибут `output_file_uri` не существует — это была ошибка в коде

**Решение:** Переход на **file-based режим** согласно документации Google:

```python
# 1. Формируем JSONL файл с запросами
jsonl_lines = []
for task in tasks:
    request_obj = {
        "key": task["id"],  # Используем task_id для сопоставления
        "request": {
            "contents": [{"parts": [{"text": prompt}], "role": "user"}],
            "generation_config": {"responseModalities": ["TEXT", "IMAGE"]},
        },
    }
    jsonl_lines.append(json.dumps(request_obj))

# 2. Загружаем в Google File API
uploaded_file = client.files.upload(
    file=temp_file_path,
    config=types.UploadFileConfig(
        display_name=f"batch-{batch_id[:8]}",
        mime_type="application/jsonl",
    ),
)

# 3. Создаём batch с file source
result = client.batches.create(
    model=model,
    src=uploaded_file.name,  # Ссылка на файл, не inline
)

# 4. Удаляем входной файл из облака (очистка)
client.files.delete(name=uploaded_file.name)
```

**Получение результатов:**

```python
# Результаты в dest.file_name (JSONL файл)
output_file = google_batch.dest.file_name
file_content = client.files.download(file=output_file)

# Парсим по ключам (task_id)
for line in file_content.decode("utf-8").split("\n"):
    parsed = json.loads(line)
    task_id = parsed["key"]
    response = parsed["response"]
    # Извлекаем изображение из response["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
```

---

### 2.4. Safety Filter: Промпты с известными персонажами

**Симптом:** Одна из двух картинок генерировалась, вторая — нет (safety filter).

**Причина:** Промпты содержали "Rick Sanchez" и "Morty Smith" — Google отфильтровывал запросы с известными персонажами.

**Исправление в** `tests/e2e/conftest.py`:

```python
# БЫЛО:
"Rick Sanchez in his garage laboratory..."
"Morty Smith looking terrified..."

# СТАЛО:
"A mad scientist in a messy garage laboratory..."
"A nervous teenager floating through colorful interdimensional space..."
```

---

### 2.5. Windows: Кодировка cp1251 и эмодзи

**Симптом:** `UnicodeEncodeError: 'charmap' codec can't encode character`

**Причина:** Эмодзи в тестовых файлах (🧪, 🎵, ✅) не поддерживаются Windows cp1251.

**Исправление:** Удалены все эмодзи из `tests/e2e/conftest.py` и `tests/e2e/test_full_system.py`.

---

### 2.6. Очистка Google Cloud Storage

**Симптом:** Входные JSONL файлы накапливались в Google Cloud (квота 20GB).

**Причина:** После создания batch файл больше не нужен, но не удалялся.

**Исправление:**

```python
# Сразу после успешного создания batch
client.files.delete(name=uploaded_file.name)
```

**Примечание:** Файлы автоматически удаляются через 48 часов, но явное удаление экономит квоту.

---

## 3. Изменённые файлы

| Файл | Изменения |
|------|-----------|
| `worker/processors/queue_processor.py` | Исправлена функция `_save_tts_audio()` — теперь использует `wave` модуль для создания корректного WAV |
| `worker/processors/batch_processor.py` | Полностью переписана логика submit/retrieve: inline → file-based режим, исправлено извлечение результатов |
| `tests/e2e/conftest.py` | Убраны эмодзи, изменены промпты (без известных персонажей) |
| `tests/e2e/test_full_system.py` | Убраны эмодзи из строк |

---

## 4. Финальные результаты тестов

```
======================== test session starts ========================
platform win32 -- Python 3.13.5, pytest-9.0.1

tests/e2e/test_full_system.py::TestRickAndMortyE2E::test_batch_images_rick_and_morty 
   Batch created: 98f29d52-...
   Batch status: PENDING → SUBMITTED → PROCESSING → COMPLETED
   Completed: 2, Failed: 0
   Saved: rick_morty_1.png (1909 KB)
   Saved: rick_morty_2.png (1927 KB)
   PASSED

tests/e2e/test_full_system.py::TestRickAndMortyE2E::test_tts_queue_pickle_rick
   TTS task created: a1af90f6-...
   Task status: PENDING → PROCESSING → COMPLETED
   Saved: pickle_rick.wav (343 KB)
   PASSED

tests/e2e/test_full_system.py::TestCostVerification::test_batch_cost_estimation PASSED
tests/e2e/test_full_system.py::TestErrorHandlingE2E::test_invalid_aspect_ratio_rejected PASSED
tests/e2e/test_full_system.py::TestErrorHandlingE2E::test_invalid_voice_rejected PASSED
tests/e2e/test_full_system.py::TestErrorHandlingE2E::test_empty_prompts_rejected PASSED
tests/e2e/test_full_system.py::TestErrorHandlingE2E::test_text_too_long_rejected PASSED

======================== 7 passed in 289.34s (0:04:49) ========================
```

---

## 5. Ключевые выводы

### Что узнали о Gemini API

1. **TTS API** возвращает RAW PCM (24000 Hz, 16-bit, mono), НЕ готовый WAV
2. **Batch API inline режим** не сохраняет результаты — для изображений нужен file-based
3. **File-based Batch** использует `{"key": "...", "request": {...}}` формат для сопоставления
4. **Safety Filter** блокирует известных персонажей (Rick, Morty, etc.)
5. **Google Files API** имеет квоту 20GB и TTL 48 часов

### Архитектурные улучшения

1. **Детерминированная сортировка** задач по `(created_at, id)` для гарантии порядка
2. **Key-based сопоставление** вместо index-based (надёжнее при частичных ошибках)
3. **Явная очистка** облачных ресурсов после использования

---

## 6. Рекомендации на будущее

1. [ ] Добавить retry логику для transient ошибок (429, 503)
2. [ ] Реализовать exponential backoff для polling
3. [ ] Добавить мониторинг квоты Google Files API
4. [ ] Рассмотреть batch splitting для очень больших запросов (>100 изображений)
