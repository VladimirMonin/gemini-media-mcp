"""Tests for backup_manager module."""

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
    """Tests for description sanitization."""

    def test_simple_prompt(self):
        """Test simple prompt extraction."""
        result = sanitize_description("A beautiful sunset over the ocean")
        assert result == "A_beautiful_sunset_o"

    def test_long_prompt(self):
        """Test truncation to 20 chars."""
        result = sanitize_description(
            "This is a very long prompt that should be truncated"
        )
        assert len(result) <= 20
        assert result == "This_is_a_very_long"

    def test_special_characters(self):
        """Test special character replacement."""
        result = sanitize_description("Hello, world! @#$%")
        assert result == "Hello__world"

    def test_multiple_spaces(self):
        """Test multiple spaces collapse."""
        result = sanitize_description("Hello    world")
        assert result == "Hello_world"

    def test_empty_string(self):
        """Test empty string handling."""
        result = sanitize_description("")
        assert result == "generated"

    def test_only_special_chars(self):
        """Test string with only special chars."""
        result = sanitize_description("@#$%^&*()")
        assert result == "generated"


class TestCreateBackupFilename:
    """Tests for backup filename generation."""

    def test_image_filename_format(self):
        """Test filename format for images."""
        filename = create_backup_filename("image", "png", "test prompt")

        # Should have format: YYYY-MM-DD_HH-MM-SS_description.png
        assert filename.endswith(".png")
        assert "test_prompt" in filename.lower()

    def test_audio_filename_format(self):
        """Test filename format for audio."""
        filename = create_backup_filename("audio", "wav", "audio test")

        assert filename.endswith(".wav")
        assert "audio_test" in filename.lower()

    def test_different_extensions(self):
        """Test various file extensions."""
        filename_png = create_backup_filename("image", "png")
        filename_wav = create_backup_filename("audio", "wav")
        filename_jpg = create_backup_filename("image", "jpg")

        assert filename_png.endswith(".png")
        assert filename_wav.endswith(".wav")
        assert filename_jpg.endswith(".jpg")

    def test_timestamp_uniqueness(self):
        """Test that filenames generated in sequence are unique."""
        filename1 = create_backup_filename("image", "png", "test")
        time.sleep(1)  # Wait 1 second
        filename2 = create_backup_filename("image", "png", "test")

        # Should have different timestamps
        assert filename1 != filename2


class TestSaveMetadataJson:
    """Tests for JSON metadata saving."""

    def test_save_metadata(self, tmp_path):
        """Test metadata JSON creation."""
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
    """Tests for complete backup workflow."""

    def test_backup_image_file(self, tmp_path):
        """Test backing up an image file."""
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
        """Test backing up an audio file."""
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
        """Test that multiple backups create unique files."""
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
        """Test that backup fails gracefully with missing file."""
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
