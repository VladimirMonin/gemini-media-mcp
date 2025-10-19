import pytest
import os
import sys
import time
from pathlib import Path

# Константа таймаута между вызовами API для предотвращения rate limiting
API_CALL_TIMEOUT = 10  # секунд

# Добавляем корневую директорию проекта в sys.path, чтобы можно было импортировать модули
# Это нужно, если pytest запускается не из корня проекта
# или если структура пакетов не позволяет прямое импортирование
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Попробуем импортировать, но обернем в pytest.importorskip, если что-то пойдет не так
try:
    from config import (
        GEMINI_API_KEY,
        DEFAULT_GEMINI_MODEL,
        AVAILABLE_IMAGE_ANALYSIS_PROMPTS,
    )
    from modules.image_analysis import ImageAnalysisModule
    from utils.gemini_client import GeminiClient
    from utils.file_utils import (
        get_file_mime_type,
        is_image_valid,
        SUPPORTED_IMAGE_MIME_TYPES,
    )
except ImportError as e:
    # Если не удалось импортировать, пропустим эти тесты с сообщением об ошибке
    pytest.importorskip(
        "gemini_image_mcp_modules", reason=f"Не удалось импортировать модули: {e}"
    )


# --- Тесты для утилит ---
class TestFileUtils:
    """Тесты для утилит работы с файлами."""

    def test_get_file_mime_type_jpg(self):
        """Проверка определения MIME типа для JPG."""
        # Создаем временный файл
        temp_jpg = Path("temp_test.jpg")
        temp_jpg.write_bytes(
            b"fake jpg content"
        )  # minimal jpg header would be better for real test
        mime_type = get_file_mime_type(str(temp_jpg))
        assert mime_type == "image/jpeg"
        temp_jpg.unlink()  # Удаляем временный файл

    def test_get_file_mime_type_png(self):
        """Проверка определения MIME типа для PNG."""
        temp_png = Path("temp_test.png")
        temp_png.write_bytes(b"fake png content")
        mime_type = get_file_mime_type(str(temp_png))
        assert mime_type == "image/png"
        temp_png.unlink()

    def test_get_file_mime_type_unknown(self):
        """Проверка определения MIME типа для неизвестного файла."""
        temp_unknown = Path("temp_test.xyz")
        temp_unknown.write_text("some content")
        mime_type = get_file_mime_type(str(temp_unknown))
        assert mime_type == "application/octet-stream"
        temp_unknown.unlink()

    def test_is_image_valid_valid_jpg(self, tmp_path):
        """Проверка валидации корректного JPG файла."""
        img_file = tmp_path / "valid.jpg"
        img_file.write_bytes(b"fake jpg content")
        assert is_image_valid(str(img_file)) is True

    def test_is_image_valid_valid_png(self, tmp_path):
        """Проверка валидации корректного PNG файла."""
        img_file = tmp_path / "valid.png"
        img_file.write_bytes(b"fake png content")
        assert is_image_valid(str(img_file)) is True

    def test_is_image_valid_non_existent(self):
        """Проверка валидации несуществующего файла."""
        assert is_image_valid("non_existent_file.jpg") is False

    def test_is_image_valid_not_an_image(self, tmp_path):
        """Проверка валидации файла, не являющегося изображением."""
        text_file = tmp_path / "not_an_image.txt"
        text_file.write_text("This is not an image.")
        assert is_image_valid(str(text_file)) is False

    def test_supported_image_mime_types(self):
        """Проверка списка поддерживаемых MIME типов."""
        assert "image/jpeg" in SUPPORTED_IMAGE_MIME_TYPES
        assert "image/png" in SUPPORTED_IMAGE_MIME_TYPES
        assert "text/plain" not in SUPPORTED_IMAGE_MIME_TYPES


# --- Тесты для ImageAnalysisModule и GeminiClient (интеграционные) ---
@pytest.fixture(scope="session")
def image_analyzer():
    """Фикстура для создания экземпляра ImageAnalysisModule."""
    if not GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY не установлен. Пропускаем интеграционные тесты.")
    try:
        analyzer = ImageAnalysisModule(model_name=DEFAULT_GEMINI_MODEL)
        return analyzer
    except ValueError as e:
        pytest.skip(f"Не удалось инициализировать ImageAnalysisModule: {e}")


@pytest.fixture
def test_image_path():
    """Фикстура с путем к тестовому изображению котика."""
    # Путь относительно корня проекта
    return str(PROJECT_ROOT / "tests" / "cat.jpg")


class TestImageAnalysis:
    """Тесты для модуля анализа изображений."""

    def test_image_analyzer_initialization(self, image_analyzer):
        """Проверка инициализации ImageAnalysisModule."""
        assert image_analyzer is not None
        assert image_analyzer.model_name == DEFAULT_GEMINI_MODEL

    def test_gemini_client_initialization(self, image_analyzer):
        """Проверка инициализации GeminiClient внутри модуля."""
        assert image_analyzer.gemini_client is not None
        assert image_analyzer.gemini_client.model_name == DEFAULT_GEMINI_MODEL

    @pytest.mark.dependency(depends=["test_image_analyzer_initialization"])
    def test_analyze_image_basic(self, image_analyzer, test_image_path):
        """Базовый тест анализа изображения. Проверяем, что не возникает ошибок."""
        if not os.path.exists(test_image_path):
            pytest.skip(f"Тестовое изображение {test_image_path} не найдено.")

        time.sleep(API_CALL_TIMEOUT)  # Ждём перед вызовом API

        result = image_analyzer.analyze(
            image_path=test_image_path,
            user_prompt="Опиши, что на этом изображении.",
            system_instruction_name="default",
        )
        assert (
            "error" not in result
        ), f"Анализ изображения завершился ошибкой: {result.get('error')}"
        assert "raw_response" in result or isinstance(
            result, dict
        ), "Ответ должен быть словарем или содержать raw_response"

    @pytest.mark.dependency(depends=["test_analyze_image_basic"])
    def test_analyze_image_english_prompt(self, image_analyzer, test_image_path):
        """Тест анализа с английским промтом и проверкой 'cat'."""
        if not os.path.exists(test_image_path):
            pytest.skip(f"Тестовое изображение {test_image_path} не найдено.")

        time.sleep(API_CALL_TIMEOUT)  # Ждём перед вызовом API

        result = image_analyzer.analyze(
            image_path=test_image_path,
            user_prompt="What animal is this? Describe it briefly.",
            system_instruction_name="default",  # или "technical" если он лучше подходит
        )
        assert (
            "error" not in result
        ), f"Анализ изображения завершился ошибкой: {result.get('error')}"

        # Извлекаем текст из полей alt_text и detailed_analysis
        alt_text = result.get("alt_text", "")
        detailed_analysis = result.get("detailed_analysis", "")
        full_response_text = f"{alt_text} {detailed_analysis}".lower()

        # Проверяем наличие слова "cat" ИЛИ "кот" (модель может ответить на разных языках)
        assert (
            "cat" in full_response_text
            or "кот" in full_response_text
            or "котенок" in full_response_text
        ), f"В ответе не найдено слово 'cat' или 'кот'. Ответ: {result}"

    @pytest.mark.dependency(depends=["test_analyze_image_basic"])
    def test_analyze_image_russian_prompt(self, image_analyzer, test_image_path):
        """Тест анализа с русским промтом и проверкой 'кот'."""
        if not os.path.exists(test_image_path):
            pytest.skip(f"Тестовое изображение {test_image_path} не найдено.")

        time.sleep(API_CALL_TIMEOUT)  # Ждём перед вызовом API

        result = image_analyzer.analyze(
            image_path=test_image_path,
            user_prompt="Какое животное на этом фото? Кратко опиши.",
            system_instruction_name="default",
        )
        assert (
            "error" not in result
        ), f"Анализ изображения завершился ошибкой: {result.get('error')}"

        # Извлекаем текст из полей alt_text и detailed_analysis
        alt_text = result.get("alt_text", "")
        detailed_analysis = result.get("detailed_analysis", "")
        full_response_text = f"{alt_text} {detailed_analysis}".lower()

        # Проверяем наличие слова "кот" ИЛИ "котенок" (модель должна определить животное)
        assert (
            "кот" in full_response_text or "котенок" in full_response_text
        ), f"В ответе не найдено слово 'кот' или 'котенок'. Ответ: {result}"

    def test_analyze_image_custom_system_instruction(
        self, image_analyzer, test_image_path
    ):
        """Тест анализа с кастомной системной инструкцией."""
        if not os.path.exists(test_image_path):
            pytest.skip(f"Тестовое изображение {test_image_path} не найдено.")

        time.sleep(API_CALL_TIMEOUT)  # Ждём перед вызовом API

        custom_system_prompt = (
            "Ты — ветеринар. Опиши породу животного и его возможные болезни."
        )
        result = image_analyzer.analyze(
            image_path=test_image_path,
            user_prompt="Что это за животное?",
            system_instruction_override=custom_system_prompt,
        )
        assert (
            "error" not in result
        ), f"Анализ изображения завершился ошибкой: {result.get('error')}"

        # Извлекаем текст из полей alt_text, detailed_analysis и raw_response
        alt_text = result.get("alt_text", "")
        detailed_analysis = result.get("detailed_analysis", "")
        raw_response = result.get("raw_response", "")
        full_response_text = f"{alt_text} {detailed_analysis} {raw_response}".lower()

        # Проверим, что модель отреагировала на кастомную инструкцию
        # Ищем хотя бы одно ключевое слово из тематики ветеринарии
        # Учитываем варианты написания с "е" и "ё"
        keywords = [
            "порода",
            "болезн",
            "ветеринар",
            "здоровье",
            "кошк",
            "котен",
            "котён",
            "мейн",
        ]
        assert any(
            keyword in full_response_text for keyword in keywords
        ), f"Кастомная системная инструкция не повлияла на ответ. Ответ: {result}"


# Запуск тестов:
# В терминале, находясь в корневой директории проекта (c:\PY\gemini_image_mcp):
# pytest
# Или с более подробным выводом:
# pytest -v
# Или запустить только тесты для утилит:
# pytest tests/test_gemini_analyzer.py::TestFileUtils -v
