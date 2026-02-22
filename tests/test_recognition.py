"""Интеграционные тесты распознавания медиа через Gemini API.

Требуется реальный GEMINI_API_KEY в .env файле.
Тестовые ассеты: tests/cat.jpg, tests/image.png, tests/test_auido.mp3

Используется gemini-2.5-flash-lite — самая дешёвая модель для тестов.

Запуск:
    pytest tests/test_recognition.py -v -s
    pytest tests/test_recognition.py -v -s -k "test_image"
"""

import json
import os
import sys
import time

import pytest

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DEFAULT_GEMINI_MODEL, GEMINI_MODELS

# Самая дешёвая модель для тестов
TEST_MODEL = "gemini-2.5-flash-lite"

# Пауза между API вызовами (rate limit protection)
API_CALL_DELAY = 3.0

# Путь к тестовым файлам
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
CAT_IMAGE = os.path.join(TESTS_DIR, "cat.jpg")
IMAGE_PNG = os.path.join(TESTS_DIR, "image.png")
AUDIO_FILE = os.path.join(TESTS_DIR, "test_auido.mp3")


def has_api_key() -> bool:
    """Проверяет наличие реального API ключа."""
    from config import GEMINI_API_KEY

    return bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_key_here")


# Пропуск всех тестов если нет ключа
pytestmark = pytest.mark.skipif(
    not has_api_key(), reason="GEMINI_API_KEY не настроен в .env"
)


@pytest.fixture(autouse=True)
def api_delay():
    """Задержка между API вызовами для rate limit."""
    yield
    time.sleep(API_CALL_DELAY)


# ============================================================================
# Тесты анализа изображений
# ============================================================================


class TestImageAnalysis:
    """Тесты распознавания изображений через analyze_image."""

    def test_cat_image_default_model(self):
        """Анализ cat.jpg с дешёвой моделью gemini-2.5-flash-lite."""
        from tools.image_analyzer import analyze_image
        from models.analysis import ImageAnalysisResponse

        assert os.path.exists(CAT_IMAGE), f"Тестовый файл не найден: {CAT_IMAGE}"

        result = analyze_image(
            image_path=CAT_IMAGE,
            user_prompt="Describe what you see in this image. Is there a cat?",
            model_name=TEST_MODEL,
        )

        assert isinstance(result, ImageAnalysisResponse), (
            f"Ожидался ImageAnalysisResponse, получен {type(result).__name__}: {result}"
        )
        assert result.alt_text, "alt_text не должен быть пустым"
        assert result.detailed_analysis, "detailed_analysis не должен быть пустым"

        # Проверяем, что модель увидела кота
        text = (result.alt_text + " " + result.detailed_analysis).lower()
        assert any(
            word in text for word in ["cat", "кот", "kitten", "котен", "feline"]
        ), f"Модель не распознала кота в изображении. Ответ: {text[:200]}"
        print(f"\n✅ Модель: {TEST_MODEL}")
        print(f"📝 Alt text: {result.alt_text[:100]}")
        print(f"📝 Analysis: {result.detailed_analysis[:200]}")

    def test_cat_image_media_resolution_high(self):
        """Анализ cat.jpg с media_resolution='high'."""
        from tools.image_analyzer import analyze_image
        from models.analysis import ImageAnalysisResponse

        result = analyze_image(
            image_path=CAT_IMAGE,
            user_prompt="Describe this image in detail.",
            media_resolution="high",
            model_name=TEST_MODEL,
        )

        assert isinstance(result, ImageAnalysisResponse)
        assert result.alt_text
        print(f"\n✅ media_resolution=high, model={TEST_MODEL}")
        print(f"📝 Alt text: {result.alt_text[:100]}")

    def test_cat_image_media_resolution_low(self):
        """Анализ cat.jpg с media_resolution='low' — экономия токенов."""
        from tools.image_analyzer import analyze_image
        from models.analysis import ImageAnalysisResponse

        result = analyze_image(
            image_path=CAT_IMAGE,
            user_prompt="What animal is in this image?",
            media_resolution="low",
            model_name=TEST_MODEL,
        )

        assert isinstance(result, ImageAnalysisResponse)
        text = (result.alt_text + " " + result.detailed_analysis).lower()
        assert any(word in text for word in ["cat", "кот", "kitten", "feline"]), (
            f"Даже с low resolution модель должна видеть кота. Ответ: {text[:200]}"
        )
        print(f"\n✅ media_resolution=low, model={TEST_MODEL}")
        print(f"📝 Alt text: {result.alt_text[:100]}")

    def test_png_image(self):
        """Анализ image.png — проверка поддержки PNG."""
        from tools.image_analyzer import analyze_image
        from models.analysis import ImageAnalysisResponse

        if not os.path.exists(IMAGE_PNG):
            pytest.skip(f"Файл не найден: {IMAGE_PNG}")

        result = analyze_image(
            image_path=IMAGE_PNG,
            user_prompt="Describe what you see in this image.",
            model_name=TEST_MODEL,
        )

        assert isinstance(result, ImageAnalysisResponse), (
            f"Ожидался ImageAnalysisResponse, получен {type(result).__name__}: {result}"
        )
        assert result.alt_text, "alt_text не должен быть пустым"
        print(f"\n✅ PNG анализ успешен, model={TEST_MODEL}")
        print(f"📝 Alt text: {result.alt_text[:100]}")

    def test_image_with_specific_model(self):
        """Анализ с явно указанной моделью gemini-2.5-flash."""
        from tools.image_analyzer import analyze_image
        from models.analysis import ImageAnalysisResponse

        result = analyze_image(
            image_path=CAT_IMAGE,
            user_prompt="What is in this image?",
            model_name="gemini-2.5-flash-lite",
        )

        assert isinstance(result, ImageAnalysisResponse)
        assert result.alt_text
        print(f"\n✅ Модель: gemini-2.5-flash-lite")
        print(f"📝 Alt text: {result.alt_text[:100]}")

    def test_invalid_model_raises(self):
        """Невалидная модель должна вызвать ValueError."""
        from tools.image_analyzer import analyze_image

        with pytest.raises(ValueError, match="not supported"):
            analyze_image(
                image_path=CAT_IMAGE,
                user_prompt="test",
                model_name="nonexistent-model-123",
            )

    def test_invalid_image_path_raises(self):
        """Несуществующий файл должен вызвать ошибку."""
        from tools.image_analyzer import analyze_image

        with pytest.raises((ValueError, FileNotFoundError)):
            analyze_image(
                image_path="C:\\nonexistent\\fake_image.jpg",
                user_prompt="test",
            )


# ============================================================================
# Тесты анализа аудио
# ============================================================================


class TestAudioAnalysis:
    """Тесты распознавания аудио через analyze_audio."""

    def test_audio_default_model(self):
        """Анализ test_auido.mp3 с дешёвой моделью."""
        from tools.audio_analyzer import analyze_audio
        from models.analysis import AudioAnalysisResponse

        if not os.path.exists(AUDIO_FILE):
            pytest.skip(f"Файл не найден: {AUDIO_FILE}")

        result = analyze_audio(
            audio_path=AUDIO_FILE,
            user_prompt="Transcribe and analyze this audio.",
            model_name=TEST_MODEL,
        )

        assert isinstance(result, AudioAnalysisResponse), (
            f"Ожидался AudioAnalysisResponse, получен {type(result).__name__}: {result}"
        )
        assert result.title or result.summary, "Должен быть title или summary"
        print(f"\n✅ Audio модель: {TEST_MODEL}")
        print(f"📝 Title: {result.title}")
        print(f"📝 Summary: {str(result.summary)[:200]}")

    def test_audio_invalid_path_raises(self):
        """Несуществующий аудио файл должен вызвать FileNotFoundError."""
        from tools.audio_analyzer import analyze_audio

        with pytest.raises(FileNotFoundError):
            analyze_audio(audio_path="C:\\nonexistent\\fake.mp3")


# ============================================================================
# Тесты GeminiClient напрямую
# ============================================================================


class TestGeminiClient:
    """Тесты GeminiClient с media_resolution."""

    def test_generate_text(self):
        """Простая генерация текста."""
        from utils.gemini_client import GeminiClient

        client = GeminiClient(model_name=TEST_MODEL)
        result = client.generate_text("Say the word 'hello' and nothing else.")

        assert result, "Ответ не должен быть пустым"
        assert "hello" in result.lower(), f"Ожидалось 'hello' в ответе: {result}"
        print(f"\n✅ generate_text: {result[:50]}")

    def test_media_resolution_mapping(self):
        """Проверка маппинга строковых значений media_resolution."""
        from utils.gemini_client import GeminiClient
        from google.genai import types

        resolved = GeminiClient._resolve_media_resolution("high")
        assert resolved == types.MediaResolution.MEDIA_RESOLUTION_HIGH

        resolved = GeminiClient._resolve_media_resolution("medium")
        assert resolved == types.MediaResolution.MEDIA_RESOLUTION_MEDIUM

        resolved = GeminiClient._resolve_media_resolution("low")
        assert resolved == types.MediaResolution.MEDIA_RESOLUTION_LOW

        resolved = GeminiClient._resolve_media_resolution(None)
        assert resolved is None

        with pytest.raises(ValueError, match="Unknown media_resolution"):
            GeminiClient._resolve_media_resolution("ultra")

        print("\n✅ Все маппинги media_resolution корректны")

    def test_generate_content_with_image_and_resolution(self):
        """Анализ изображения через GeminiClient с media_resolution."""
        from utils.gemini_client import GeminiClient

        assert os.path.exists(CAT_IMAGE)

        client = GeminiClient(model_name=TEST_MODEL)
        result = client.generate_content(
            prompt="What animal is in this image? Answer in one word.",
            image_path=CAT_IMAGE,
            media_resolution="high",
        )

        assert result, "Ответ не должен быть пустым"
        assert any(word in result.lower() for word in ["cat", "кот", "kitten"]), (
            f"Модель не распознала кота: {result}"
        )
        print(f"\n✅ GeminiClient с media_resolution=high: {result[:50]}")


# ============================================================================
# Тесты конфигурации моделей
# ============================================================================


class TestModelConfig:
    """Тесты конфигурации моделей."""

    def test_gemini_3_flash_preview_in_models(self):
        """gemini-3-flash-preview должен быть в списке моделей."""
        assert "gemini-3-flash-preview" in GEMINI_MODELS

    def test_gemini_3_1_pro_preview_in_models(self):
        """gemini-3.1-pro-preview должен быть в списке моделей."""
        assert "gemini-3.1-pro-preview" in GEMINI_MODELS

    def test_default_model_is_gemini_3_flash(self):
        """Модель по умолчанию должна быть gemini-3-flash-preview."""
        assert DEFAULT_GEMINI_MODEL == "gemini-3-flash-preview"

    def test_all_models_present(self):
        """Все ожидаемые модели в списке."""
        expected = [
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-3-flash-preview",
            "gemini-3-pro-preview",
            "gemini-3.1-pro-preview",
        ]
        for model in expected:
            assert model in GEMINI_MODELS, f"Модель {model} отсутствует в GEMINI_MODELS"

    def test_image_tokens_pricing_has_gemini3(self):
        """image_tokens.py должен содержать Gemini 3 модели в pricing."""
        from utils.image_tokens import estimate_cost

        # Не должен падать для новых моделей
        result = estimate_cost(1000, "gemini-3-flash-preview")
        assert result["model"] == "gemini-3-flash-preview"
        assert result["estimated_input_cost_usd"] >= 0

        result = estimate_cost(1000, "gemini-3.1-pro-preview")
        assert result["model"] == "gemini-3.1-pro-preview"
        assert result["estimated_input_cost_usd"] > 0  # pro стоит дороже
