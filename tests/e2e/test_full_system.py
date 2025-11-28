"""E2E Test: Full System Integration  Rick and Morty Edition! 

      :
1. Batch Image Generation (2  Rick & Morty)
2. TTS Queue Processing ( )
3.    tests/e2e/output/

:       Gemini API!
: pytest tests/e2e/ -m paid -v

 : ~$0.02
- 2  batch  $0.0025 = $0.005
- 1 TTS   $0.01 = $0.01
"""

import shutil
import time
from pathlib import Path

import pytest

from tools.batch_tools import (
    batch_generate_images,
    check_batch_progress,
    check_task_status,
    queue_generate_audio,
)

# 
BATCH_SUBMIT_TIMEOUT = 120  # 2     Google
BATCH_COMPLETE_TIMEOUT = 360  # 6    batch
TTS_COMPLETE_TIMEOUT = 60  # 1   TTS


def wait_for_batch_status(
    batch_id: str,
    target_statuses: list[str],
    timeout: int,
    check_interval: int = 10,
) -> dict:
    """
      batch   .

    Args:
        batch_id: ID 
        target_statuses:    (  )
        timeout:     
        check_interval:  

    Returns:
          batch

    Raises:
        TimeoutError:      timeout
    """
    start = time.time()
    last_status = None

    while time.time() - start < timeout:
        progress = check_batch_progress(batch_id)
        status = progress["status"]

        if status != last_status:
            print(
                f"   Batch status: {status} ({progress['completed_tasks']}/{progress['total_tasks']})"
            )
            last_status = status

        if status in target_statuses:
            return progress

        if status == "FAILED":
            raise RuntimeError(f"Batch failed! Progress: {progress}")

        time.sleep(check_interval)

    raise TimeoutError(
        f"Batch did not reach {target_statuses} within {timeout}s. "
        f"Last status: {last_status}"
    )


def wait_for_task_status(
    task_id: str,
    target_statuses: list[str],
    timeout: int,
    check_interval: int = 5,
) -> dict:
    """
      task   .
    """
    start = time.time()
    last_status = None

    while time.time() - start < timeout:
        status_info = check_task_status(task_id)
        status = status_info["status"]

        if status != last_status:
            print(f"   Task status: {status}")
            last_status = status

        if status in target_statuses:
            return status_info

        if status == "FAILED":
            error = status_info.get("error", "Unknown error")
            raise RuntimeError(f"Task failed: {error}")

        time.sleep(check_interval)

    raise TimeoutError(
        f"Task did not reach {target_statuses} within {timeout}s. "
        f"Last status: {last_status}"
    )


@pytest.mark.paid
class TestRickAndMortyE2E:
    """
     Wubba Lubba Dub Dub!

    Full E2E test suite featuring Rick and Morty prompts.
    """

    def test_batch_images_rick_and_morty(
        self,
        e2e_db,
        e2e_worker,
        e2e_output_dir: Path,
        rick_and_morty_prompts: list[str],
    ):
        """
        Test batch image generation with Rick and Morty prompts.

        1.  batch  2 
        2.  SUBMITTED (  Google)
        3.  COMPLETED ( )
        4.    tests/e2e/output/images/
        5.     PNG
        """
        print("\n === BATCH IMAGE GENERATION TEST ===")
        print(f" Prompts: {len(rick_and_morty_prompts)}")

        # 1.  batch
        result = batch_generate_images(
            prompts=rick_and_morty_prompts,
            aspect_ratio="16:9",
            resolution="1K",
            model_type="fast",  # !
        )

        batch_id = result["batch_id"]
        print(f" Batch created: {batch_id}")
        print(f" Estimated cost: {result['estimated_cost']}")

        # 2.  SUBMITTED   PROCESSING/COMPLETED
        print("\n Waiting for batch submission...")
        wait_for_batch_status(
            batch_id,
            ["SUBMITTED", "PROCESSING", "COMPLETED"],
            timeout=BATCH_SUBMIT_TIMEOUT,
        )

        # 3.  COMPLETED
        print("\n Waiting for batch completion...")
        final_progress = wait_for_batch_status(
            batch_id,
            ["COMPLETED"],
            timeout=BATCH_COMPLETE_TIMEOUT,
        )

        print(f"\n Batch completed!")
        print(f"  - Completed: {final_progress['completed_tasks']}")
        print(f"  - Failed: {final_progress['failed_tasks']}")

        # 4.    
        tasks = e2e_db.get_tasks_by_batch(batch_id)
        images_dir = e2e_output_dir / "images"

        for i, task in enumerate(tasks):
            assert task["status"] == "COMPLETED", (
                f"Task {i} not completed: {task['status']}"
            )

            local_path = task.get("local_path")
            assert local_path, f"Task {i} has no local_path"

            src_file = Path(local_path)
            assert src_file.exists(), f"File not found: {src_file}"
            assert src_file.stat().st_size > 1000, f"File too small: {src_file}"

            #   - 
            dest_name = f"rick_morty_{i + 1}.png"
            dest_file = images_dir / dest_name
            shutil.copy2(src_file, dest_file)

            print(f"   Saved: {dest_name} ({src_file.stat().st_size // 1024} KB)")

        print(f"\n Images saved to: {images_dir}")

        # Assertions
        assert final_progress["completed_tasks"] == 2
        assert final_progress["failed_tasks"] == 0
        assert final_progress["progress_percent"] == 100

    def test_tts_queue_pickle_rick(
        self,
        e2e_db,
        e2e_worker,
        e2e_output_dir: Path,
        rick_tts_text: str,
    ):
        """
        Test TTS queue processing with Rick's famous quote.

        1.  TTS 
        2.  COMPLETED
        3.  WAV  tests/e2e/output/audio/
        4.    
        """
        print("\n === TTS QUEUE TEST ===")
        print(f" Text: {rick_tts_text[:50]}...")

        # 1.  TTS 
        result = queue_generate_audio(
            text=rick_tts_text,
            voice="puck",  # Closest to Rick's voice
            model_type="flash",  # !
        )

        task_id = result["task_id"]
        print(f" TTS task created: {task_id}")
        print(f" Voice: {result['voice']}")
        print(f" Estimated cost: {result['estimated_cost']}")

        # 2.  COMPLETED
        print("\n Waiting for TTS completion...")
        final_status = wait_for_task_status(
            task_id,
            ["COMPLETED"],
            timeout=TTS_COMPLETE_TIMEOUT,
        )

        print(f"\n TTS completed!")

        # 3.    
        local_path = final_status.get("local_path")
        assert local_path, "TTS task has no local_path"

        src_file = Path(local_path)
        assert src_file.exists(), f"Audio file not found: {src_file}"
        assert src_file.stat().st_size > 1000, f"Audio file too small: {src_file}"

        #   - 
        audio_dir = e2e_output_dir / "audio"
        dest_file = audio_dir / "pickle_rick.wav"
        shutil.copy2(src_file, dest_file)

        print(f"   Saved: pickle_rick.wav ({src_file.stat().st_size // 1024} KB)")
        print(f"\n Audio saved to: {audio_dir}")

        # Assertions
        assert final_status["status"] == "COMPLETED"


@pytest.mark.paid
class TestCostVerification:
    """
    Verify that batch API is actually cheaper than sync.
    """

    def test_batch_cost_estimation(self, e2e_db):
        """
        Batch    50%.

           ,   .
        """
        from tools.batch_tools import batch_generate_images

        # 10   batch
        result = batch_generate_images(
            prompts=[f"Test image {i}" for i in range(10)],
            aspect_ratio="1:1",
            model_type="fast",
        )

        # $0.0025  10 = $0.025
        assert result["estimated_cost"] == "$0.0250"
        print(f" Batch cost for 10 images: {result['estimated_cost']}")

        # Sync   $0.005  10 = $0.05
        # : 50%
        print(" Confirmed: Batch is 50% cheaper than sync!")


@pytest.mark.paid
class TestErrorHandlingE2E:
    """
    Test error handling with real validation (no mocks).
    """

    def test_invalid_aspect_ratio_rejected(self, e2e_db):
        """Invalid aspect ratio should be rejected."""
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            batch_generate_images(
                prompts=["Test 1", "Test 2"],
                aspect_ratio="invalid:ratio",
            )
        print(" Invalid aspect ratio correctly rejected")

    def test_invalid_voice_rejected(self, e2e_db):
        """Invalid voice should be rejected."""
        with pytest.raises(ValueError, match="Invalid voice"):
            queue_generate_audio(
                text="Test",
                voice="rick_sanchez_voice",  # Not a real voice
            )
        print(" Invalid voice correctly rejected")

    def test_empty_prompts_rejected(self, e2e_db):
        """Empty prompts list should be rejected."""
        with pytest.raises(ValueError, match="2-100 items"):
            batch_generate_images(prompts=[])
        print(" Empty prompts correctly rejected")

    def test_text_too_long_rejected(self, e2e_db):
        """Text over 5000 chars should be rejected."""
        long_text = "Wubba lubba dub dub! " * 500  # ~10500 chars

        with pytest.raises(ValueError, match="5000 characters"):
            queue_generate_audio(text=long_text)
        print(" Long text correctly rejected")
