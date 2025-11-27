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
    # rpm_limit = 10 для Pay-as-you-go tier (Tier 1+)
    (
        "IMG_GEN",
        "Image Generation",
        "sync",
        "Текущая генерация изображений (полная цена)",
        10,  # 10 RPM на Tier 1
    ),
    (
        "TTS_GEN",
        "Audio Generation (TTS)",
        "sync",
        "Текущая генерация аудио (полная цена)",
        10,  # 10 RPM на Tier 1
    ),
    ("IMG_ANALYZE", "Image Analysis", "sync", "Текущий анализ изображений", 10),
    ("AUDIO_ANALYZE", "Audio Analysis", "sync", "Текущий анализ аудио", 10),
    ("VIDEO_ANALYZE", "Video Analysis", "sync", "Текущий анализ видео", 10),
    ("GIF_ANALYZE", "GIF Analysis", "sync", "Текущий анализ GIF", 10),
    # Batch операции (50% скидка через Google Batch API)
    # rpm_limit = NULL — Batch API сам управляет очередью, rate limiting не нужен
    (
        "IMG_GEN_BATCH",
        "Image Generation (Batch)",
        "batch",
        "Генерация изображений через Batch API (50% скидка)",
        None,  # Batch API не требует rate limiting
    ),
    (
        "IMG_ANALYZE_BATCH",
        "Image Analysis (Batch)",
        "batch",
        "Анализ изображений через Batch API",
        None,
    ),
    (
        "VIDEO_ANALYZE_BATCH",
        "Video Analysis (Batch)",
        "batch",
        "Анализ видео через Batch API",
        None,
    ),
    (
        "GIF_ANALYZE_BATCH",
        "GIF Analysis (Batch)",
        "batch",
        "Анализ GIF через Batch API",
        None,
    ),
]

# SQL для вставки (используется в manager.py)
INSERT_OPERATION_TYPES = """
INSERT OR IGNORE INTO operation_types (operation_type, display_name, execution_mode, description, rpm_limit)
VALUES (?, ?, ?, ?, ?)
"""
