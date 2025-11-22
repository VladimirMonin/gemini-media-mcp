# Примеры конфигурации MCP клиентов

Этот документ предоставляет примеры конфигурации для MCP клиентов, включая Cline, VS Code Native и Qwen CLI. Другие MCP клиенты могут иметь другие форматы конфигурации.

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
| `args` | array | Путь к файлу `server.py` (включите флаг `-u` для небуферизованного вывода) |
| `env.GEMINI_API_KEY` | string | Ваш API ключ Gemini из [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `autoApprove` | array | Инструменты, которые не требуют ручного подтверждения (см. предупреждение ниже) |
| `timeout` | number | **КРИТИЧНО:** Максимальное время выполнения. **Секунды** для VS Code/Cline (600 = 10 мин), **Миллисекунды** для Qwen CLI (120000 = 2 мин) |

## Настройка таймаута по клиентам

| Клиент | Единица измерения | Пример значения | Реальное время |
|--------|-------------------|-----------------|----------------|
| **Cline** | Секунды | 600 | 10 минут |
| **VS Code Native** | Секунды | 600 | 10 минут |
| **Qwen CLI** | **Миллисекунды** | 120000 | 2 минуты |

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

## Конфигурация Qwen CLI

Qwen CLI - это MCP клиент на базе Node.js, который требует особого внимания к настройке таймаутов.

### Расположение файла конфигурации

Создайте или отредактируйте `.qwen/settings.json` в корне вашего проекта или `~/.qwen/settings.json` глобально.

### ⚠️ КРИТИЧЕСКИ ВАЖНО: Настройка таймаута

**Qwen CLI использует миллисекунды для таймаутов, НЕ секунды!**

Это отличается от VS Code и Cline (которые используют секунды). Если вы укажете небольшое число вроде 600, Qwen будет ждать всего 0.6 секунды и сообщит, что инструмент не найден.

**Рекомендуемый таймаут: 120000 миллисекунд = 2 минуты**

### Пример конфигурации Qwen CLI (Windows)

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "C:/Projects/gemini-media-mcp/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/Projects/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "ваш_ключ_gemini_api",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines",
        "get_audio_generation_guide"
      ],
      "disabled": false,
      "type": "stdio",
      "timeout": 120000
    }
  }
}
```

### Важные замечания по Qwen CLI

1. **Всегда используйте прямые слэши `/` в путях**, даже в Windows (например, `C:/Projects/...` а не `C:\Projects\...`)
2. **Таймаут указывается в миллисекундах**: 120000 = 120 000 миллисекунд = 2 минуты
3. **Включите аргумент `-u`** и переменную окружения `PYTHONUNBUFFERED` для корректной буферизации вывода
4. **Добавьте поле `type: "stdio"`** для совместимости с Qwen CLI

### Почему такой большой таймаут?

Python-серверы с ML-библиотеками (NumPy, Pillow и т.д.) могут занимать значительное время для запуска. Таймаут в 2 минуты гарантирует, что сервер успеет правильно инициализироваться, особенно при первом запуске.

## Встроенная поддержка MCP в VS Code

VS Code имеет встроенную поддержку MCP, которая отображается в боковой панели или интегрируется с Copilot.

### Расположение файла конфигурации

**Windows:** `%APPDATA%\Code\User\profiles\{Profile_ID}\mcp.json` (или в основной папке User для одного профиля)
**macOS/Linux:** `~/Library/Application Support/Code/User/profiles/{Profile_ID}/mcp.json`

### Пример конфигурации VS Code Native (Windows)

```json
{
  "servers": {
    "gemini-media-analyzer": {
      "command": "C:/Projects/gemini-media-mcp/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/Projects/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "ваш_ключ_gemini_api",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1"
      },
      "autoApprove": [],
      "disabled": false,
      "timeout": 600
    }
  },
  "$version": 1
}
```

### Замечания по VS Code Native

1. **Корневой объект - `"servers"`**, а не `"mcpServers"` (отличается от Cline/Qwen)
2. **Таймаут указывается в секундах**: 600 = 10 минут
3. **Требуется перезагрузка окна** после изменения конфигурации
4. **Строгая валидация JSON** - убедитесь, что структура точно правильная

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
