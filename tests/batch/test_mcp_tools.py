"""Tests for batch and queue MCP tools.

Tests cover:
- batch_generate_images: validation, task creation, DB integration
- queue_generate_audio: validation, task creation, voice handling
- check_task_status: task lookup, status reporting
- check_batch_progress: batch lookup, progress calculation
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

# Import tools
from tools.batch_tools import (
    batch_generate_images,
    queue_generate_audio,
    check_task_status,
    check_batch_progress,
    VALID_VOICES,
)
from config import VALID_ASPECT_RATIOS, VALID_RESOLUTIONS, TTS_MODELS, IMAGE_GEN_MODELS


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Mock DatabaseManager for testing."""
    with patch("tools.batch_tools.db") as mock:
        yield mock


@pytest.fixture
def sample_batch():
    """Sample batch data for testing."""
    return {
        "id": str(uuid4()),
        "operation_type": "IMG_GEN_BATCH",
        "status": "PROCESSING",
        "google_batch_id": "batches/abc123",
        "created_at": "2025-11-28 10:00:00",
        "completed_at": None,
    }


@pytest.fixture
def sample_task():
    """Sample task data for testing."""
    return {
        "id": str(uuid4()),
        "operation_type": "TTS_GEN_QUEUE",
        "status": "COMPLETED",
        "local_path": "media/tts/test.wav",
        "error_details": None,
        "created_at": "2025-11-28 10:00:00",
        "completed_at": "2025-11-28 10:00:05",
    }


# ============================================================================
# batch_generate_images Tests
# ============================================================================


class TestBatchGenerateImages:
    """Tests for batch_generate_images tool."""

    def test_creates_batch_with_valid_prompts(self, mock_db):
        """Should create batch with valid prompts."""
        prompts = ["A red car", "A blue motorcycle"]

        result = batch_generate_images(prompts=prompts)

        assert "batch_id" in result
        assert result["total_tasks"] == 2
        assert result["status"] == "PENDING"
        assert "estimated_cost" in result
        mock_db.create_batch_with_tasks.assert_called_once()

    def test_validates_minimum_prompts(self, mock_db):
        """Should reject less than 2 prompts."""
        with pytest.raises(ValueError, match="2-100 items"):
            batch_generate_images(prompts=["Single prompt"])

    def test_validates_maximum_prompts(self, mock_db):
        """Should reject more than 100 prompts."""
        prompts = [f"Prompt {i}" for i in range(101)]

        with pytest.raises(ValueError, match="2-100 items"):
            batch_generate_images(prompts=prompts)

    def test_validates_empty_prompts(self, mock_db):
        """Should reject empty prompts list."""
        with pytest.raises(ValueError, match="2-100 items"):
            batch_generate_images(prompts=[])

    def test_validates_aspect_ratio(self, mock_db):
        """Should reject invalid aspect ratio."""
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            batch_generate_images(prompts=["A", "B"], aspect_ratio="invalid")

    def test_validates_resolution(self, mock_db):
        """Should reject invalid resolution."""
        with pytest.raises(ValueError, match="Invalid resolution"):
            batch_generate_images(prompts=["A", "B"], resolution="4K")

    def test_validates_model_type(self, mock_db):
        """Should reject invalid model type."""
        with pytest.raises(ValueError, match="Invalid model_type"):
            batch_generate_images(prompts=["A", "B"], model_type="invalid")

    def test_forces_1k_for_fast_model(self, mock_db):
        """Should force 1K resolution when using fast model with 2K."""
        prompts = ["A", "B"]

        result = batch_generate_images(
            prompts=prompts, model_type="fast", resolution="2K"
        )

        # Check that task payload has 1K, not 2K
        call_args = mock_db.create_batch_with_tasks.call_args
        tasks = call_args[1]["tasks"]
        payload = json.loads(tasks[0]["input_payload"])
        assert payload["resolution"] == "1K"

    def test_allows_2k_for_pro_model(self, mock_db):
        """Should allow 2K resolution for pro model."""
        prompts = ["A", "B"]

        result = batch_generate_images(
            prompts=prompts, model_type="pro", resolution="2K"
        )

        call_args = mock_db.create_batch_with_tasks.call_args
        tasks = call_args[1]["tasks"]
        payload = json.loads(tasks[0]["input_payload"])
        assert payload["resolution"] == "2K"

    def test_tasks_have_null_target_path(self, mock_db):
        """Tasks should have target_path=None (worker decides)."""
        prompts = ["A", "B"]

        batch_generate_images(prompts=prompts)

        call_args = mock_db.create_batch_with_tasks.call_args
        tasks = call_args[1]["tasks"]

        for task in tasks:
            assert task["target_path"] is None

    def test_all_valid_aspect_ratios_accepted(self, mock_db):
        """All valid aspect ratios from config should be accepted."""
        for ratio in VALID_ASPECT_RATIOS:
            result = batch_generate_images(prompts=["A", "B"], aspect_ratio=ratio)
            assert result["status"] == "PENDING"


# ============================================================================
# queue_generate_audio Tests
# ============================================================================


class TestQueueGenerateAudio:
    """Tests for queue_generate_audio tool."""

    def test_creates_task_with_valid_text(self, mock_db):
        """Should create TTS task with valid text."""
        result = queue_generate_audio(text="Hello, world!")

        assert "task_id" in result
        assert result["status"] == "PENDING"
        assert result["voice"] == "puck"
        mock_db.create_task.assert_called_once()

    def test_validates_empty_text(self, mock_db):
        """Should reject empty text."""
        with pytest.raises(ValueError, match="cannot be empty"):
            queue_generate_audio(text="")

    def test_validates_whitespace_text(self, mock_db):
        """Should reject whitespace-only text."""
        with pytest.raises(ValueError, match="cannot be empty"):
            queue_generate_audio(text="   ")

    def test_validates_text_length(self, mock_db):
        """Should reject text longer than 5000 characters."""
        long_text = "x" * 5001

        with pytest.raises(ValueError, match="5000 characters"):
            queue_generate_audio(text=long_text)

    def test_accepts_max_length_text(self, mock_db):
        """Should accept text exactly 5000 characters."""
        text = "x" * 5000

        result = queue_generate_audio(text=text)

        assert result["status"] == "PENDING"

    def test_validates_voice(self, mock_db):
        """Should reject invalid voice."""
        with pytest.raises(ValueError, match="Invalid voice"):
            queue_generate_audio(text="Hello", voice="invalid_voice")

    def test_validates_model_type(self, mock_db):
        """Should reject invalid model type."""
        with pytest.raises(ValueError, match="Invalid model_type"):
            queue_generate_audio(text="Hello", model_type="invalid")

    def test_normalizes_voice_to_lowercase(self, mock_db):
        """Voice should be normalized to lowercase."""
        result = queue_generate_audio(text="Hello", voice="PUCK")

        assert result["voice"] == "puck"

    def test_task_has_null_target_path(self, mock_db):
        """Task should have target_path=None (worker decides)."""
        queue_generate_audio(text="Hello")

        call_args = mock_db.create_task.call_args
        assert call_args[1]["target_path"] is None

    def test_uses_correct_model_for_flash(self, mock_db):
        """Should use flash TTS model."""
        result = queue_generate_audio(text="Hello", model_type="flash")

        assert result["model"] == TTS_MODELS["flash"]

    def test_uses_correct_model_for_pro(self, mock_db):
        """Should use pro TTS model."""
        result = queue_generate_audio(text="Hello", model_type="pro")

        assert result["model"] == TTS_MODELS["pro"]

    def test_valid_voices_from_config(self, mock_db):
        """First few voices from config should be valid."""
        sample_voices = VALID_VOICES[:5]

        for voice in sample_voices:
            result = queue_generate_audio(text="Test", voice=voice)
            assert result["status"] == "PENDING"


# ============================================================================
# check_task_status Tests
# ============================================================================


class TestCheckTaskStatus:
    """Tests for check_task_status tool."""

    def test_returns_task_status(self, mock_db, sample_task):
        """Should return task status."""
        mock_db.get_task.return_value = sample_task

        result = check_task_status(sample_task["id"])

        assert result["task_id"] == sample_task["id"]
        assert result["status"] == "COMPLETED"
        assert result["operation_type"] == "TTS_GEN_QUEUE"

    def test_raises_for_unknown_task(self, mock_db):
        """Should raise ValueError for unknown task."""
        mock_db.get_task.return_value = None

        with pytest.raises(ValueError, match="Task not found"):
            check_task_status("unknown-task-id")

    def test_returns_absolute_local_path(self, mock_db, sample_task):
        """local_path should be absolute."""
        mock_db.get_task.return_value = sample_task

        result = check_task_status(sample_task["id"])

        # Path should be absolute (starts with / or drive letter)
        local_path = result.get("local_path", "")
        assert local_path  # Not empty
        # On Windows it starts with drive letter, on Unix with /
        import os

        assert os.path.isabs(local_path)

    def test_includes_error_for_failed_task(self, mock_db, sample_task):
        """Should include error details for failed task."""
        sample_task["status"] = "FAILED"
        sample_task["error_details"] = "API quota exceeded"
        mock_db.get_task.return_value = sample_task

        result = check_task_status(sample_task["id"])

        assert result["status"] == "FAILED"
        assert result["error"] == "API quota exceeded"

    def test_includes_completed_at(self, mock_db, sample_task):
        """Should include completed_at timestamp."""
        mock_db.get_task.return_value = sample_task

        result = check_task_status(sample_task["id"])

        assert "completed_at" in result
        assert result["completed_at"] == sample_task["completed_at"]


# ============================================================================
# check_batch_progress Tests
# ============================================================================


class TestCheckBatchProgress:
    """Tests for check_batch_progress tool."""

    def test_returns_batch_progress(self, mock_db, sample_batch):
        """Should return batch progress."""
        mock_db.get_batch.return_value = sample_batch
        mock_db.get_batch_progress.return_value = {
            "total": 10,
            "completed": 3,
            "failed": 0,
            "pending": 7,
        }

        result = check_batch_progress(sample_batch["id"])

        assert result["batch_id"] == sample_batch["id"]
        assert result["status"] == "PROCESSING"
        assert result["total_tasks"] == 10
        assert result["completed_tasks"] == 3
        assert result["progress_percent"] == 30

    def test_raises_for_unknown_batch(self, mock_db):
        """Should raise ValueError for unknown batch."""
        mock_db.get_batch.return_value = None

        with pytest.raises(ValueError, match="Batch not found"):
            check_batch_progress("unknown-batch-id")

    def test_calculates_progress_correctly(self, mock_db, sample_batch):
        """Progress percent should be calculated correctly."""
        mock_db.get_batch.return_value = sample_batch
        mock_db.get_batch_progress.return_value = {
            "total": 10,
            "completed": 5,
            "failed": 2,
            "pending": 3,
        }

        result = check_batch_progress(sample_batch["id"])

        # (5 + 2) / 10 = 70%
        assert result["progress_percent"] == 70

    def test_handles_zero_total(self, mock_db, sample_batch):
        """Should handle zero total tasks gracefully."""
        mock_db.get_batch.return_value = sample_batch
        mock_db.get_batch_progress.return_value = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "pending": 0,
        }

        result = check_batch_progress(sample_batch["id"])

        assert result["progress_percent"] == 0

    def test_includes_google_batch_id(self, mock_db, sample_batch):
        """Should include google_batch_id when available."""
        mock_db.get_batch.return_value = sample_batch
        mock_db.get_batch_progress.return_value = {
            "total": 10,
            "completed": 0,
            "failed": 0,
            "pending": 10,
        }

        result = check_batch_progress(sample_batch["id"])

        assert result["google_batch_id"] == "batches/abc123"

    def test_status_messages(self, mock_db, sample_batch):
        """Should generate appropriate status messages."""
        mock_db.get_batch_progress.return_value = {
            "total": 10,
            "completed": 0,
            "failed": 0,
            "pending": 10,
        }

        # Test PENDING status
        sample_batch["status"] = "PENDING"
        mock_db.get_batch.return_value = sample_batch
        result = check_batch_progress(sample_batch["id"])
        assert "waiting" in result["message"].lower()

        # Test COMPLETED status
        sample_batch["status"] = "COMPLETED"
        mock_db.get_batch_progress.return_value = {
            "total": 10,
            "completed": 8,
            "failed": 2,
            "pending": 0,
        }
        mock_db.get_batch.return_value = sample_batch
        result = check_batch_progress(sample_batch["id"])
        assert "8 succeeded" in result["message"]


# ============================================================================
# Integration Tests
# ============================================================================


class TestValidVoicesFromConfig:
    """Test that voices are correctly loaded from config."""

    def test_valid_voices_not_empty(self):
        """VALID_VOICES should have entries from config."""
        assert len(VALID_VOICES) > 0

    def test_puck_is_valid_voice(self):
        """Default voice 'puck' should be in valid voices."""
        assert "puck" in VALID_VOICES

    def test_voices_are_lowercase(self):
        """All voice keys should be lowercase."""
        for voice in VALID_VOICES:
            assert voice == voice.lower()


class TestValidAspectRatiosFromConfig:
    """Test that aspect ratios are correctly loaded from config."""

    def test_aspect_ratios_not_empty(self):
        """VALID_ASPECT_RATIOS should have entries."""
        assert len(VALID_ASPECT_RATIOS) > 0

    def test_common_ratios_present(self):
        """Common aspect ratios should be present."""
        assert "1:1" in VALID_ASPECT_RATIOS
        assert "16:9" in VALID_ASPECT_RATIOS
        assert "9:16" in VALID_ASPECT_RATIOS
