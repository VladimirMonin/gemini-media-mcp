# Phase 3 Step 3: Batch Retrieval - Completion Report

## Статус: ✅ ЗАВЕРШЕНО

**Дата:** 2025-11-28  
**Тесты:** 69 passed, 3 skipped  

---

## 🎯 Что было реализовано

### 1. Функция `retrieve_completed_batches()`

Основная функция для обработки завершённых батчей (~170 строк):

```python
def retrieve_completed_batches(db: DatabaseManager) -> int:
```

**Логика работы:**

1. Получает батчи со статусом `COMPLETED` из БД
2. Для каждого батча получает задачи, сортирует детерминированно
3. **Mock Mode:** Генерирует тестовые PNG для всех задач
4. **Real API Mode:** Скачивает JSONL, парсит построчно, извлекает base64
5. **Критическая валидация:** `len(results) != len(tasks)` → весь батч FAILED
6. Сохраняет файлы с шардингом: `media/generated/{batch_id}/{task_id}.png`
7. Обновляет статусы в БД атомарно

### 2. Хелпер `_extract_image_data()`

Извлекает base64 из ответа Gemini:

```python
def _extract_image_data(response: Dict) -> Optional[str]:
    # Обрабатывает структуру: response.candidates[0].content.parts[0].inline_data.data
```

### 3. Хелпер `_save_image()`

Сохраняет изображение с шардингом:

```python
def _save_image(base64_data: str, batch_id: int, task_id: int) -> str:
    # Путь: media/generated/{batch_id}/{task_id}.png
```

### 4. Детерминированная сортировка

Добавлена в обе функции для идентичного порядка задач:

```python
tasks.sort(key=lambda t: (t["created_at"], t["id"]))
```

---

## 🐛 Решённые проблемы

### 1. Неправильные имена методов БД

**Проблема:** Код использовал `mark_task_completed()` вместо `update_task_completed()`

**Решение:** Исправлены все вызовы на правильные методы:

- `update_task_completed(task_id, output_path)`
- `update_task_failed(task_id, error_message)`
- `update_batch_failed(batch_id, error_message)`

### 2. httpx patching в тестах

**Проблема:** `monkeypatch.setattr("httpx.get", ...)` не работал, потому что httpx импортировался на уровне модуля.

**Решение:**

```python
# В batch_processor.py (строка 18):
import httpx  # ВАЖНО: на уровне модуля для корректного patching

# В тестах:
monkeypatch.setattr(bp.httpx, "get", MockResponse)
```

### 3. Битая фикстура broken_jsonl

**Проблема:** В JSON отсутствовала закрывающая скобка `]` для массива candidates.

**Решение:** Исправлена структура JSON:

```python
# Было: "}]}}"  
# Стало: "}]]}}"
```

### 4. Несоответствие ожиданий в test_worker

**Проблема:** `test_local_queue_ignores_batch_tasks` ожидал статус `SUBMITTED`, но после Step 3 задачи корректно проходят до `COMPLETED`.

**Решение:** Обновлён тест с пояснительным комментарием:

```python
# В mock режиме batch задачи проходят полный цикл:
# PENDING → SUBMITTED → PROCESSING → COMPLETED
assert task["status"] == "COMPLETED"
```

---

## 📊 Тестовое покрытие

### Итерация 1: Заглушки (проблема)

Изначально тесты были написаны как заглушки с `pytest.skip("Waiting for...")`:

- 10 тестов, из них 7 пропущено
- **Проблема:** "Потёмкинская деревня" — тесты не проверяли реальную логику

### Итерация 2: Реальные тесты (решение)

Создан отдельный пакет `tests/batch/` с полноценными тестами:

```
tests/batch/
├── __init__.py          # Документация пакета
├── conftest.py          # Общие фикстуры (temp_db, mock_mode, JSONL fixtures)
└── test_retrieval.py    # 9 реальных тестов для Step 3
```

### Retrieval тесты (9 passed)

| Тест | Статус | Описание |
|------|--------|----------|
| `test_sorting_by_created_at_and_id` | ✅ PASSED | Детерминированная сортировка |
| `test_length_mismatch_fails_entire_batch` | ✅ PASSED | **Паранойя-режим** (критический!) |
| `test_processes_batch_without_api` | ✅ PASSED | Mock режим создаёт файлы на диске |
| `test_files_saved_in_batch_folders` | ✅ PASSED | Шардинг по batch_id (fallback) |
| `test_only_completed_batches_processed` | ✅ PASSED | Фильтрация по статусу COMPLETED |
| `test_invalid_json_fails_batch` | ✅ PASSED | Битый JSON → batch FAILED |
| `test_missing_output_file_uri_skips_batch` | ✅ PASSED | Race condition handling |
| `test_task_error_in_jsonl_marks_task_failed` | ✅ PASSED | Safety Filter в ответе |
| `test_invalid_base64_marks_task_failed` | ✅ PASSED | Битый base64 → task FAILED |

### Полный набор тестов

- **tests/batch/test_retrieval.py:** 9 passed
- **test_batch_submission.py:** 5 passed
- **test_batch_polling.py:** 8 passed
- **test_database.py:** 23 passed
- **test_worker.py:** 8 passed
- **Прочие:** 16 passed, 3 skipped (E2E с реальным API)
- **Всего:** 69 passed, 3 skipped

---

## 🏗️ Архитектурные решения

### 1. Paranoia Mode для индексной валидации

Если количество результатов не совпадает с количеством задач — весь батч помечается как FAILED:

```python
if len(results) != len(tasks):
    error_msg = f"Количество результатов ({len(results)}) != количеству задач ({len(tasks)})"
    db.update_batch_failed(batch["id"], error_msg)
    for task in tasks:
        db.update_task_failed(task["id"], "Batch index validation failed")
```

### 2. Атомарность операций

1. Сначала сохраняем файл на диск
2. Только потом обновляем БД
3. При ошибке сохранения — задача FAILED, но остальные продолжают

### 3. Mock Mode поддержка

Mock режим (google_batch_id начинается с `batches/mock_`) автоматически генерирует тестовые PNG без реального API.

---

## 📁 Изменённые файлы

1. **worker/processors/batch_processor.py** (+170 строк)
   - `import httpx` (строка 18)
   - Детерминированная сортировка (строка 117)
   - `retrieve_completed_batches()` (строки 330-500)
   - `_extract_image_data()` (строки 500-530)
   - `_save_image()` (строки 540-590)

2. **tests/batch/** (НОВЫЙ ПАКЕТ)
   - `__init__.py` — документация пакета
   - `conftest.py` — общие фикстуры (temp_db, mock_mode, JSONL fixtures)
   - `test_retrieval.py` — 9 реальных тестов для Step 3

3. **tests/test_batch_retrieval.py** (УДАЛЁН)
   - Заменён на `tests/batch/test_retrieval.py`

4. **tests/test_worker.py** (1 исправление)
   - `test_local_queue_ignores_batch_tasks` → COMPLETED

---

## 🔧 Технические детали тестов

### Проблема с target_path

**Проблема:** SQLite constraint `NOT NULL` на `tasks.target_path`

**Решение:** Все тесты теперь указывают валидный `target_path`:

```python
{"task_id": tid, "input_payload": {...}, "target_path": f"/tmp/{tid}.png"}
```

### Проблема с шардингом на Windows

**Проблема:** Windows создаёт папки по любому пути (`mkdir -p` эквивалент)

**Решение:** Использовать путь с запрещёнными символами для гарантированного fallback:

```python
invalid_path = "Z:\\<invalid>|path*"  # Вызывает fallback на media/generated/
```

---

## 🔜 Следующие шаги (Step 4: TTS Queue)

Согласно документации, Step 4 добавит:

1. **Отдельную очередь для TTS запросов**
2. **Rate limiting** для соблюдения квот
3. **Приоритизацию** real-time vs batch
4. **Retry логику** с exponential backoff

---

## ✅ Критерии завершения Step 3

- [x] Функция `retrieve_completed_batches()` реализована
- [x] Детерминированная сортировка в обоих направлениях
- [x] Критическая валидация длины (paranoia mode)
- [x] Шардинг файлов по batch_id
- [x] Mock mode поддержка
- [x] ~~Все тесты проходят (63 passed)~~ → **69 passed, 3 skipped**
- [x] Тесты покрывают реальную логику (не заглушки)
- [x] Документация обновлена

---

## 📝 Уроки и выводы

### 1. "Потёмкинская деревня" в тестах

**Проблема:** 7 из 10 тестов были `pytest.skip("Waiting for...")` — фактически мёртвый код.

**Урок:** Тесты должны проверять реальную логику. Заглушки создают ложное чувство безопасности.

### 2. Структура тестов

**Решение:** Вынести тесты в отдельный пакет `tests/batch/` с общими фикстурами в `conftest.py`.

**Преимущества:**

- Переиспользование фикстур между тестами
- Чистая структура файлов
- Легко добавлять новые тесты

### 3. Кроссплатформенность

**Проблема:** Тест шардинга не работал на Windows (ОС создаёт любые папки).

**Решение:** Использовать символы, запрещённые в Windows (`< > : " | ? *`), для гарантированного fallback.
