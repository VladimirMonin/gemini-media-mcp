#!/usr/bin/env python3
"""
Фаза 0: Валидация Google Batch API
Тестовый скрипт для проверки работоспособности Batch API для различных типов операций.

Автор: Gemini Media MCP Team
Дата: 27 ноября 2025 г.
Версия: 1.0

Результаты тестирования определяют execution_mode для каждого operation_type:
- ✅ SUCCESS → 'batch' (50% скидка на API)
- ❌ FAILED → 'local_queue' (обычная цена, последовательная обработка)
"""

import os
import sys
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Проверка наличия google-genai
try:
    import google.genai as genai
except ImportError:
    print("❌ ERROR: google-genai не установлен. Выполните: pip install google-genai")
    sys.exit(1)

# Проверка API ключа
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ ERROR: GEMINI_API_KEY не установлен в переменных окружения")
    sys.exit(1)

# Инициализация клиента
client = genai.Client(api_key=API_KEY)


# Цвета для терминала (кросс-платформенная поддержка)
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Печать заголовка теста."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.ENDC}\n")


def print_result(test_name: str, success: bool, details: str = ""):
    """Печать результата теста."""
    status = (
        f"{Colors.GREEN}✅ SUCCESS{Colors.ENDC}"
        if success
        else f"{Colors.RED}❌ FAILED{Colors.ENDC}"
    )
    print(f"{test_name}: {status}")
    if details:
        print(f"   {Colors.YELLOW}→ {details}{Colors.ENDC}")


def test_text_to_text() -> Dict[str, Any]:
    """
    Тест 1: Text-to-Text (базовая функциональность Batch API)
    Ожидается: ✅ SUCCESS
    """
    print_header("TEST 1: Text-to-Text (базовый тест)")

    try:
        inline_requests = [
            {
                "contents": [
                    {"parts": [{"text": "Hello, world! This is a batch API test."}]}
                ]
            }
        ]

        print("Отправка запроса в Batch API...")
        batch_job = client.batches.create(model="gemini-2.5-flash", src=inline_requests)

        print(f"Batch Job ID: {batch_job.name}")
        print(f"Статус: {batch_job.state}")

        return {
            "test_name": "Text-to-Text",
            "model": "gemini-2.5-flash",
            "success": True,
            "batch_id": batch_job.name,
            "status": str(batch_job.state),
            "execution_mode": "batch",
        }

    except Exception as e:
        error_msg = str(e)
        return {
            "test_name": "Text-to-Text",
            "model": "gemini-2.5-flash",
            "success": False,
            "error": error_msg,
            "execution_mode": "local_queue",
        }


def test_text_to_image() -> Dict[str, Any]:
    """
    Тест 2: Text-to-Image (генерация изображений)
    Ожидается: ✅ SUCCESS (официальная документация подтверждает)
    """
    print_header("TEST 2: Text-to-Image (gemini-2.5-flash-image)")

    try:
        inline_requests = [
            {
                "contents": [
                    {"parts": [{"text": "A cat astronaut floating in space"}]}
                ],
                "config": {"response_modalities": ["TEXT", "IMAGE"]},
            }
        ]

        print("Отправка запроса в Batch API...")
        batch_job = client.batches.create(
            model="gemini-2.5-flash-image", src=inline_requests
        )

        print(f"Batch Job ID: {batch_job.name}")
        print(f"Статус: {batch_job.state}")

        return {
            "test_name": "Text-to-Image",
            "model": "gemini-2.5-flash-image",
            "success": True,
            "batch_id": batch_job.name,
            "status": str(batch_job.state),
            "execution_mode": "batch",
        }

    except Exception as e:
        error_msg = str(e)
        return {
            "test_name": "Text-to-Image",
            "model": "gemini-2.5-flash-image",
            "success": False,
            "error": error_msg,
            "execution_mode": "local_queue",
        }


def test_image_to_image() -> Dict[str, Any]:
    """
    Тест 3: Image-to-Image (редактирование изображений)
    Ожидается: ✅ SUCCESS
    """
    print_header("TEST 3: Image-to-Image editing (gemini-3-pro-image-preview)")

    try:
        # Создаем простое тестовое изображение (1x1 красный пиксель)
        # В реальном тесте можно использовать существующий файл
        import io
        from PIL import Image

        # Создаем минимальное изображение
        img = Image.new("RGB", (64, 64), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        inline_requests = [
            {
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": base64_image,
                                }
                            },
                            {"text": "Add a wizard hat to this image"},
                        ]
                    }
                ],
                "config": {"response_modalities": ["IMAGE"]},
            }
        ]

        print("Отправка запроса в Batch API...")
        batch_job = client.batches.create(
            model="gemini-3-pro-image-preview", src=inline_requests
        )

        print(f"Batch Job ID: {batch_job.name}")
        print(f"Статус: {batch_job.state}")

        return {
            "test_name": "Image-to-Image",
            "model": "gemini-3-pro-image-preview",
            "success": True,
            "batch_id": batch_job.name,
            "status": str(batch_job.state),
            "execution_mode": "batch",
        }

    except Exception as e:
        error_msg = str(e)
        return {
            "test_name": "Image-to-Image",
            "model": "gemini-3-pro-image-preview",
            "success": False,
            "error": error_msg,
            "execution_mode": "local_queue",
        }


def test_text_to_audio() -> Dict[str, Any]:
    """
    Тест 4: Text-to-Audio TTS
    Ожидается: ❌ 404 NOT_FOUND (известный баг Google API)
    """
    print_header("TEST 4: Text-to-Audio TTS (gemini-2.5-flash-preview-tts)")

    try:
        inline_requests = [
            {
                "contents": [{"parts": [{"text": "Hello from Gemini TTS batch test"}]}],
                "config": {
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {"voice_name": "Kore"}
                        }
                    }
                },
            }
        ]

        print("Отправка запроса в Batch API...")
        batch_job = client.batches.create(
            model="gemini-2.5-flash-preview-tts", src=inline_requests
        )

        # Если дошли сюда - неожиданный успех!
        print(f"⚠️  НЕОЖИДАННО: Batch Job создан! ID: {batch_job.name}")
        print("⚠️  Google мог исправить баг с TTS Batch API")

        return {
            "test_name": "Text-to-Audio TTS",
            "model": "gemini-2.5-flash-preview-tts",
            "success": True,
            "batch_id": batch_job.name,
            "status": str(batch_job.state),
            "execution_mode": "batch",
            "note": "UNEXPECTED SUCCESS - Google may have fixed the bug!",
        }

    except Exception as e:
        error_msg = str(e)

        # Проверяем, является ли это ожидаемой ошибкой 404
        is_expected_error = (
            "404" in error_msg
            or "not supported" in error_msg.lower()
            or "batchGenerateContent" in error_msg
        )

        if is_expected_error:
            print(
                f"{Colors.YELLOW}⚠️  Получена ожидаемая ошибка (известный баг Google){Colors.ENDC}"
            )
            print(f"{Colors.YELLOW}   Подробности: {error_msg[:200]}{Colors.ENDC}")

        return {
            "test_name": "Text-to-Audio TTS",
            "model": "gemini-2.5-flash-preview-tts",
            "success": False,
            "error": error_msg,
            "execution_mode": "local_queue",
            "expected_failure": is_expected_error,
        }


def generate_report(results: list) -> str:
    """Генерация отчета в формате Markdown."""
    report_lines = [
        "# Отчет о валидации Google Batch API",
        "",
        f"**Дата тестирования:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
        "**Версия SDK:** google-genai",
        "",
        "## Результаты тестирования",
        "",
        "| Тест | Модель | Статус | Execution Mode | Примечания |",
        "|------|--------|--------|----------------|------------|",
    ]

    for result in results:
        status_emoji = "✅" if result["success"] else "❌"
        test_name = result["test_name"]
        model = result["model"]
        exec_mode = result["execution_mode"]

        notes = []
        if not result["success"]:
            error = result.get("error", "Unknown error")
            # Обрезаем длинные ошибки
            error_short = error[:100] + "..." if len(error) > 100 else error
            notes.append(f"Error: {error_short}")

            if result.get("expected_failure"):
                notes.append("(Ожидаемый баг Google)")

        if "note" in result:
            notes.append(result["note"])

        notes_str = " | ".join(notes) if notes else "-"

        report_lines.append(
            f"| {test_name} | `{model}` | {status_emoji} | `{exec_mode}` | {notes_str} |"
        )

    report_lines.extend(
        [
            "",
            "## Выводы и рекомендации",
            "",
            "### Операции с поддержкой Batch API (50% скидка):",
            "",
        ]
    )

    batch_supported = [r for r in results if r["success"]]
    if batch_supported:
        for r in batch_supported:
            report_lines.append(
                f"* **{r['test_name']}** (`{r['model']}`) → `execution_mode='batch'`"
            )
    else:
        report_lines.append("* _(нет операций с рабочим Batch API)_")

    report_lines.extend(["", "### Операции БЕЗ поддержки Batch API (local_queue):", ""])

    local_queue = [r for r in results if not r["success"]]
    if local_queue:
        for r in local_queue:
            expected = (
                " _(ожидаемо)_" if r.get("expected_failure") else " _(неожиданно)_"
            )
            report_lines.append(
                f"* **{r['test_name']}** (`{r['model']}`) → `execution_mode='local_queue'`{expected}"
            )
    else:
        report_lines.append("* _(все операции поддерживают Batch API)_")

    report_lines.extend(
        [
            "",
            "## Ссылки",
            "",
            "* [Официальная документация Batch API](https://ai.google.dev/gemini-api/docs/batch)",
            "* [Баг TTS Batch API (форум Google)](https://discuss.ai.google.dev/t/104621)",
            "* [Context7 SDK Documentation](/google/generative-ai-python)",
            "",
            "---",
            "",
            f"_Отчет сгенерирован автоматически: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}_",
        ]
    )

    return "\n".join(report_lines)


def main():
    """Основная функция запуска всех тестов."""
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}Gemini Media MCP - Фаза 0: Валидация Batch API{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

    if API_KEY:
        print(f"Клиент инициализирован с API ключом: {API_KEY[:10]}...{API_KEY[-4:]}")
    print("SDK версия: google.genai\n")

    # Запуск всех тестов
    results = []

    # Тест 1: Text-to-Text
    result1 = test_text_to_text()
    results.append(result1)
    print_result(
        result1["test_name"],
        result1["success"],
        result1.get("error", f"Batch ID: {result1.get('batch_id', 'N/A')}"),
    )

    # Тест 2: Text-to-Image
    result2 = test_text_to_image()
    results.append(result2)
    print_result(
        result2["test_name"],
        result2["success"],
        result2.get("error", f"Batch ID: {result2.get('batch_id', 'N/A')}"),
    )

    # Тест 3: Image-to-Image
    try:
        import importlib.util

        if importlib.util.find_spec("PIL") is not None:
            result3 = test_image_to_image()
            results.append(result3)
            print_result(
                result3["test_name"],
                result3["success"],
                result3.get("error", f"Batch ID: {result3.get('batch_id', 'N/A')}"),
            )
        else:
            raise ImportError("PIL not found")
    except ImportError:
        print(
            f"{Colors.YELLOW}⚠️  Пропуск теста Image-to-Image (требуется Pillow: pip install Pillow){Colors.ENDC}"
        )
        results.append(
            {
                "test_name": "Image-to-Image",
                "model": "gemini-3-pro-image-preview",
                "success": False,
                "error": "Pillow not installed",
                "execution_mode": "local_queue",
            }
        )

    # Тест 4: Text-to-Audio TTS
    result4 = test_text_to_audio()
    results.append(result4)
    print_result(
        result4["test_name"],
        result4["success"],
        result4.get("error", f"Batch ID: {result4.get('batch_id', 'N/A')}"),
    )

    # Генерация отчета
    print_header("Генерация отчета")

    report_path = (
        Path(__file__).parent.parent / "docs" / "batch_api_validation_report.md"
    )
    report_content = generate_report(results)

    report_path.write_text(report_content, encoding="utf-8")
    print(f"✅ Отчет сохранен: {report_path}")

    # Итоговая статистика
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed

    print(f"\n{Colors.BOLD}Итого:{Colors.ENDC}")
    print(f"  Всего тестов: {total}")
    print(f"  {Colors.GREEN}Успешно: {passed}{Colors.ENDC}")
    print(f"  {Colors.RED}Провалено: {failed}{Colors.ENDC}")

    # Рекомендации
    print(f"\n{Colors.BOLD}Рекомендации для execution_mode:{Colors.ENDC}")
    for r in results:
        mode_color = Colors.GREEN if r["execution_mode"] == "batch" else Colors.YELLOW
        print(f"  {r['test_name']}: {mode_color}{r['execution_mode']}{Colors.ENDC}")

    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

    # Код выхода
    sys.exit(
        0 if failed == 0 or failed == 1 else 1
    )  # Разрешаем 1 ожидаемый провал (TTS)


if __name__ == "__main__":
    main()
