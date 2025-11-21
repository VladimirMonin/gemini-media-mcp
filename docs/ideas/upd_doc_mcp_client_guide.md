Полное руководство по настройке MCP клиентов (Windows + Python)

Этот документ описывает эталонную конфигурацию для трех основных клиентов: Cline, VS Code (Native) и Qwen CLI.

Глобальные правила (The Golden Rules)

Пути: Используйте прямые слэши / даже в Windows. Это спасает от ошибок экранирования в JSON.

Плохо: "C:\Projects\server.py" (JSON подумает, что \P — это спецсимвол).

Хорошо: "C:/Projects/server.py".

Таймауты:

VS Code / Cline: Считают время в секундах. 600 = 10 минут.

Node.js Apps (Qwen): Считают время в миллисекундах. 120000 = 2 минуты.

Python: Всегда запускайте с флагом -u и переменной PYTHONUNBUFFERED.

1. Cline (VS Code Extension)

Статус: Cline обычно сам настраивает этот файл через свой интерфейс, но ручная правка надежнее для тонкой настройки (например, env vars).
Путь к файлу: %APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json

{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "C:/PY/gemini-media-mcp/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/PY/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "ВАШ_КЛЮЧ_ЗДЕСЬ",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_audio_generation_guide"
      ],
      "disabled": false,
      "timeout": 600
    }
  }
}

Примечание по таймауту: Здесь 600 означает 600 секунд. Cline достаточно умён.

2. VS Code (Native MCP Support)

Статус: Это встроенная поддержка MCP в самом редакторе (появляется в боковой панели или используется Copilot). Требует перезагрузки окна VS Code после правки.
Путь к файлу: %APPDATA%\Code\User\profiles\{Profile_ID}\mcp.json (или в основной папке User, если профиль один).

{
  "servers": {
    "gemini-media-mcp": {
      "command": "C:/PY/gemini-media-mcp/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/PY/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "ВАШ_КЛЮЧ_ЗДЕСЬ",
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

Важно: VS Code строже относится к структуре JSON. Убедитесь, что корневой объект называется "servers".

3. Qwen CLI (Node.js / The "Princess")

Статус: Самый капризный клиент. Требует огромного таймаута в цифрах и идеальной чистоты канала данных.
Путь к файлу: .qwen/settings.json (в корне вашего проекта) или ~/.qwen/settings.json (глобально).

{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "C:/PY/gemini-media-mcp/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/PY/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "ВАШ_КЛЮЧ_ЗДЕСЬ",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_audio_generation_guide"
      ],
      "disabled": false,
      "type": "stdio",
      "timeout": 120000
    }
  }
}

Почему здесь timeout 120000?

Qwen CLI написан на Node.js и использует нативную функцию setTimeout(ms).

Если вы напишете 600, он будет ждать 0.6 секунды. Сервер с ML-библиотеками (Torch, NumPy) просто не успеет загрузиться за это время.

120000 = 120 000 миллисекунд = 2 минуты. Этого достаточно для любого тяжелого старта.

Чек-лист перед запуском

[ ] Пути: Проверено, что везде стоят / (forward slashes).

[ ] Ключ: Вставлен реальный API Key вместо заглушки.

[ ] Server Code: В файле server.py логи настроены на stream=sys.stderr (как мы исправили ранее).

[ ] Буферизация: Везде добавлен аргумент "-u" и переменная "PYTHONUNBUFFERED": "1".
