"""File handling utilities for image validation and MIME type detection.

This module provides utilities for working with image files, including
MIME type detection, file validation, and binary file reading operations.
"""

import mimetypes
import os
from pathlib import Path
from typing import List

SUPPORTED_IMAGE_MIME_TYPES: List[str] = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
]


def get_file_mime_type(file_path: str) -> str | None:
    """Detect MIME type of a file.

    Attempts to determine MIME type using mimetypes library,
    with fallback to extension-based detection.

    Args:
        file_path: Path to the file to analyze.

    Returns:
        MIME type string, or 'application/octet-stream' for unknown types.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type

    file_extension = Path(file_path).suffix.lower()
    extension_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".heic": "image/heic",
        ".heif": "image/heif",
    }

    return extension_map.get(file_extension, "application/octet-stream")


def read_file_as_bytes(file_path: str) -> bytes:
    """Read file contents as bytes.

    Args:
        file_path: Path to the file to read.

    Returns:
        File contents as bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If an error occurs during file reading.
    """
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"File not found: {file_path}") from exc
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}") from e


def is_image_valid(file_path: str) -> bool:
    """Validate if a file is a supported image type.

    Args:
        file_path: Path to the file to validate.

    Returns:
        True if the file exists and is a supported image type, False otherwise.
    """
    if not os.path.exists(file_path):
        return False
    if not os.path.isfile(file_path):
        return False
    mime_type = get_file_mime_type(file_path)
    return mime_type in SUPPORTED_IMAGE_MIME_TYPES
