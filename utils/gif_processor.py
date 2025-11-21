"""GIF animation processing utilities for Gemini API."""

from typing import Optional, Literal
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_gif_frames(
    image: Image.Image,
    mode: Literal["fps", "total", "interval"] = "total",
    gif_fps: Optional[float] = None,
    frame_count: Optional[int] = None,
    interval_sec: Optional[float] = None,
) -> list[Image.Image]:
    """Extract frames from animated GIF using different strategies.

    Args:
        image: PIL Image object (animated GIF)
        mode: Extraction mode ('fps', 'total', 'interval')
        gif_fps: Frames per second to extract (for 'fps' mode)
        frame_count: Total number of frames to extract (for 'total' mode)
        interval_sec: Time interval in seconds (for 'interval' mode)

    Returns:
        List of extracted frames as PIL Images

    Raises:
        ValueError: If required parameters for mode are missing

    Examples:
        # Mode 1: Extract at 1 FPS
        frames = extract_gif_frames(gif, mode='fps', gif_fps=1.0)

        # Mode 2: Extract exactly 5 frames (evenly distributed)
        frames = extract_gif_frames(gif, mode='total', frame_count=5)

        # Mode 3: Extract frame every 5 seconds
        frames = extract_gif_frames(gif, mode='interval', interval_sec=5.0)
    """
    if not getattr(image, "is_animated", False):
        logger.info("Image is not animated, returning single frame")
        return [_convert_frame(image)]

    # Get GIF metadata
    gif_duration_ms = image.info.get("duration", 100)  # milliseconds per frame
    total_frames = getattr(image, "n_frames", 1)
    total_duration_sec = (gif_duration_ms * total_frames) / 1000.0
    native_fps = 1000.0 / gif_duration_ms

    logger.info(
        f"GIF info: {total_frames} frames, {total_duration_sec:.1f}s, {native_fps:.1f} fps"
    )

    # Determine frame indices based on mode
    if mode == "fps":
        if gif_fps is None:
            raise ValueError("Parameter 'gif_fps' required for mode 'fps'")
        frame_indices = _get_fps_indices(total_frames, native_fps, gif_fps)

    elif mode == "total":
        if frame_count is None:
            raise ValueError("Parameter 'frame_count' required for mode 'total'")
        frame_indices = _get_total_indices(total_frames, frame_count)

    elif mode == "interval":
        if interval_sec is None:
            raise ValueError("Parameter 'interval_sec' required for mode 'interval'")
        frame_indices = _get_interval_indices(
            total_frames, total_duration_sec, interval_sec
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

    logger.info(f"Extracting {len(frame_indices)} frames using mode '{mode}'")

    # Extract frames at calculated indices
    frames = []
    for idx in frame_indices:
        image.seek(idx)
        frame = image.copy()
        frames.append(_convert_frame(frame))

    return frames


def _get_fps_indices(
    total_frames: int, native_fps: float, target_fps: float
) -> list[int]:
    """Calculate frame indices for FPS mode.

    Args:
        total_frames: Total number of frames in GIF
        native_fps: GIF's native frame rate
        target_fps: Desired extraction rate

    Returns:
        List of frame indices to extract
    """
    frame_step = max(1, int(native_fps / target_fps))
    return list(range(0, total_frames, frame_step))


def _get_total_indices(total_frames: int, frame_count: int) -> list[int]:
    """Calculate evenly distributed frame indices for TOTAL mode.

    Args:
        total_frames: Total number of frames in GIF
        frame_count: Desired number of frames to extract

    Returns:
        List of evenly distributed frame indices

    Examples:
        # 30 frames, want 5
        _get_total_indices(30, 5)  # [0, 6, 12, 18, 24]

        # 180 frames (3 min at 1fps), want 5
        _get_total_indices(180, 5)  # [0, 36, 72, 108, 144]
    """
    if frame_count >= total_frames:
        return list(range(total_frames))

    # Evenly distribute frames
    step = total_frames / frame_count
    indices = [int(i * step) for i in range(frame_count)]

    return indices


def _get_interval_indices(
    total_frames: int, total_duration_sec: float, interval_sec: float
) -> list[int]:
    """Calculate frame indices for INTERVAL mode.

    Args:
        total_frames: Total number of frames in GIF
        total_duration_sec: Total duration in seconds
        interval_sec: Time interval in seconds

    Returns:
        List of frame indices at specified intervals
    """
    if total_duration_sec <= 0:
        return [0]

    frames_per_sec = total_frames / total_duration_sec
    frame_step = max(1, int(interval_sec * frames_per_sec))

    return list(range(0, total_frames, frame_step))


def _convert_frame(frame: Image.Image) -> Image.Image:
    """Convert frame to compatible mode for Gemini API.

    Args:
        frame: PIL Image frame

    Returns:
        Converted frame in compatible mode
    """
    # Convert palette mode (P) and other incompatible modes to RGB
    if frame.mode in ("P", "LA", "PA"):
        return frame.convert("RGB")
    elif frame.mode == "RGBA":
        return frame  # Keep RGBA - it's supported
    elif frame.mode not in ("RGB", "L"):
        return frame.convert("RGB")
    return frame


def resize_image(image: Image.Image, max_dimension: Optional[int]) -> Image.Image:
    """Resize image maintaining aspect ratio.

    Args:
        image: PIL Image object
        max_dimension: Maximum size for longest side (None = no resize)

    Returns:
        Resized image
    """
    if max_dimension is None:
        return image

    width, height = image.size
    max_current = max(width, height)

    if max_current <= max_dimension:
        return image

    scale = max_dimension / max_current
    new_width = int(width * scale)
    new_height = int(height * scale)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def create_animation_prompt(
    user_prompt: str, frame_count: int, extraction_info: str, system_prompt: str
) -> str:
    """Create context-aware prompt for GIF animation analysis.

    Args:
        user_prompt: User's original prompt
        frame_count: Number of extracted frames
        extraction_info: Description of extraction method
        system_prompt: System prompt explaining animation analysis approach

    Returns:
        Enhanced prompt with animation context
    """
    context_prompt = f"""{system_prompt}

**Animation Details:**
- Total frames analyzed: {frame_count}
- Extraction method: {extraction_info}

**User's Specific Request:**
{user_prompt}

Please provide your analysis based on the frames and the user's request above."""

    return context_prompt
