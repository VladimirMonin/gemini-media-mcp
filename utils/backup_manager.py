"""Backup manager for generated content with metadata.

Automatically creates backup copies of generated images and audio files
with timestamped filenames and JSON metadata sidecars.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Literal, Optional, Tuple
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


def sanitize_description(text: str, max_length: int = 20) -> str:
    """
    Extract and sanitize first words from prompt for filename.

    Args:
        text: Source text (usually prompt)
        max_length: Maximum characters to keep

    Returns:
        Sanitized string safe for filenames
    """
    # Take first words
    words = text.split()[:5]  # First 5 words max
    description = "_".join(words)

    # Remove unsafe characters
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    description = "".join(c if c in safe_chars else "_" for c in description)

    # Truncate and clean up
    description = description[:max_length].strip("_-")

    return description or "generated"


def create_backup_filename(
    file_type: Literal["image", "audio"],
    extension: str,
    description: Optional[str] = None,
) -> str:
    """
    Generate unique timestamped filename.

    Format: YYYY-MM-DD_HH-MM-SS_description.ext

    Args:
        file_type: Type of file ('image' or 'audio')
        extension: File extension without dot (e.g., 'png', 'wav')
        description: Optional description (will be sanitized)

    Returns:
        Filename string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if description:
        safe_desc = sanitize_description(description)
        filename = f"{timestamp}_{safe_desc}.{extension}"
    else:
        filename = f"{timestamp}_generated.{extension}"

    logger.debug(f"Generated backup filename: {filename}")
    return filename


def save_metadata_json(metadata_path: str, metadata: dict) -> None:
    """
    Save metadata as JSON sidecar file.

    Args:
        metadata_path: Full path to metadata JSON file
        metadata: Dictionary with metadata
    """
    try:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.debug(f"Metadata saved: {metadata_path}")
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")
        raise


def backup_generation(
    original_path: str, file_type: Literal["image", "audio"], metadata: dict
) -> Tuple[str, str]:
    """
    Create backup copy of generated file with metadata sidecar.

    Args:
        original_path: Path to the original generated file
        file_type: Type of file ('image' or 'audio')
        metadata: Metadata dictionary to save

    Returns:
        Tuple of (backup_file_path, metadata_file_path)

    Raises:
        FileNotFoundError: If original file doesn't exist
        IOError: If backup operation fails
    """
    logger.info("=" * 60)
    logger.info(f"💾 BACKUP PROCESS STARTED for {file_type}")

    # Validate original file exists
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"Original file not found: {original_path}")

    # Get backup directory from config
    from config import OUTPUT_IMAGES_DIR, OUTPUT_AUDIO_DIR_NEW

    backup_dir = OUTPUT_IMAGES_DIR if file_type == "image" else OUTPUT_AUDIO_DIR_NEW
    logger.info(f"📁 Backup directory: {backup_dir}")

    # Ensure backup directory exists
    os.makedirs(backup_dir, exist_ok=True)

    # Get file extension
    extension = Path(original_path).suffix.lstrip(".")

    # Extract description from metadata (from prompt if available)
    description = None
    if "parameters" in metadata and "prompt" in metadata["parameters"]:
        description = metadata["parameters"]["prompt"]

    # Generate backup filename
    backup_filename = create_backup_filename(file_type, extension, description)
    backup_path = os.path.join(backup_dir, backup_filename)

    # Generate metadata filename (same name, .json extension)
    metadata_filename = f"{Path(backup_filename).stem}.json"
    metadata_path = os.path.join(backup_dir, metadata_filename)

    logger.info(f"🔖 Backup file: {backup_filename}")
    logger.info(f"📄 Metadata file: {metadata_filename}")

    try:
        # Copy file
        shutil.copy2(original_path, backup_path)
        logger.info(f"✅ File copied: {original_path} -> {backup_path}")

        # Save metadata
        save_metadata_json(metadata_path, metadata)
        logger.info(f"✅ Metadata saved: {metadata_path}")

        # Log metadata summary
        logger.debug(f"📊 Metadata keys: {list(metadata.keys())}")
        if "parameters" in metadata:
            logger.debug(f"📊 Parameters: {list(metadata['parameters'].keys())}")

        logger.info("💾 BACKUP COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        return backup_path, metadata_path

    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        logger.info("=" * 60)
        raise IOError(f"Backup operation failed: {e}")
