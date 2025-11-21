# Пример конфигурации клиента Cline

Этот документ предоставляет примеры конфигурации для клиента Cline. Другие MCP клиенты могут иметь другие форматы конфигурации.

## Расположение файла конфигурации

**macOS/Linux:**

```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

**Windows:**

```
%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

## Настройка клиента Cline

Для настройки клиента Cline добавьте следующую конфигурацию в файл `cline_mcp_settings.json`. Замените пути на абсолютный путь к директории вашего проекта.

### Пример конфигурации для macOS

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "/Users/username/Documents/gemini-media-mcp/.venv/bin/python",
      "args": [
        "/Users/username/Documents/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "ваш_ключ_gemini_api"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines",
        "get_audio_generation_guide"
      ],
      "timeout": 600
    }
  }
}
```

**Реальный пример (macOS):**

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "/Users/ivan/Documents/py/gemini-media-mcp/.venv/bin/python",
      "args": [
        "/Users/ivan/Documents/py/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "AIzaSyD1234567890abcdefghijklmnopqrstuvw"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines"
      ],
      "timeout": 600
    }
  }
}
```

**Как найти ваши пути (macOS):**

```bash
# Перейдите в директорию проекта
cd ~/Documents/gemini-media-mcp

# Получите путь к Python
echo "$(pwd)/.venv/bin/python"

# Получите путь к server.py
echo "$(pwd)/server.py"
```

### Пример конфигурации для Windows

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "C:\\Users\\username\\Documents\\gemini-media-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\username\\Documents\\gemini-media-mcp\\server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "ваш_ключ_gemini_api",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines",
        "get_audio_generation_guide"
      ],
      "timeout": 600
    }
  }
}
```

**Реальный пример (Windows):**

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "C:\\Projects\\gemini-media-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Projects\\gemini-media-mcp\\server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "AIzaSyD1234567890abcdefghijklmnopqrstuvw",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines"
      ],
      "timeout": 600
    }
  }
}
```

**Как найти ваши пути (Windows PowerShell):**

```powershell
# Перейдите в директорию проекта
cd C:\Projects\gemini-media-mcp

# Получите путь к Python
Write-Host "$PWD\.venv\Scripts\python.exe"

# Получите путь к server.py
Write-Host "$PWD\server.py"
```

### Пример конфигурации для Linux

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "/home/username/projects/gemini-media-mcp/.venv/bin/python",
      "args": [
        "/home/username/projects/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "ваш_ключ_gemini_api"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines"
      ],
      "timeout": 600
    }
  }
}
```

## Параметры конфигурации

| Параметр | Тип | Описание |
|----------|-----|----------|
| `command` | string | **Полный путь** к интерпретатору Python в виртуальном окружении |
| `args` | array | Путь к файлу `server.py` |
| `env.GEMINI_API_KEY` | string | Ваш API ключ Gemini из [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `autoApprove` | array | Инструменты, которые не требуют ручного подтверждения (см. предупреждение ниже) |
| `timeout` | number | Максимальное время выполнения в секундах (по умолчанию: 600 для обработки медиа) |

## Особенности платформ

### macOS/Linux

- Расположение исполняемого файла Python: `.venv/bin/python`
- Используйте прямые слэши `/` в путях
- Пути чувствительны к регистру

### Windows

- Расположение исполняемого файла Python: `.venv\Scripts\python.exe`
- Используйте двойные обратные слэши `\\` в JSON путях
- Добавьте переменные окружения для поддержки Unicode

## Проверка конфигурации

После добавления конфигурации:

1. **Перезагрузите окно VS Code:**
   - Нажмите `Cmd+Shift+P` (macOS) или `Ctrl+Shift+P` (Windows/Linux)
   - Введите "Reload Window" и нажмите Enter

2. **Проверьте регистрацию сервера:**
   - Откройте чат Cline
   - Найдите "gemini-media-analyzer" в доступных MCP серверах
   - Вы должны увидеть 7 зарегистрированных инструментов:
     - `analyze_image`
     - `analyze_gif`
     - `analyze_audio`
     - `generate_image`
     - `generate_audio_from_yaml`
     - `get_gif_guidelines`
     - `get_audio_generation_guide`

3. **Тест вручную (опционально):**

**macOS/Linux:**

```bash
cd /path/to/gemini-media-mcp
source .venv/bin/activate
python server.py
```

**Windows:**

```powershell
cd C:\path\to\gemini-media-mcp
.venv\Scripts\Activate.ps1
python server.py
```

Вы должны увидеть:

```
Tool 'analyze_image' registered successfully.
Tool 'analyze_audio' registered successfully.
Tool 'generate_image' registered successfully.
Tool 'generate_audio_from_yaml' registered successfully.
Tool 'get_audio_generation_guide' registered successfully.
Tool 'analyze_gif' registered successfully.
Tool 'get_gif_guidelines' registered successfully.
```

## ⚠️ Важные предупреждения о безопасности и стоимости

### Предупреждение о автоодобрении

**НИКОГДА не включайте автоодобрение для инструментов, если вы не уверены на 100% в том, что делаете, или не используете исключительно бесплатный тариф.**

Настройка `autoApprove` позволяет инструментам запускаться без явного подтверждения пользователя. Это может быть опасно для платных инструментов или инструментов, которые могут повлечь расходы. Используйте автоодобрение только если вы полностью понимаете последствия и используете бесплатные функции.

### Стоимость генерации изображений

**Генерация изображений (инструмент `generate_image`) - это платная функция без бесплатного тарифа.**

- Текущая стоимость: примерно $0.04 за изображение
- Эта функция использует платный API генерации изображений от Google
- Будьте внимательны к потенциальным расходам перед интенсивным использованием этого инструмента
- Рассмотрите возможность настройки лимитов использования или мониторинга использования вашего API
