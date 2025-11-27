"""
Seed данные для справочников БД.

operation_types — валидные типы операций на основе:
- Фазы 0 валидации Batch API (27.11.2025)
- Реальных инструментов в tools/
"""

# ============================================================================
# Operation Types
# ============================================================================

OPERATION_TYPES_SEED = [
    # Синхронные операции (текущее поведение)
    (
        "IMG_GEN",
        "Image Generation",
        "sync",
        "Текущая генерация изображений (полная цена)",
    ),
    (
        "TTS_GEN",
        "Audio Generation (TTS)",
        "sync",
        "Текущая генерация аудио (полная цена)",
    ),
    ("IMG_ANALYZE", "Image Analysis", "sync", "Текущий анализ изображений"),
    ("AUDIO_ANALYZE", "Audio Analysis", "sync", "Текущий анализ аудио"),
    ("VIDEO_ANALYZE", "Video Analysis", "sync", "Текущий анализ видео"),
    ("GIF_ANALYZE", "GIF Analysis", "sync", "Текущий анализ GIF"),
    # Batch операции (50% скидка через Google Batch API)
    (
        "IMG_GEN_BATCH",
        "Image Generation (Batch)",
        "batch",
        "Генерация изображений через Batch API (50% скидка)",
    ),
    (
        "IMG_ANALYZE_BATCH",
        "Image Analysis (Batch)",
        "batch",
        "Анализ изображений через Batch API",
    ),
    (
        "VIDEO_ANALYZE_BATCH",
        "Video Analysis (Batch)",
        "batch",
        "Анализ видео через Batch API",
    ),
    (
        "GIF_ANALYZE_BATCH",
        "GIF Analysis (Batch)",
        "batch",
        "Анализ GIF через Batch API",
    ),
]

# SQL для вставки (используется в manager.py)
INSERT_OPERATION_TYPES_QUERY = """
INSERT OR IGNORE INTO operation_types (operation_type, display_name, execution_mode, description)
VALUES (?, ?, ?, ?)
"""
