# Code Review — 2025-11-29

## Дерево проекта

```
gemini-media-mcp/
├── config.py
├── recreate_db.py
├── server.py
├── config/
│   └── mcp_config.py
├── database/
│   ├── __init__.py
│   ├── batches_repository.py
│   ├── connection_manager.py
│   ├── manager.py
│   ├── manager_old.py
│   ├── operation_types_repository.py
│   ├── queries.py
│   ├── schema.py
│   ├── seed_data.py
│   ├── task_utilities.py
│   └── tasks_repository.py
├── models/
│   ├── __init__.py
│   └── analysis.py
├── scripts/
│   ├── check_batch_api.py
│   ├── debug_batch_response.py
│   ├── debug_httpx_patch.py
│   ├── demo_worker.py
│   ├── install_server.py
│   └── recreate_db.py
├── tests/
│   ├── test_backup_manager.py
│   ├── test_batch_polling.py
│   ├── test_batch_submission.py
│   ├── test_database.py
│   ├── test_gemini_analyzer.py
│   ├── test_worker.py
│   ├── batch/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_mcp_tools.py
│   │   ├── test_retrieval.py
│   │   └── test_tts_queue.py
│   └── e2e/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_full_system.py
├── tools/
│   ├── __init__.py
│   ├── audio_analyzer.py
│   ├── audio_generator.py
│   ├── batch_tools.py
│   ├── gif_analyzer.py
│   ├── image_analyzer.py
│   ├── image_generator.py
│   └── video_analyzer.py
├── utils/
│   ├── __init__.py
│   ├── audio_extractor.py
│   ├── backup_manager.py
│   ├── file_utils.py
│   ├── gemini_client.py
│   ├── gif_processor.py
│   ├── image_tokens.py
│   ├── logger.py
│   └── media_frame_extractor.py
└── worker/
    ├── __init__.py
    ├── manager.py
    └── processors/
        ├── __init__.py
        ├── batch_processor.py
        └── queue_processor.py
```

## Сводная таблица

| Статус | Файл | Путь | Замечания |
|--------|------|------|-----------|
| 🟡 | `config.py` | `./config.py` | 2 |
| 🟡 | `recreate_db.py` | `./recreate_db.py` | 1 |
| 🟡 | `server.py` | `./server.py` | 2 |
| 🔴 | `mcp_config.py` | `./config/mcp_config.py` | 3 |
| ✅ | `__init__.py` | `./database/__init__.py` | — |
| ✅ | `batches_repository.py` | `./database/batches_repository.py` | — |
| ✅ | `connection_manager.py` | `./database/connection_manager.py` | — |
| ✅ | `manager.py` | `./database/manager.py` | — |
| 🔴 | `manager_old.py` | `./database/manager_old.py` | 1 |
| ✅ | `operation_types_repository.py` | `./database/operation_types_repository.py` | — |
| ✅ | `queries.py` | `./database/queries.py` | — |
| ✅ | `schema.py` | `./database/schema.py` | — |
| ✅ | `seed_data.py` | `./database/seed_data.py` | — |
| ✅ | `task_utilities.py` | `./database/task_utilities.py` | — |
| ✅ | `tasks_repository.py` | `./database/tasks_repository.py` | — |
| 🟡 | `__init__.py` | `./models/__init__.py` | 1 |
| 🟡 | `analysis.py` | `./models/analysis.py` | 1 |
| ✅ | `check_batch_api.py` | `./scripts/check_batch_api.py` | — |
| ✅ | `debug_batch_response.py` | `./scripts/debug_batch_response.py` | — |
| ✅ | `debug_httpx_patch.py` | `./scripts/debug_httpx_patch.py` | — |
| ✅ | `demo_worker.py` | `./scripts/demo_worker.py` | — |
| 🟡 | `install_server.py` | `./scripts/install_server.py` | 1 |
| ✅ | `recreate_db.py` | `./scripts/recreate_db.py` | — |
| 🟡 | `test_backup_manager.py` | `./tests/test_backup_manager.py` | 1 |
| ✅ | `test_batch_polling.py` | `./tests/test_batch_polling.py` | — |
| ✅ | `test_batch_submission.py` | `./tests/test_batch_submission.py` | — |
| 🟡 | `test_database.py` | `./tests/test_database.py` | 1 |
| 🟡 | `test_gemini_analyzer.py` | `./tests/test_gemini_analyzer.py` | 1 |
| ✅ | `test_worker.py` | `./tests/test_worker.py` | — |
| ✅ | `conftest.py` | `./tests/batch/conftest.py` | — |
| ✅ | `__init__.py` | `./tests/batch/__init__.py` | — |
| 🟡 | `test_mcp_tools.py` | `./tests/batch/test_mcp_tools.py` | 1 |
| ✅ | `test_retrieval.py` | `./tests/batch/test_retrieval.py` | — |
| ✅ | `test_tts_queue.py` | `./tests/batch/test_tts_queue.py` | — |
| 🟡 | `__init__.py` | `./tests/e2e/__init__.py` | 1 |
| ✅ | `conftest.py` | `./tests/e2e/conftest.py` | — |
| 🟡 | `test_full_system.py` | `./tests/e2e/test_full_system.py` | 1 |
| ❓ | `__init__.py` | `./tools/__init__.py` | — |
| 🟡 | `audio_analyzer.py` | `./tools/audio_analyzer.py` | 1 |
| 🟡 | `audio_generator.py` | `./tools/audio_generator.py` | 2 |
| 🟡 | `batch_tools.py` | `./tools/batch_tools.py` | 1 |
| 🟡 | `gif_analyzer.py` | `./tools/gif_analyzer.py` | 1 |
| 🟡 | `image_analyzer.py` | `./tools/image_analyzer.py` | 1 |
| 🟡 | `image_generator.py` | `./tools/image_generator.py` | 1 |
| 🟡 | `video_analyzer.py` | `./tools/video_analyzer.py` | 1 |
| 🟡 | `__init__.py` | `./utils/__init__.py` | 1 |
| 🟡 | `audio_extractor.py` | `./utils/audio_extractor.py` | 1 |
| ✅ | `backup_manager.py` | `./utils/backup_manager.py` | — |
| 🟡 | `file_utils.py` | `./utils/file_utils.py` | 1 |
| 🟡 | `gemini_client.py` | `./utils/gemini_client.py` | 1 |
| 🟡 | `gif_processor.py` | `./utils/gif_processor.py` | 1 |
| 🟡 | `image_tokens.py` | `./utils/image_tokens.py` | 1 |
| 🟡 | `logger.py` | `./utils/logger.py` | 1 |
| 🟡 | `media_frame_extractor.py` | `./utils/media_frame_extractor.py` | 1 |
| ✅ | `__init__.py` | `./worker/__init__.py` | — |
| ✅ | `manager.py` | `./worker/manager.py` | — |
| ✅ | `__init__.py` | `./worker/processors/__init__.py` | — |
| 🟡 | `batch_processor.py` | `./worker/processors/batch_processor.py` | 2 |
| ✅ | `queue_processor.py` | `./worker/processors/queue_processor.py` | — |

## Детальный разбор

---

### 🟡 `config.py`

**Путь:** `./config.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | Докстринг на АНГЛИЙСКОМ, должен быть на русском |
| 2 | `TIER_RATE_LIMITS` | Избыточные комментарии (OVER_COMMENT) — пояснения к каждому tier можно убрать |

---

### 🟡 `recreate_db.py`

**Путь:** `./recreate_db.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | Докстринг на АНГЛИЙСКОМ (короткий), нужен русский |

---

### 🟡 `server.py`

**Путь:** `./server.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | `NO_MOD_DOC` — нет модульного докстринга вообще |
| 2 | комментарии | OVER_COMMENT — много AI-комментариев типа `# 1. Фикс кодировки...`, `# 2. НАСТРОЙКА ЛОГГЕРА...`, `# 3. Явный запуск...` |

---

### 🔴 `mcp_config.py`

**Путь:** `./config/mcp_config.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | `NO_MOD_DOC` — нет модульного докстринга |
| 2 | `MCPServerConfig` | `NO_DOC` — нет докстринга класса |
| 3 | `MCPClientConfig` | `NO_DOC` — нет докстринга класса |

---

### 🔴 `manager_old.py`

**Путь:** `./database/manager_old.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | весь файл | `DEAD_CODE` — файл устарел, есть новый `manager.py` с рефакторингом. Рекомендуется удалить |

---

### 🟡 `models/__init__.py`

**Путь:** `./models/__init__.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | Докстринг на АНГЛИЙСКОМ |

---

### 🟡 `models/analysis.py`

**Путь:** `./models/analysis.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + классы | Докстринги на АНГЛИЙСКОМ (модуль, ImageAnalysisResponse, ErrorResponse, AudioAnalysisResponse, VideoAnalysisResponse) |

---

### 🟡 `tools/image_analyzer.py`

**Путь:** `./tools/image_analyzer.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `tools/audio_analyzer.py`

**Путь:** `./tools/audio_analyzer.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `tools/audio_generator.py`

**Путь:** `./tools/audio_generator.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | `NO_MOD_DOC` — нет модульного докстринга |
| 2 | все функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `tools/image_generator.py`

**Путь:** `./tools/image_generator.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `tools/gif_analyzer.py`

**Путь:** `./tools/gif_analyzer.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `tools/video_analyzer.py`

**Путь:** `./tools/video_analyzer.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `tools/batch_tools.py`

**Путь:** `./tools/batch_tools.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `utils/__init__.py`

**Путь:** `./utils/__init__.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | Докстринг на АНГЛИЙСКОМ |

---

### 🟡 `utils/logger.py`

**Путь:** `./utils/logger.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `utils/file_utils.py`

**Путь:** `./utils/file_utils.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `utils/gemini_client.py`

**Путь:** `./utils/gemini_client.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + класс + методы | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `utils/image_tokens.py`

**Путь:** `./utils/image_tokens.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `utils/gif_processor.py`

**Путь:** `./utils/gif_processor.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `utils/audio_extractor.py`

**Путь:** `./utils/audio_extractor.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `utils/media_frame_extractor.py`

**Путь:** `./utils/media_frame_extractor.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринги на АНГЛИЙСКОМ |

---

### 🟡 `worker/processors/batch_processor.py`

**Путь:** `./worker/processors/batch_processor.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | `_save_image()` | Дублирование Raises в докстринге (скопировано дважды) |
| 2 | комментарии | OVER_COMMENT — много избыточных комментариев типа `# ⚠️ КРИТИЧНО:`, `# ВАЖНО:`, `# CRITICAL:`, пояснения каждого шага |

---

### 🟡 `scripts/install_server.py`

**Путь:** `./scripts/install_server.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | `NO_MOD_DOC` — нет модульного докстринга |

---

### 🟡 `tests/test_backup_manager.py`

**Путь:** `./tests/test_backup_manager.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + все классы/функции | `ENGLISH_DOC` — все докстринги на английском языке |

---

### 🟡 `tests/test_database.py`

**Путь:** `./tests/test_database.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + все классы/функции | `ENGLISH_DOC` — все докстринги на английском языке |

---

### 🟡 `tests/test_gemini_analyzer.py`

**Путь:** `./tests/test_gemini_analyzer.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | `NO_MOD_DOC` — нет модульного докстринга |

---

### 🟡 `tests/batch/test_mcp_tools.py`

**Путь:** `./tests/batch/test_mcp_tools.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + все классы/функции | `ENGLISH_DOC` — все докстринги на английском языке |

---

### 🟡 `tests/e2e/__init__.py`

**Путь:** `./tests/e2e/__init__.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль | `ENGLISH_DOC` — докстринг на английском языке |

---

### 🟡 `tests/e2e/test_full_system.py`

**Путь:** `./tests/e2e/test_full_system.py`

| № | Функция/Метод | Проблема |
|---|---------------|----------|
| 1 | модуль + функции | Докстринг на **смешанном языке** (русские символы + английские слова + иероглифы?) — видимо проблема кодировки файла |

---

## Файлы с высокой плотностью комментариев (OVER_COMMENT)

| Файл | Плотность | Комментариев/Строк |
|------|-----------|-------------------|
| `config.py` | 10.3% | 70/679 |
| `database/queries.py` | 17% | 42/247 |
| `worker/processors/batch_processor.py` | 12.2% | 83/682 |
| `worker/processors/queue_processor.py` | 12.8% | 38/296 |

---

## Общие рекомендации

### 1. DEAD_CODE — Удалить мёртвый файл

**`database/manager_old.py`** — резервная копия старого менеджера БД. Необходимо удалить или переместить в `docs/archive/`.

### 2. ENGLISH_DOC — Перевести докстринги на русский

Файлы с английской документацией (требуется перевод):

**Корневые:**

- `config.py` — модуль + некоторые переменные
- `server.py` — добавить модульный докстринг

**config/:**

- `mcp_config.py` — добавить докстринги

**models/:**

- `models/__init__.py`, `models/analysis.py`

**tools/:**

- `tools/__init__.py`, `tools/audio_analyzer.py`, `tools/audio_generator.py`
- `tools/batch_tools.py`, `tools/gif_analyzer.py`, `tools/image_analyzer.py`
- `tools/image_generator.py`, `tools/video_analyzer.py`

**utils/:**

- `utils/__init__.py`, `utils/logger.py`, `utils/file_utils.py`
- `utils/gemini_client.py`, `utils/image_tokens.py`, `utils/gif_processor.py`
- `utils/audio_extractor.py`, `utils/media_frame_extractor.py`

**tests/:**

- `tests/test_backup_manager.py`, `tests/test_database.py`
- `tests/test_gemini_analyzer.py`, `tests/batch/test_mcp_tools.py`
- `tests/e2e/__init__.py`, `tests/e2e/test_full_system.py`

### 3. OVER_COMMENT — Убрать избыточные комментарии

Файлы с избыточными комментариями (более 10% комментариев от общего количества строк):

- **`database/queries.py`** (17%) — SQL-запросы не требуют пояснения каждой строки
- **`worker/processors/batch_processor.py`** (12.2%) — много `# ВАЖНО:`, `# КРИТИЧНО:`, секционных разделителей
- **`worker/processors/queue_processor.py`** (12.8%) — аналогично
- **`config.py`** (10.3%) — избыточные пояснения переменных

### 4. NO_MOD_DOC — Добавить модульные докстринги

- `scripts/install_server.py`
- `tests/test_gemini_analyzer.py`

### 5. Кодировка файла

**`tests/e2e/test_full_system.py`** — проблема с кодировкой (отображаются иероглифы вместо русских символов). Проверить и исправить кодировку на UTF-8.

---

## Статистика

| Статус | Количество файлов |
|--------|-------------------|
| ✅ Отлично | 32 |
| 🟡 Замечания | 28 |
| 🔴 Критично | 1 (manager_old.py — DEAD_CODE) |

---

_Отчет создан: 2025-11-29_
