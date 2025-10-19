# 🔧 Решение проблем

## Сервер не запускается

### ❌ Ошибка: "Module not found"

**Решение:**

```bash
pip install -r requirements.txt
```

### ❌ Ошибка: "GEMINI_API_KEY not set"

**Решение:**

1. Проверьте наличие файла `.env` в корне проекта
2. Проверьте формат ключа: `GEMINI_API_KEY="ваш_ключ_здесь"`
3. Перезапустите сервер

### ❌ Ошибка: "Permission denied"

**Решение (Windows):**

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Проблемы подключения

### ❌ MCP клиент не может подключиться

**Проверьте:**

1. Путь к виртуальному окружению в конфиге правильный
2. Путь к серверу указывает на `server.py`
3. Полностью перезапустите MCP клиент

**Проверьте вручную:**

```bash
python server.py
```

### ❌ Сервер запущен, но не отвечает

**Решение:**

1. Проверьте логи в консоли
2. Проверьте валидность API ключа
3. Протестируйте API ключ:

```bash
python -c "from config import GEMINI_API_KEY; print('Ключ загружен' if GEMINI_API_KEY else 'Отсутствует')"
```

## Ошибки API

### ❌ Ошибка: "Invalid API key"

**Решение:**

1. Получите новый ключ на [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Обновите файл `.env`
3. Перезапустите сервер

### ❌ Ошибка: "Rate limit exceeded"

**Решение:**

- Подождите несколько минут перед повторной попыткой
- Рассмотрите возможность обновления тарифного плана API

### ❌ Ошибка: "File too large"

**Решение:**

- Максимальный размер файла 20 МБ
- Уменьшите размер изображения перед анализом

## Проблемы анализа изображений

### ❌ Ошибка: "Unsupported image format"

**Поддерживаемые форматы:**

- JPEG, PNG, GIF, WEBP, HEIC, HEIF

**Решение:**
Конвертируйте изображение онлайн или:

```bash
pip install pillow
python -c "from PIL import Image; Image.open('input.bmp').save('output.jpg')"
```

### ❌ Ошибка: "Image file not found"

**Решение:**

- Используйте абсолютные пути: `C:\Users\Имя\Pictures\photo.jpg`
- Проверьте существование файла и права чтения

## Получение дополнительной помощи

- [Частые проблемы](common-issues.md) - Конкретные сценарии ошибок
- [FAQ](faq.md) - Часто задаваемые вопросы
- [GitHub Issues](https://github.com/your-username/gemini-media-mcp/issues)

---

**Всё ещё застряли?** Откройте issue с информацией:

- Сообщение об ошибке
- Операционная система
- Версия Python (`python --version`)
