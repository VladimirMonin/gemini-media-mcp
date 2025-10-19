# ⚙️ Конфигурация

## Настройка API ключа

### Шаг 1: Получение Gemini API ключа

1. Перейдите на [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Войдите с аккаунтом Google
3. Нажмите "Create API Key"
4. Скопируйте сгенерированный ключ

### Шаг 2: Настройка окружения

Создайте файл `.env` в корне проекта:

```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте ключ:

```env
GEMINI_API_KEY="ваш_настоящий_api_ключ_здесь"
```

## Конфигурация MCP клиента

### Claude Desktop

**Расположение файла конфигурации:**

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Добавьте эту конфигурацию:**

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "/путь/к/venv/bin/python",
      "args": ["/путь/к/server.py"],
      "env": {
        "GEMINI_API_KEY": "ваш_ключ"
      }
    }
  }
}
```

### Cursor / Windsurf

Такая же конфигурация, как для Claude Desktop.

## Настройка модели

Отредактируйте `config.py` для изменения модели по умолчанию:

```python
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"  # Быстрая
# DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"  # Продвинутая
```

## Следующие шаги

- [🚀 Быстрый старт](quick-start.md) - Запустите первый анализ
- [💡 Руководство по использованию](usage.md) - Изучите инструмент

---

**Нужна помощь?** Смотрите [Частые проблемы](common-issues.md)
