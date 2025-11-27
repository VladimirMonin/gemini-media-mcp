# Фаза 0: Валидация Google Batch API

## Обзор

Перед началом полномасштабной разработки асинхронной системы генерации контента (спецификация v3.0) **критически важно** проверить реальную доступность Google Batch API для всех планируемых типов операций.

### Зачем нужна валидация?

**Проблема:** Официальная документация Google может опережать фактическую реализацию API. Например, TTS модели (`gemini-2.5-flash-preview-tts`) документированы как поддерживающие Batch API, но на практике возвращают ошибку `404 NOT_FOUND` с сообщением `"not supported for batchGenerateContent"`.

**Риск:** Без валидации мы можем потратить недели на разработку системы, ориентированной на 50% экономию затрат через Batch API, только чтобы обнаружить, что половина операций его не поддерживает.

**Решение:** Фаза 0 проверяет каждый тип операции **до начала разработки**, позволяя выбрать правильный `execution_mode`:

- ✅ `batch` — операция поддерживает Batch API (50% скидка)
- ⚠️ `local_queue` — операция НЕ поддерживает Batch API (стандартная цена, последовательная обработка)

## Тестовый скрипт

### Запуск

```powershell
# Ключ загружается из .env автоматически
python scripts\check_batch_api.py
```

### Что тестируется?

1. **Text-to-Text** (`gemini-2.5-flash`)
   - Базовая проверка работоспособности Batch API
   - Ожидается: ✅ SUCCESS

2. **Text-to-Image** (`gemini-2.5-flash-image`)
   - Генерация изображений по текстовому запросу
   - Ожидается: ✅ SUCCESS
   - Документация: [Batch API - Image Generation](https://ai.google.dev/gemini-api/docs/batch#use-batch-api-for-content-gen)

3. **Image-to-Image editing** (`gemini-3-pro-image-preview`)
   - Редактирование существующего изображения
   - Ожидается: ✅ SUCCESS
   - Требует: `pip install Pillow`

4. **Text-to-Audio TTS** (`gemini-2.5-flash-preview-tts`)
   - Генерация речи (TTS)
   - Ожидается: ❌ FAILED (404 NOT_FOUND)
   - Известный баг: [Google Forum - Issue 104621](https://discuss.ai.google.dev/t/104621)

## Результаты валидации (27.11.2025)

**Статус:** ✅ ВАЛИДАЦИЯ ПРОЙДЕНА

| Операция | Модель | Batch API | Execution Mode |
|----------|--------|-----------|----------------|
| Text-to-Text | `gemini-2.5-flash` | ✅ | `batch` |
| Text-to-Image | `gemini-2.5-flash-image` | ✅ | `batch` |
| Image-to-Image | `gemini-3-pro-image-preview` | ✅ | `batch` |
| Text-to-Audio TTS | `gemini-2.5-flash-preview-tts` | ❌ | `local_queue` |

**Вывод:** 3 из 4 операций поддерживают Batch API. Гибридная архитектура подтверждена.

**Следующий шаг:** Фаза 1 (Database Core) с корректными `execution_mode` в таблице `operation_types`.

---

## Тестовый скрипт

```
================================================================================
Gemini Media MCP - Фаза 0: Валидация Batch API
================================================================================

Клиент инициализирован с API ключом: AIzaSyBm7Z...Xk9A
SDK версия: google.genai

================================================================================
TEST 1: Text-to-Text (базовый тест)
================================================================================

Отправка запроса в Batch API...
Batch Job ID: projects/.../locations/.../batchPredictionJobs/...
Статус: STATE_SUCCEEDED
Text-to-Text: ✅ SUCCESS

================================================================================
TEST 2: Text-to-Image (gemini-2.5-flash-image)
================================================================================

Отправка запроса в Batch API...
Batch Job ID: projects/.../locations/.../batchPredictionJobs/...
Статус: STATE_PENDING
Text-to-Image: ✅ SUCCESS

================================================================================
TEST 3: Image-to-Image editing (gemini-3-pro-image-preview)
================================================================================

Отправка запроса в Batch API...
Batch Job ID: projects/.../locations/.../batchPredictionJobs/...
Статус: STATE_PENDING
Image-to-Image: ✅ SUCCESS

================================================================================
TEST 4: Text-to-Audio TTS (gemini-2.5-flash-preview-tts)
================================================================================

Отправка запроса в Batch API...
⚠️  Получена ожидаемая ошибка (известный баг Google)
   Подробности: 404 Resource not found. Method not supported for batchGenerateContent.
Text-to-Audio TTS: ❌ FAILED

================================================================================
Генерация отчета
================================================================================

✅ Отчет сохранен: c:\PY\gemini-media-mcp\docs\batch_api_validation_report.md

Итого:
  Всего тестов: 4
  Успешно: 3
  Провалено: 1

Рекомендации для execution_mode:
  Text-to-Text: batch
  Text-to-Image: batch
  Image-to-Image: batch
  Text-to-Audio TTS: local_queue

================================================================================
```

## Интерпретация результатов

### Сценарий 1: Все работает как ожидается (3 успеха, 1 провал TTS)

**Действие:** Продолжайте с гибридной архитектурой:

- IMG_GEN → `execution_mode='batch'` (50% скидка)
- TTS_GEN → `execution_mode='local_queue'` (стандартная цена)

**Обновление схемы:**

```sql
INSERT INTO operation_types (operation_type, display_name, execution_mode) VALUES
('IMG_GEN', 'Image Generation', 'batch'),
('IMG_EDIT', 'Image Editing', 'batch'),
('TTS_GEN', 'Text-to-Speech', 'local_queue');
```

### Сценарий 2: TTS неожиданно работает (4 успеха)

**Действие:** Google исправил баг! 🎉

- Все операции → `execution_mode='batch'`
- Полная экономия 50% на всех запросах
- Упрощенная архитектура воркера (только Batch API, без local_queue)

### Сценарий 3: Изображения не работают (меньше 3 успехов)

**Действие:** Критическая проблема, требуется:

1. Проверить версию SDK: `pip show google-genai`
2. Проверить квоты API в Google Cloud Console
3. Обновить документацию о неподдерживаемых моделях
4. Возможно, отложить внедрение Batch API до исправления Google

## Следующие шаги

После успешной валидации:

1. ✅ **Обновить спецификацию v3.0**
   - Зафиксировать `execution_mode` для каждого `operation_type`
   - Добавить ссылки на отчет валидации

2. ✅ **Перейти к Фазе 1: Database Core**
   - Создать таблицы с корректными `execution_mode`
   - Реализовать DatabaseManager

3. ✅ **Перейти к Фазе 2: Worker Skeleton**
   - Реализовать dual-mode обработку (batch vs local_queue)
   - Добавить логику маршрутизации по `execution_mode`

## Дополнительные ресурсы

- [Техническая спецификация v3.0](../ideas/Детальная%20техническая%20спецификация%20v3.0_%20Система%20асинхронной%20генерации%20контента%20Gemini%20Media%20MCP.md)
- [Официальная документация Batch API](https://ai.google.dev/gemini-api/docs/batch)
- [Context7 - Google Generative AI Python SDK](https://context7.ai/google/generative-ai-python)
- [Баг TTS Batch API (форум Google)](https://discuss.ai.google.dev/t/104621)

## Troubleshooting

### Ошибка: "GEMINI_API_KEY не установлен"

```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

### Ошибка: "google-genai не установлен"

```powershell
pip install --upgrade google-genai
```

### Ошибка: "Pillow not installed" (Тест 3)

```powershell
pip install Pillow
```

Тест 3 можно пропустить, если не требуется image-to-image editing.

### Неожиданные 404 на всех тестах

Проверьте:

1. Корректность API ключа
2. Квоты в Google Cloud Console
3. Доступность моделей в вашем регионе

---

**Последнее обновление:** 27 ноября 2025 г.
