"""
Тесты для TTS Queue Processor (Phase 3, Step 4).

Тестирует:
- process_local_queue_tasks() с mock режимом
- Динамический rate limiting из operation_types
- Валидацию input_payload (text, voice, model_type)
- Сохранение аудио в media/tts/
- Обработку ошибок (пустой текст, длинный текст, невалидный голос)
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from pathlib import Path

from worker.processors.queue_processor import (
    process_local_queue_tasks,
    _validate_tts_payload,
    _get_rate_limit_delay,
    _save_tts_audio,
)
import config


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def tts_task_data():
    """Данные для создания TTS задачи."""
    task_id = str(uuid4())
    batch_id = str(uuid4())
    return {
        "task_id": task_id,
        "batch_id": batch_id,
        "operation_type": "TTS_GEN_QUEUE",
        "input_payload": {
            "text": "Hello, this is a test.",
            "voice": "Puck",
            "model_type": "flash",
        },
        "target_path": f"media/tts/{task_id}.wav",
    }


@pytest.fixture
def mock_genai_response():
    """Мок ответа от Gemini TTS API.

    Returns:
        MagicMock: Объект с декодированными PCM bytes (как реальный API).
    """
    import base64

    mock_response = MagicMock()
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [MagicMock()]
    # RAW PCM bytes (как реальный Gemini TTS API)
    mock_response.candidates[0].content.parts[0].inline_data = MagicMock()
    mock_response.candidates[0].content.parts[0].inline_data.data = base64.b64decode(
        "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA="
    )
    return mock_response


# ==============================================================================
# Тесты валидации payload
# ==============================================================================


class TestValidateTTSPayload:
    """Тесты валидации input_payload."""

    def test_valid_payload_with_defaults(self):
        """Валидный payload с дефолтными значениями."""
        payload = {"text": "Hello world"}
        text, voice, model_type = _validate_tts_payload(payload)

        assert text == "Hello world"
        assert voice == config.DEFAULT_VOICE.capitalize()
        assert model_type == config.DEFAULT_TTS_MODEL

    def test_valid_payload_with_all_fields(self):
        """Валидный payload со всеми полями."""
        payload = {
            "text": "Test message",
            "voice": "puck",
            "model_type": "pro",
        }
        text, voice, model_type = _validate_tts_payload(payload)

        assert text == "Test message"
        assert voice == "Puck"  # capitalize
        assert model_type == "pro"

    def test_empty_text_raises_error(self):
        """Пустой текст вызывает ошибку."""
        payload = {"text": ""}
        with pytest.raises(ValueError, match="TTS text is empty"):
            _validate_tts_payload(payload)

    def test_whitespace_text_raises_error(self):
        """Текст из пробелов вызывает ошибку."""
        payload = {"text": "   \n\t  "}
        with pytest.raises(ValueError, match="TTS text is empty"):
            _validate_tts_payload(payload)

    def test_missing_text_raises_error(self):
        """Отсутствующий текст вызывает ошибку."""
        payload = {"voice": "Puck"}
        with pytest.raises(ValueError, match="TTS text is empty"):
            _validate_tts_payload(payload)

    def test_too_long_text_raises_error(self):
        """Слишком длинный текст (>5000 символов) вызывает ошибку."""
        payload = {"text": "x" * 5001}
        with pytest.raises(ValueError, match="TTS text too long"):
            _validate_tts_payload(payload)

    def test_exactly_5000_chars_is_valid(self):
        """Ровно 5000 символов — валидно."""
        payload = {"text": "x" * 5000}
        text, _, _ = _validate_tts_payload(payload)
        assert len(text) == 5000

    def test_unknown_model_type_uses_default(self):
        """Неизвестный model_type заменяется на дефолт."""
        payload = {"text": "Test", "model_type": "unknown_model"}
        _, _, model_type = _validate_tts_payload(payload)
        assert model_type == config.DEFAULT_TTS_MODEL


# ==============================================================================
# Тесты rate limiting
# ==============================================================================


class TestRateLimitDelay:
    """Тесты динамического rate limiting из БД."""

    def test_rate_limit_from_db(self, temp_db):
        """Rate limit вычисляется из rpm_limit в operation_types."""
        # TTS_GEN_QUEUE имеет rpm_limit=10 в seed_data
        delay = _get_rate_limit_delay(temp_db, "TTS_GEN_QUEUE")

        # 60 / 10 = 6.0 секунд
        assert delay == 6.0

    def test_unknown_operation_uses_default(self, temp_db):
        """Неизвестная операция использует дефолт (20 сек = 3 RPM)."""
        delay = _get_rate_limit_delay(temp_db, "UNKNOWN_OPERATION")
        assert delay == 20.0

    def test_null_rpm_limit_uses_default(self, temp_db):
        """NULL rpm_limit (batch операции) использует дефолт."""
        # IMG_GEN_BATCH имеет rpm_limit=NULL
        delay = _get_rate_limit_delay(temp_db, "IMG_GEN_BATCH")
        assert delay == 20.0


# ==============================================================================
# Тесты сохранения аудио
# ==============================================================================


class TestSaveTTSAudio:
    """Тесты сохранения TTS аудио в файл."""

    def test_save_to_default_path(self, tmp_path, monkeypatch):
        """Сохранение в media/tts/{task_id}.wav если target_path не указан."""
        import base64

        # Подменить OUTPUT_TTS_DIR на tmp_path
        monkeypatch.setattr(config, "OUTPUT_TTS_DIR", str(tmp_path / "media" / "tts"))

        task_id = str(uuid4())
        # RAW PCM bytes (как реальный API)
        audio_pcm = base64.b64decode(
            "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA="
        )

        result_path = _save_tts_audio(task_id, audio_pcm, target_path=None)

        assert Path(result_path).exists()
        assert task_id in result_path
        assert result_path.endswith(".wav")

    def test_save_to_custom_path(self, tmp_path):
        """Сохранение в указанный target_path."""
        import base64

        custom_path = tmp_path / "custom" / "audio.wav"
        task_id = str(uuid4())
        audio_pcm = base64.b64decode(
            "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA="
        )

        result_path = _save_tts_audio(task_id, audio_pcm, target_path=str(custom_path))

        assert Path(result_path).exists()
        assert "custom" in result_path
        assert result_path.endswith("audio.wav")

    def test_creates_parent_directories(self, tmp_path, monkeypatch):
        """Создаёт родительские директории если их нет."""
        import base64

        deep_path = tmp_path / "a" / "b" / "c" / "d"
        monkeypatch.setattr(config, "OUTPUT_TTS_DIR", str(deep_path))

        task_id = str(uuid4())
        audio_pcm = base64.b64decode(
            "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA="
        )

        result_path = _save_tts_audio(task_id, audio_pcm, target_path=None)

        assert Path(result_path).exists()
        assert deep_path.exists()


# ==============================================================================
# Тесты основного процессора (mock mode)
# ==============================================================================


class TestProcessLocalQueueTasks:
    """Тесты process_local_queue_tasks() в mock режиме."""

    def test_empty_queue_returns_zero(self, temp_db):
        """Пустая очередь возвращает 0."""
        result = process_local_queue_tasks(temp_db, mock_mode=True)
        assert result == 0

    def test_processes_tts_task_mock_mode(
        self, temp_db, tts_task_data, tmp_path, monkeypatch
    ):
        """Обрабатывает TTS задачу в mock режиме."""
        # Подменить OUTPUT_TTS_DIR
        monkeypatch.setattr(config, "OUTPUT_TTS_DIR", str(tmp_path / "media" / "tts"))

        # Создать batch и task
        temp_db.create_batch(
            tts_task_data["batch_id"],
            tts_task_data["operation_type"],
            total_tasks=1,
        )
        temp_db.create_task(
            tts_task_data["task_id"],
            tts_task_data["batch_id"],
            tts_task_data["operation_type"],
            tts_task_data["input_payload"],
            tts_task_data["target_path"],
        )

        # Обработать
        result = process_local_queue_tasks(temp_db, mock_mode=True)

        assert result == 1

        # Проверить статус задачи
        task = temp_db.get_task(tts_task_data["task_id"])
        assert task["status"] == "COMPLETED"

    def test_failed_task_marked_as_failed(self, temp_db):
        """Задача с пустым текстом помечается как FAILED."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        # Создать batch и task с пустым текстом
        temp_db.create_batch(batch_id, "TTS_GEN_QUEUE", total_tasks=1)
        temp_db.create_task(
            task_id,
            batch_id,
            "TTS_GEN_QUEUE",
            {"text": ""},  # Пустой текст
            f"media/tts/{task_id}.wav",
        )

        # Обработать
        result = process_local_queue_tasks(temp_db, mock_mode=True)

        assert result == 1  # Задача обработана (с ошибкой)

        # Проверить статус
        task = temp_db.get_task(task_id)
        assert task["status"] == "FAILED"
        assert "empty" in task["error_details"].lower()

    def test_only_processes_local_queue_tasks(self, temp_db):
        """Не обрабатывает batch задачи (только local_queue)."""
        batch_id = str(uuid4())
        task_id = str(uuid4())

        # Создать batch задачу (не local_queue)
        temp_db.create_batch(batch_id, "IMG_GEN_BATCH", total_tasks=1)
        temp_db.create_task(
            task_id,
            batch_id,
            "IMG_GEN_BATCH",
            {"prompt": "test"},
            f"/tmp/{task_id}.png",
        )

        # Обработать
        result = process_local_queue_tasks(temp_db, mock_mode=True)

        # Не должно обработаться (это batch задача)
        assert result == 0


# ==============================================================================
# Интеграционные тесты (с мок API)
# ==============================================================================


class TestProcessLocalQueueTasksWithMockedAPI:
    """Тесты с моком Gemini API (не mock_mode, а реальный мок)."""

    @patch("worker.processors.queue_processor.genai")
    def test_real_api_call_mocked(
        self,
        mock_genai,
        temp_db,
        tts_task_data,
        tmp_path,
        monkeypatch,
        mock_genai_response,
    ):
        """Тест реального API вызова через мок.

        Note:
            Использует mock_genai_response фикстуру, которая возвращает bytes.
        """
        # Подменить OUTPUT_TTS_DIR
        monkeypatch.setattr(config, "OUTPUT_TTS_DIR", str(tmp_path / "media" / "tts"))

        # Настроить мок
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_genai_response
        mock_genai.Client.return_value = mock_client

        # Создать batch и task
        temp_db.create_batch(
            tts_task_data["batch_id"],
            tts_task_data["operation_type"],
            total_tasks=1,
        )
        temp_db.create_task(
            tts_task_data["task_id"],
            tts_task_data["batch_id"],
            tts_task_data["operation_type"],
            tts_task_data["input_payload"],
            tts_task_data["target_path"],
        )

        # Мокаем time.sleep чтобы тест не ждал
        with patch("worker.processors.queue_processor.time.sleep"):
            result = process_local_queue_tasks(temp_db, mock_mode=False)

        assert result == 1

        # Проверить вызов API
        mock_genai.Client.assert_called_once()
        mock_client.models.generate_content.assert_called_once()

        # Проверить статус задачи
        task = temp_db.get_task(tts_task_data["task_id"])
        assert task["status"] == "COMPLETED"
        assert task["local_path"] is not None

        # Проверить файл
        assert Path(task["local_path"]).exists()

    @patch("worker.processors.queue_processor.genai")
    def test_api_error_marks_task_failed(
        self, mock_genai, temp_db, tts_task_data, tmp_path, monkeypatch
    ):
        """Ошибка API помечает задачу как FAILED."""
        # Подменить OUTPUT_TTS_DIR
        monkeypatch.setattr(config, "OUTPUT_TTS_DIR", str(tmp_path / "media" / "tts"))

        # Настроить мок с ошибкой
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("API Error")
        mock_genai.Client.return_value = mock_client

        # Создать batch и task
        temp_db.create_batch(
            tts_task_data["batch_id"],
            tts_task_data["operation_type"],
            total_tasks=1,
        )
        temp_db.create_task(
            tts_task_data["task_id"],
            tts_task_data["batch_id"],
            tts_task_data["operation_type"],
            tts_task_data["input_payload"],
            tts_task_data["target_path"],
        )

        # Обработать
        result = process_local_queue_tasks(temp_db, mock_mode=False)

        assert result == 1

        # Проверить статус
        task = temp_db.get_task(tts_task_data["task_id"])
        assert task["status"] == "FAILED"
        assert "API Error" in task["error_details"]
