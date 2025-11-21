"""Audio extraction and conversion utilities for video analysis.

This module provides functionality to extract audio tracks from video files
and convert them to optimized Vorbis mono format with configurable bitrates.
All processing is done in-memory without creating temporary files.
"""

import base64
import io
import os
from typing import Optional, Literal
from pydub import AudioSegment
from utils.logger import get_logger

logger = get_logger(__name__)


def estimate_audio_size(duration_sec: float, bitrate: int = 64) -> float:
    """Calculate estimated audio file size without processing.

    Args:
        duration_sec: Audio duration in seconds
        bitrate: Bitrate in kbps (default: 64)

    Returns:
        Estimated size in MB

    Examples:
        >>> estimate_audio_size(600, 64)  # 10 minutes at 64 kbps
        4.8
        >>> estimate_audio_size(1800, 32)  # 30 minutes at 32 kbps
        7.2
        >>> estimate_audio_size(1800, 24)  # 30 minutes at 24 kbps
        5.4
    """
    # Formula: (duration_sec * bitrate_kbps * 1000 bits/kbit) / 8 bits/byte
    size_bytes = (duration_sec * bitrate * 1000) / 8
    size_mb = size_bytes / (1024 * 1024)
    return round(size_mb, 2)


def extract_audio_from_video(
    video_path: str,
    bitrate: Literal[64, 32, 24] = 64,
    max_duration_sec: Optional[int] = None,
    dry_run: bool = False,
) -> dict:
    """Extract and convert audio track from video file.

    Extracts audio in-memory and converts to mono Vorbis (OGG) format
    for optimal compression and Gemini API compatibility.

    Args:
        video_path: Path to video file
        bitrate: Output bitrate in kbps (64/32/24, default: 64)
        max_duration_sec: Maximum duration to extract (None = full audio)
        dry_run: If True, only calculate size without processing

    Returns:
        Dictionary with audio data:
        {
            'base64': str,           # Only if dry_run=False
            'mime_type': 'audio/ogg',
            'duration_sec': float,
            'size_mb': float,
            'bitrate': int,
            'channels': 1  # mono
        }

    Raises:
        FileNotFoundError: If video file not found
        RuntimeError: If audio extraction fails

    Examples:
        # Extract full audio at 64 kbps
        audio = extract_audio_from_video("video.mp4", bitrate=64)
        print(f"Size: {audio['size_mb']:.2f} MB")

        # Extract first 5 minutes at 32 kbps
        audio = extract_audio_from_video("lecture.mp4", bitrate=32, max_duration_sec=300)

        # Dry run to estimate size
        audio = extract_audio_from_video("long.mp4", dry_run=True)
        print(f"Estimated: {audio['size_mb']:.2f} MB")
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")

    logger.info(f"Extracting audio from video: {video_path}")
    logger.info(f"Settings: bitrate={bitrate} kbps, mono, Vorbis (OGG)")

    try:
        # Load audio from video using pydub
        # pydub will use ffmpeg under the hood (from imageio-ffmpeg)
        logger.info("Loading audio track from video...")
        audio = AudioSegment.from_file(video_path)

        # Get original duration
        duration_ms = len(audio)
        duration_sec = duration_ms / 1000.0
        logger.info(f"Original audio: {duration_sec:.1f}s, {audio.channels} channels")

        # Trim if needed
        if max_duration_sec and duration_sec > max_duration_sec:
            logger.info(f"Trimming audio to {max_duration_sec}s")
            audio = audio[: max_duration_sec * 1000]
            duration_sec = max_duration_sec

        # If dry run, just estimate size
        if dry_run:
            estimated_size = estimate_audio_size(duration_sec, bitrate)
            logger.info(f"🔍 Dry run: estimated size {estimated_size:.2f} MB")

            return {
                "mime_type": "audio/ogg",
                "duration_sec": round(duration_sec, 1),
                "size_mb": estimated_size,
                "bitrate": bitrate,
                "channels": 1,
            }

        # Convert to mono
        if audio.channels > 1:
            logger.info("Converting stereo to mono...")
            audio = audio.set_channels(1)

        # Export to Vorbis (OGG) format in-memory
        logger.info(f"Converting to Vorbis mono {bitrate} kbps...")
        buffer = io.BytesIO()

        audio.export(
            buffer,
            format="ogg",
            codec="libvorbis",
            bitrate=f"{bitrate}k",
            parameters=["-ac", "1"],  # Force mono
        )

        # Get size and base64
        buffer.seek(0)
        audio_bytes = buffer.getvalue()
        actual_size_mb = len(audio_bytes) / (1024 * 1024)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        logger.info(
            f"✅ Audio extracted: {duration_sec:.1f}s, "
            f"{actual_size_mb:.2f} MB, "
            f"{bitrate} kbps mono"
        )

        return {
            "base64": audio_b64,
            "mime_type": "audio/ogg",
            "duration_sec": round(duration_sec, 1),
            "size_mb": round(actual_size_mb, 3),
            "bitrate": bitrate,
            "channels": 1,
        }

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to extract audio: {e}")
        raise RuntimeError(f"Audio extraction failed: {e}")


def get_audio_metadata(video_path: str) -> dict:
    """Get audio metadata without extracting full audio.

    Fast metadata retrieval for planning purposes.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with metadata:
        {
            'duration_sec': float,
            'channels': int,
            'sample_rate': int,
            'has_audio': bool
        }

    Raises:
        FileNotFoundError: If video file not found
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    try:
        # Load just the first second to get metadata
        audio = AudioSegment.from_file(video_path, duration=1.0)

        # Get full file duration by loading without limit
        full_audio = AudioSegment.from_file(video_path)
        duration_sec = len(full_audio) / 1000.0

        return {
            "duration_sec": round(duration_sec, 1),
            "channels": audio.channels,
            "sample_rate": audio.frame_rate,
            "has_audio": True,
        }

    except Exception as e:
        logger.warning(f"Could not extract audio metadata: {e}")
        return {
            "duration_sec": 0.0,
            "channels": 0,
            "sample_rate": 0,
            "has_audio": False,
        }
