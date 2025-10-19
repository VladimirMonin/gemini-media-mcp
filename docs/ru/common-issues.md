# 📝 Частые проблемы и решения

## Проблемы установки

### Проблема: pip install падает с SSL ошибкой

**Симптомы:**

```text
SSL: CERTIFICATE_VERIFY_FAILED
```

**Решение:**

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Проблема: Версия Python слишком старая

**Симптомы:**

```text
ERROR: Python 3.7 is not supported
```

**Решение:**

- Установите Python 3.8 или выше
- Проверьте версию: `python --version`

## Проблемы конфигурации

### Проблема: API ключ не распознаётся

**Симптомы:**

```text
Error: GEMINI_API_KEY environment variable not set
```

**Решение:**

1. Проверьте формат файла `.env` (без пробелов):

   ```env
   GEMINI_API_KEY="AIza..."
   ```

2. Проверьте кодировку файла UTF-8
3. Перезапустите терминал после редактирования

### Проблема: Конфигурация MCP клиента не работает

**Симптомы:**

- Сервер не появляется в клиенте
- Тайм-аут подключения

**Решение:**

1. Проверьте синтаксис JSON (используйте [jsonlint.com](https://jsonlint.com))
2. Проверьте пути с прямыми слэшами или экранированными обратными:

   ```json
   "command": "C:/Python38/python.exe"
   ```

3. Полностью перезапустите клиентское приложение

## Проблемы выполнения

### Проблема: "Image encoding failed"

**Симптомы:**

```text
Error encoding image to base64
```

**Решение:**

1. Проверьте, что изображение не повреждено
2. Попробуйте открыть в просмотрщике изображений
3. Конвертируйте в стандартный формат (JPEG/PNG)

### Проблема: Анализ возвращает пустой ответ

**Симптомы:**

- Нет ошибки, но поле `description` пустое

**Решение:**

1. Попробуйте другой промпт
2. Проверьте качество изображения (не слишком размытое)
3. Переключитесь на модель `gemini-2.5-pro`

### Проблема: Медленная производительность анализа

**Симптомы:**

- Занимает >30 секунд на изображение

**Решение:**

1. Используйте `gemini-2.5-flash` для скорости
2. Уменьшите размер изображения перед анализом
3. Проверьте сетевое подключение

## Проблемы специфичные для Windows

### Проблема: Выполнение PowerShell скриптов отключено

**Симптомы:**

```text
cannot be loaded because running scripts is disabled
```

**Решение:**

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Проблема: Путь содержит пробелы

**Симптомы:**

- Ошибки конфигурационного файла с путями

**Решение:**
Используйте кавычки в JSON:

```json
"args": ["C:/Program Files/Python/server.py"]
```

## Получение диагностической информации

Запустите диагностический скрипт:

```bash
python -c "import sys; print(f'Python: {sys.version}'); from config import GEMINI_API_KEY; print('API Key:', 'Установлен' if GEMINI_API_KEY else 'Отсутствует')"
```

---

**Всё ещё нужна помощь?**

- [Руководство по решению проблем](troubleshooting.md)
- [FAQ](faq.md)
- [GitHub Issues](https://github.com/your-username/gemini-media-mcp/issues)
