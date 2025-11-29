"""Тесты для модуля backup_manager.

Классы:
    TestSanitizeDescription — тесты санитизации описаний.
    TestCreateBackupFilename — тесты генерации имён файлов.
    TestSaveMetadataJson — тесты сохранения JSON метаданных.
    TestBackupGeneration — тесты полного workflow бэкапа.
"""

import pytest
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.backup_manager import (
    create_backup_filename,
    sanitize_description,
    backup_generation,
    save_metadata_json,
)


class TestSanitizeDescription:
    """Тесты санитизации описаний."""

    def test_simple_prompt(self):
        """Проверяет извлечение простого промпта."""
        result = sanitize_description("A beautiful sunset over the ocean")
        assert result == "A_beautiful_sunset_o"

    def test_long_prompt(self):
        """Проверяет обрезку до 20 символов."""
        result = sanitize_description(
            "This is a very long prompt that should be truncated"
        )
        assert len(result) <= 20
        assert result == "This_is_a_very_long"

    def test_special_characters(self):
        """Проверяет замену специальных символов."""
        result = sanitize_description("Hello, world! @#$%")
        assert result == "Hello__world"

    def test_multiple_spaces(self):
        """Проверяет схлопывание множественных пробелов."""
        result = sanitize_description("Hello    world")
        assert result == "Hello_world"

    def test_empty_string(self):
        """Проверяет обработку пустой строки."""
        result = sanitize_description("")
        assert result == "generated"

    def test_only_special_chars(self):
        """Проверяет строку только из спецсимволов."""
        result = sanitize_description("@#$%^&*()")
        assert result == "generated"


class TestCreateBackupFilename:
    """Тесты генерации имён backup файлов."""

    def test_image_filename_format(self):
        """Проверяет формат имени файла для изображений."""
        filename = create_backup_filename("image", "png", "test prompt")

        # Should have format: YYYY-MM-DD_HH-MM-SS_description.png
        assert filename.endswith(".png")
        assert "test_prompt" in filename.lower()

    def test_audio_filename_format(self):
        """Проверяет формат имени файла для аудио."""
        filename = create_backup_filename("audio", "wav", "audio test")

        assert filename.endswith(".wav")
        assert "audio_test" in filename.lower()

    def test_different_extensions(self):
        """Проверяет различные расширения файлов."""
        filename_png = create_backup_filename("image", "png")
        filename_wav = create_backup_filename("audio", "wav")
        filename_jpg = create_backup_filename("image", "jpg")

        assert filename_png.endswith(".png")
        assert filename_wav.endswith(".wav")
        assert filename_jpg.endswith(".jpg")

    def test_timestamp_uniqueness(self):
        """Проверяет уникальность имён файлов по времени."""
        filename1 = create_backup_filename("image", "png", "test")
        time.sleep(1)  # Wait 1 second
        filename2 = create_backup_filename("image", "png", "test")

        # Should have different timestamps
        assert filename1 != filename2


class TestSaveMetadataJson:
    """Тесты сохранения JSON метаданных."""

    def test_save_metadata(self, tmp_path):
        """Проверяет создание JSON метаданных."""
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(tmp_path / "test_image.png"),
            "parameters": {
                "prompt": "A test image",
                "model": "gemini-2.5-flash",
                "aspect_ratio": "16:9",
            },
        }

        json_path = tmp_path / "test_metadata.json"
        save_metadata_json(str(json_path), metadata)

        # Check JSON file exists
        assert json_path.exists()

        # Check JSON content
        with open(json_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["parameters"]["prompt"] == "A test image"
        assert loaded["parameters"]["model"] == "gemini-2.5-flash"
        assert "timestamp" in loaded


class TestBackupGeneration:
    """Тесты полного workflow бэкапа."""

    def test_backup_image_file(self, tmp_path):
        """Проверяет бэкап файла изображения."""
        # Create source file
        source_file = tmp_path / "original.png"
        source_file.write_bytes(b"fake png data")

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(source_file),
            "parameters": {
                "prompt": "Test image generation",
                "model": "gemini-2.5-flash",
            },
        }

        # Perform backup
        backup_path, metadata_path = backup_generation(
            original_path=str(source_file),
            file_type="image",
            metadata=metadata,
        )

        # Verify backup file exists
        assert os.path.exists(backup_path)
        assert backup_path.endswith(".png")

        # Verify content copied
        with open(backup_path, "rb") as f:
            assert f.read() == b"fake png data"

        # Verify JSON metadata exists
        assert os.path.exists(metadata_path)
        assert metadata_path.endswith(".json")

        with open(metadata_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            assert loaded["parameters"]["prompt"] == "Test image generation"

    def test_backup_audio_file(self, tmp_path):
        """Проверяет бэкап аудиофайла."""
        source_file = tmp_path / "original.wav"
        source_file.write_bytes(b"fake wav data")

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(source_file),
            "parameters": {
                "prompt": "Audio narration test",
                "yaml_script": "/path/to/script.yaml",
                "model": "gemini-2.5-flash-preview-tts",
            },
        }

        backup_path, metadata_path = backup_generation(
            original_path=str(source_file),
            file_type="audio",
            metadata=metadata,
        )

        assert os.path.exists(backup_path)
        assert backup_path.endswith(".wav")

        # Verify metadata
        assert os.path.exists(metadata_path)
        with open(metadata_path, "r") as f:
            loaded = json.load(f)
            assert loaded["parameters"]["yaml_script"] == "/path/to/script.yaml"

    def test_multiple_backups_dont_overwrite(self, tmp_path):
        """Проверяет, что множественные бэкапы создают уникальные файлы."""
        source_file = tmp_path / "source.png"
        source_file.write_bytes(b"data v1")

        metadata1 = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(source_file),
            "parameters": {"prompt": "Same prompt"},
        }

        # First backup
        backup1, _ = backup_generation(
            original_path=str(source_file),
            file_type="image",
            metadata=metadata1,
        )

        time.sleep(1)  # Wait to ensure different timestamp

        # Update source file
        source_file.write_bytes(b"data v2")

        metadata2 = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(source_file),
            "parameters": {"prompt": "Same prompt"},
        }

        # Second backup with same prompt
        backup2, _ = backup_generation(
            original_path=str(source_file),
            file_type="image",
            metadata=metadata2,
        )

        # Should create different files
        assert backup1 != backup2
        assert os.path.exists(backup1)
        assert os.path.exists(backup2)

        # Verify different content
        with open(backup1, "rb") as f:
            assert f.read() == b"data v1"

        with open(backup2, "rb") as f:
            assert f.read() == b"data v2"

    def test_backup_with_missing_file(self, tmp_path):
        """Проверяет, что бэкап с отсутствующим файлом завершается с ошибкой."""
        missing_file = tmp_path / "nonexistent.png"

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(missing_file),
            "parameters": {"prompt": "Test"},
        }

        with pytest.raises(FileNotFoundError):
            backup_generation(
                original_path=str(missing_file),
                file_type="image",
                metadata=metadata,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
