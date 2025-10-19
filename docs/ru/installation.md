# 📥 Руководство по установке

## Требования

- Python 3.8 или выше
- pip (менеджер пакетов Python)
- Git

## Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/your-username/gemini-media-mcp.git
cd gemini-media-mcp
```

## Шаг 2: Создание виртуального окружения

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

## Шаг 3: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 4: Проверка установки

```bash
python server.py --help
```

Если вы видите справочную информацию, установка прошла успешно!

## Следующие шаги

- [⚙️ Конфигурация](configuration.md) - Настройка API ключей и параметров
- [🚀 Быстрый старт](quick-start.md) - Запуск первого анализа

---

**Проблемы?** Проверьте [Решение проблем](troubleshooting.md)
