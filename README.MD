<div align="center">

# Gemini Media MCP

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**MCP server for analyzing multimedia content using Google Gemini AI**

[English](#english)  [Русский](#русский)

</div>

---

## English

### About

Model Context Protocol (MCP) server for analyzing images, audio, and video using Google Gemini AI. Built with modular architecture for easy functionality extension.

### Current Features

- **Image Analysis** - AI-powered image descriptions
- **GIF Animation Analysis** - Frame-by-frame analysis of animated GIFs with intelligent sampling
- **Audio Analysis** - Recognition and transcription of audio files
- **Video Analysis** - Frame-by-frame video analysis with audio transcription
- **Image Generation** - Create images from text and reference images using Gemini 2.5 Flash and Gemini 3 Pro
- **Audio Generation** - Multi-speaker audio from YAML scripts
- **Flexible Prompts** - Custom system prompts
- **Multiple Models** - Gemini 2.5 (Flash, Pro, Flash Lite) and Gemini 3 Pro for image generation
- **Privacy First** - Runs locally with your API key

### Documentation

**Getting Started:**

- [Installation Guide](docs/en/installation.md)
- [Configuration](docs/en/configuration.md)
- [Quick Start](docs/en/quick-start.md)

**Usage:**

- [Basic Usage](docs/en/usage.md)
- [Troubleshooting](docs/en/troubleshooting.md)
- [Common Issues](docs/en/common-issues.md)

---

## Русский

### О проекте

MCP (Model Context Protocol) сервер для анализа изображений, аудио и видео с помощью Google Gemini AI. Модульная архитектура для лёгкого расширения функциональности.

### Текущие возможности

- **Анализ изображений** - ИИ описания изображений
- **Анализ GIF-анимаций** - Покадровый анализ анимированных GIF с умной выборкой кадров
- **Анализ аудио** - Распознавание и транскрипция аудиофайлов
- **Анализ видео** - Покадровый анализ видео с транскрипцией аудио
- **Генерация изображений** - Создание изображений по тексту и референсам с помощью Gemini 2.5 Flash и Gemini 3 Pro
- **Генерация аудио** - Многоголосое аудио из YAML сценариев
- **Гибкие промпты** - Настраиваемые системные промпты
- **Несколько моделей** - Gemini 2.5 (Flash, Pro, Flash Lite) и Gemini 3 Pro для генерации изображений
- **Конфиденциальность** - Работает локально с вашим ключом

### Документация

**Начало работы:**

- [Установка](docs/ru/installation.md)
- [Настройка](docs/ru/configuration.md)
- [Быстрый старт](docs/ru/quick-start.md)

**Использование:**

- [Базовое использование](docs/ru/usage.md)
- [Решение проблем](docs/ru/troubleshooting.md)
- [Частые ошибки](docs/ru/common-issues.md)

---

## Quick Start / Быстрый старт

### Using Installer (Recommended)

1. **Install the package with CLI dependencies:**

    ```bash
    pip install .[cli]
    ```

2. **Run the installer:**

    ```bash
    install-gemini-mcp --gemini-api-key "your_gemini_api_key"
    ```

### Manual Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/VladimirMonin/gemini-media-mcp.git
    cd gemini-media-mcp
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure your MCP client** to pass the `GEMINI_API_KEY` environment variable. See [Client Configuration Examples](docs/en/client_examples.md).
4. **Run the server:**

    ```bash
    python server.py
    ```

---

## Project Structure

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

## Future Plans

- Advanced GIF processing features
- Batch media processing
- Web search integration with Google Search API

---

## License

MIT License - see [LICENSE](LICENSE)

---

<div align="center">

**Made with  for the MCP community**

[Report Bug](https://github.com/your-username/gemini-media-mcp/issues)  [Documentation](docs/en/)

</div>
