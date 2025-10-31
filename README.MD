<div align="center">

#  Gemini Media MCP

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**MCP server for analyzing multimedia content using Google Gemini AI**

[English](#english)  [Русский](#русский)

</div>

---

## English

###  About

Model Context Protocol (MCP) server for analyzing images, audio, and video using Google Gemini AI. Built with modular architecture for easy functionality extension.

###  Current Features

-  **Image Analysis** - AI-powered image descriptions
-  **Audio Analysis** - Recognition and transcription of audio files
-  **Flexible Prompts** - Custom system prompts
-  **Multiple Models** - Gemini 2.5 Flash, Pro, and the new Flash Lite
-  **Privacy First** - Runs locally with your API key

###  Documentation

**Getting Started:**
- [ Installation Guide](docs/en/installation.md)
- [ Configuration](docs/en/configuration.md)
- [ Quick Start](docs/en/quick-start.md)

**Usage:**
- [ Basic Usage](docs/en/usage.md)
- [ Troubleshooting](docs/en/troubleshooting.md)
- [ Common Issues](docs/en/common-issues.md)

---

## Русский

###  О проекте

MCP (Model Context Protocol) сервер для анализа изображений, аудио и видео с помощью Google Gemini AI. Модульная архитектура для лёгкого расширения функциональности.

###  Текущие возможности

-  **Анализ изображений** - ИИ описания изображений
-  **Анализ аудио** - Распознавание и транскрипция аудиофайлов
-  **Гибкие промпты** - Настраиваемые системные промпты
-  **Несколько моделей** - Gemini 2.5 Flash, Pro и новая Flash Lite
-  **Конфиденциальность** - Работает локально с вашим ключом

###  Документация

**Начало работы:**
- [ Установка](docs/ru/installation.md)
- [ Настройка](docs/ru/configuration.md)
- [ Быстрый старт](docs/ru/quick-start.md)

**Использование:**
- [ Базовое использование](docs/ru/usage.md)
- [ Решение проблем](docs/ru/troubleshooting.md)
- [ Частые ошибки](docs/ru/common-issues.md)

---

##  Quick Start / Быстрый старт

```bash
# Clone / Клонировать
git clone https://github.com/your-username/gemini-media-mcp.git
cd gemini-media-mcp

# Install / Установить
pip install -r requirements.txt

# Configure / Настроить
cp .env.example .env

# Run / Запустить
python server.py
```

---

##  Project Structure

```
gemini-media-mcp/
 README.md
 docs/
    en/
    ru/
 server.py
 config.py
 models/
 modules/
 utils/
```

---

##  Future Plans

-  Video analysis
-  Image generation
-  Audio generation

---

##  License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**Made with  for the MCP community**

[Report Bug](https://github.com/your-username/gemini-media-mcp/issues)  [Documentation](docs/en/)

</div>
