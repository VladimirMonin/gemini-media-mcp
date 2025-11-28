# Phase 3 Step 4: TTS Queue Integration — Completion Report

**Дата завершения:** 28 ноября 2025 г.  
**Статус:** ✅ ЗАВЕРШЁН  
**Тесты:** 89 passed, 3 skipped

---

## Цель шага

Заменить мок в `process_local_queue_tasks()` на **реальную генерацию аудио** через Google Gemini TTS API с учётом архитектурных улучшений, внедрённых в предыдущих шагах.

---

## Архитектурные улучшения

В процессе реализации были применены три ключевых улучшения относительно исходного плана:

| Аспект | Было в документе | Стало |
|--------|------------------|-------|
| **Rate Limiting** | `RATE_LIMIT_DELAY = 1.8` хардкод | `60.0 / rpm_limit` динамически из `operation_types` |
| **Имя модели** | `"gemini-2.5-flash-preview-tts"` хардкод | `config.TTS_MODELS["flash"]` из конфига |
| **Путь файлов** | `output_audio/{task_id}.wav` | `media/tts/{task_id}.wav` (единообразие) |

**Обоснование:**

- Rate Limiting из БД позволяет менять лимиты без изменения кода
- Модели в config.py — единый источник правды при обновлениях Google API
- Структура `media/tts/` согласована с `media/generated/` для batch-изображений

---

## Что реализовано

### 1. Конфигурация (`config.py`)

```python
# TTS Models
TTS_MODELS = {
    "flash": "gemini-2.5-flash-preview-tts",
    "pro": "gemini-2.5-pro-preview-tts",
}
DEFAULT_TTS_MODEL = "flash"

# Output directory
OUTPUT_TTS_DIR = os.path.join(_PROJECT_ROOT, "media", "tts")
```

### 2. База данных

**`database/seed_data.py`** — новый operation_type:

```python
("TTS_GEN_QUEUE", "TTS Generation (Queue)", "local_queue", 
 "Генерация аудио через локальную очередь", 10)  # 10 RPM
```

**`database/queries.py`** — новый запрос с JOIN:

```sql
SELECT t.* FROM tasks t
JOIN operation_types ot ON t.operation_type = ot.operation_type
WHERE t.status = 'PENDING' AND ot.execution_mode = 'local_queue'
ORDER BY t.created_at ASC LIMIT ?
```

**`database/tasks_repository.py`** — метод `get_pending_local_queue(limit)`

**`database/manager.py`** — обёртка `get_pending_local_queue_tasks(limit)`

### 3. Queue Processor (`worker/processors/queue_processor.py`)

Полная реализация с разделением ответственности:

| Функция | Назначение |
|---------|------------|
| `_get_rate_limit_delay(db, op_type)` | Вычисление задержки из `rpm_limit` в БД |
| `_validate_tts_payload(payload)` | Валидация text, voice, model_type с дефолтами |
| `_generate_tts(text, voice, model_type)` | Вызов Gemini TTS API, возврат base64 |
| `_save_tts_audio(task_id, audio_base64, target_path)` | Сохранение WAV в `media/tts/` |
| `process_local_queue_tasks(db, mock_mode)` | Основной процессор с обработкой ошибок |

**Ключевые особенности:**

- Параметр `mock_mode=True` для unit-тестов без API
- Динамический rate limiting: `delay = 60.0 / rpm_limit`
- Валидация текста: не пустой, ≤5000 символов
- Автоматическое создание директорий

### 4. Тесты (`tests/batch/test_tts_queue.py`)

**20 новых тестов:**

| Класс | Тесты | Покрытие |
|-------|-------|----------|
| `TestValidateTTSPayload` | 8 | Валидация payload, дефолты, ошибки |
| `TestRateLimitDelay` | 3 | Динамический rate limit из БД |
| `TestSaveTTSAudio` | 3 | Сохранение файлов, создание директорий |
| `TestProcessLocalQueueTasks` | 4 | Mock mode, пустая очередь, ошибки |
| `TestProcessLocalQueueTasksWithMockedAPI` | 2 | Интеграция с моком Gemini API |

**Исправленные тесты:**

- `test_database.py::test_seed_data_loaded` — обновлено количество op_types (10 → 11)
- `test_worker.py::test_local_queue_processes_one_task` — мок Gemini API, исправлен payload

---

## Блокирующий характер TTS

Как обсуждалось в плане, `time.sleep()` в queue_processor блокирует весь воркер:

```python
# После обработки TTS задачи
delay = _get_rate_limit_delay(db, "TTS_GEN_QUEUE")  # 6 секунд для 10 RPM
time.sleep(delay)
```

**Trade-off:** Пока идёт активная озвучка длинной книги, polling batch-изображений замедляется. Это осознанное решение в пользу простоты однопоточной архитектуры.

---

## Структура файлов

```
config.py                           # +TTS_MODELS, +OUTPUT_TTS_DIR
database/
  seed_data.py                      # +TTS_GEN_QUEUE
  queries.py                        # +GET_PENDING_LOCAL_QUEUE_TASKS
  tasks_repository.py               # +get_pending_local_queue()
  manager.py                        # +get_pending_local_queue_tasks()
worker/processors/
  queue_processor.py                # Полная реализация TTS
tests/batch/
  test_tts_queue.py                 # 20 новых тестов
```

---

## Результаты тестирования

```
================================ test session starts ================================
collected 91 items / 1 skipped

tests/batch/test_retrieval.py         9 passed
tests/batch/test_tts_queue.py        20 passed
tests/test_backup_manager.py         11 passed
tests/test_batch_polling.py           5 passed, 2 skipped (E2E)
tests/test_batch_submission.py        5 passed
tests/test_database.py               23 passed
tests/test_worker.py                  8 passed

========================== 89 passed, 3 skipped in 36.92s ===========================
```

---

## Следующий шаг

**Phase 3 Step 5: MCP Tools Integration**

Создание MCP-инструментов для агента:

- `queue_tts(text, voice, model_type)` — постановка TTS в очередь
- `check_task_status(task_id)` — проверка статуса задачи
- `get_task_result(task_id)` — получение результата

---

## Lessons Learned

1. **Mock time.sleep осторожно** — патч `time.sleep` ломает `threading.Event.wait()` в воркере
2. **JOIN для execution_mode** — эффективнее фильтровать в SQL, чем в Python
3. **Согласованность путей** — `media/tts/` и `media/generated/` упрощают backup и cleanup

---

**Версия:** 1.0  
**Автор:** GitHub Copilot + Vladimir Monin  
**Дата:** 28 ноября 2025 г.
