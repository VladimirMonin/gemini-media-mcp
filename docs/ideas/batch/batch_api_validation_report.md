# Отчет о валидации Google Batch API

**Дата тестирования:** 27.11.2025 13:55:40
**Версия SDK:** google-genai

## Результаты тестирования

| Тест | Модель | Статус | Execution Mode | Примечания |
|------|--------|--------|----------------|------------|
| Text-to-Text | `gemini-2.5-flash` | ✅ | `batch` | - |
| Text-to-Image | `gemini-2.5-flash-image` | ✅ | `batch` | - |
| Image-to-Image | `gemini-3-pro-image-preview` | ✅ | `batch` | - |
| Text-to-Audio TTS | `gemini-2.5-flash-preview-tts` | ❌ | `local_queue` | Error: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'models/gemini-2.5-flash-preview-tts is not found ... | (Ожидаемый баг Google) |

## Выводы и рекомендации

### Операции с поддержкой Batch API (50% скидка):

* **Text-to-Text** (`gemini-2.5-flash`) → `execution_mode='batch'`
* **Text-to-Image** (`gemini-2.5-flash-image`) → `execution_mode='batch'`
* **Image-to-Image** (`gemini-3-pro-image-preview`) → `execution_mode='batch'`

### Операции БЕЗ поддержки Batch API (local_queue):

* **Text-to-Audio TTS** (`gemini-2.5-flash-preview-tts`) → `execution_mode='local_queue'` _(ожидаемо)_

## Ссылки

* [Официальная документация Batch API](https://ai.google.dev/gemini-api/docs/batch)
* [Баг TTS Batch API (форум Google)](https://discuss.ai.google.dev/t/104621)
* [Context7 SDK Documentation](/google/generative-ai-python)

---

_Отчет сгенерирован автоматически: 27.11.2025 13:55:40_