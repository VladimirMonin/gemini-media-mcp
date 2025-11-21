# Анализ Видео (Video Analysis)

Анализ видео через извлечение кадров и аудиодорожки с отправкой в Gemini API в одном мультимодальном запросе.

## Возможности

- **3 режима извлечения кадров**: `total` (N кадров равномерно), `fps` (X кадров в секунду), `interval` (кадр каждые X секунд)
- **Гибкие настройки качества**: разрешение (1080p/720p/480p), формат (WEBP/JPEG), битрейт аудио (64/32/24 kbps)
- **Dry-run режим**: оценка размера запроса БЕЗ обработки видео
- **Проверка лимита**: автоматическая проверка < 20 MB перед отправкой
- **In-memory обработка**: без временных файлов
- **Структурированный ответ**: JSON с визуальным анализом, транскрипцией аудио и объединенным нарративом

## Быстрый старт

### Базовый пример

```python
# Анализ видео с 30 кадрами (равномерно распределенными)
result = analyze_video(
    video_path="/path/to/lecture.mp4",
    prompt="Summarize this lecture video",
    frame_count=30
)
```

### Режимы извлечения кадров

#### 1. Режим `total` - N кадров равномерно

```python
# Извлечь ровно 20 кадров, распределенных по всему видео
result = analyze_video(
    video_path="video.mp4",
    frame_mode="total",
    frame_count=20  # кадры будут равномерно распределены
)
```

#### 2. Режим `fps` - X кадров в секунду

```python
# Извлечь 1 кадр каждые 2 секунды (0.5 FPS)
result = analyze_video(
    video_path="video.mp4",
    frame_mode="fps",
    fps=0.5  # 0.5 = 1 кадр каждые 2 секунды
)

# Извлечь 2 кадра в секунду
result = analyze_video(
    video_path="dynamic.mp4",
    frame_mode="fps",
    fps=2.0
)
```

#### 3. Режим `interval` - кадр каждые X секунд

```python
# Извлечь кадр каждые 10 секунд
result = analyze_video(
    video_path="long_video.mp4",
    frame_mode="interval",
    interval_sec=10
)
```

## Оптимизация качества и размера

### Настройка качества кадров

```python
# Высокое качество (1080p WEBP)
result = analyze_video(
    video_path="lecture.mp4",
    max_dimension=1920,  # 1080p
    image_format="webp",
    image_quality=80
)

# Экономия размера (720p WEBP, lower quality)
result = analyze_video(
    video_path="long_video.mp4",
    max_dimension=1280,  # 720p
    image_format="webp",
    image_quality=70
)

# Минимальный размер (480p JPEG)
result = analyze_video(
    video_path="overview.mp4",
    max_dimension=720,  # SD quality
    image_format="jpeg",
    image_quality=60
)
```

### Настройка аудио битрейта

```python
# Высокое качество аудио (64 kbps) - для речи + музыка
result = analyze_video(
    video_path="podcast.mp4",
    audio_bitrate=64
)

# Среднее качество (32 kbps) - хорошо для речи (рекомендуется)
result = analyze_video(
    video_path="lecture.mp4",
    audio_bitrate=32
)

# Низкое качество (24 kbps) - приемлемо для речи
result = analyze_video(
    video_path="interview.mp4",
    audio_bitrate=24
)
```

## Dry-run: оценка размера

Используйте `dry_run=True` для быстрой оценки размера запроса БЕЗ обработки видео:

```python
# Оценить размер без обработки
estimate = analyze_video(
    video_path="large_video.mp4",
    frame_count=50,
    audio_bitrate=32,
    dry_run=True
)

# Результат:
{
  "estimated_size_mb": 15.2,
  "fits_in_limit": true,
  "usage_percent": 76.0,
  "frames": {
    "count": 50,
    "mode": "total",
    "resolution": "~1920p",
    "format": "webp",
    "size_mb": 5.0
  },
  "audio": {
    "duration_sec": 600.0,
    "bitrate_kbps": 32,
    "size_mb": 10.2
  },
  "recommendation": "Good fit (76% of limit)"
}
```

## Типовые сценарии

### Сценарий 1: Короткое динамичное видео (10 минут)

```python
result = analyze_video(
    video_path="action_video.mp4",
    frame_mode="fps",
    fps=0.5,  # 30 кадров (1 каждые 2 сек)
    max_dimension=1280,  # 720p
    audio_bitrate=64
)
# Размер: ~6.3 MB (31% лимита)
```

### Сценарий 2: Лекция/презентация (30 минут)

```python
result = analyze_video(
    video_path="lecture.mp4",
    frame_mode="total",
    frame_count=30,  # 30 кадров равномерно
    max_dimension=1920,  # 1080p для читаемости текста
    audio_bitrate=32  # экономия на аудио
)
# Размер: ~10.2 MB (51% лимита)
```

### Сценарий 3: Длинная лекция (60 минут)

```python
result = analyze_video(
    video_path="long_lecture.mp4",
    frame_mode="interval",
    interval_sec=60,  # кадр каждую минуту
    max_dimension=1280,  # 720p
    audio_bitrate=24  # низкий битрейт
)
# Размер: ~16 MB (80% лимита)
```

### Сценарий 4: Только визуальный анализ

```python
# Без аудио (если не нужна транскрипция)
result = analyze_video(
    video_path="silent_demo.mp4",
    frame_count=40,
    include_audio=False
)
# Размер: только кадры (~4 MB)
```

## Структура ответа

```json
{
  "visual_summary": "Подробное описание визуального содержимого всех кадров",
  "audio_transcription": "Полная транскрипция речи из аудио",
  "audio_description": "Описание музыки, звуковых эффектов, фонового шума",
  "combined_narrative": "Объединенная история, комбинирующая визуал и аудио",
  "key_moments": [
    "Важный момент 1 на временной метке X",
    "Ключевое событие 2",
    "Поворотная точка 3"
  ]
}
```

## Рекомендации по размеру

### Лимит Gemini API: 20 MB

**Таблица размеров кадров (WEBP quality 80):**

| Разрешение | Размер/кадр | 10 кадров | 30 кадров | 60 кадров |
|------------|-------------|-----------|-----------|----------|
| 1080p | ~100 KB | 1 MB | 3 MB | 6 MB |
| 720p | ~50 KB | 0.5 MB | 1.5 MB | 3 MB |
| 480p | ~25 KB | 0.25 MB | 0.75 MB | 1.5 MB |

**Таблица размеров аудио (Vorbis mono):**

| Битрейт | Размер/минута | 10 минут | 30 минут | 60 минут |
|---------|---------------|----------|----------|----------|
| 64 kbps | 0.48 MB | 4.8 MB | 14.4 MB | 28.8 MB ❌ |
| 32 kbps | 0.24 MB | 2.4 MB | 7.2 MB | 14.4 MB |
| 24 kbps | 0.18 MB | 1.8 MB | 5.4 MB | 10.8 MB |

### Стратегии оптимизации

1. **Для длинных видео (>30 мин):**
   - Используйте `audio_bitrate=24` или `32`
   - Уменьшите `frame_count` или используйте `interval_sec`
   - Снизьте `max_dimension` до 1280 или 720

2. **Для видео с мелким текстом:**
   - Используйте `max_dimension=1920` (1080p)
   - Формат `webp` с `image_quality=80`
   - Можно снизить `frame_count` для экономии

3. **Проверка перед обработкой:**
   - ВСЕГДА используйте `dry_run=True` для длинных видео
   - Цель: 50-80% от 20 MB лимита

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `video_path` | str | - | Абсолютный путь к видео файлу |
| `prompt` | str | "Analyze..." | Промпт для анализа |
| `frame_mode` | str | "total" | Режим: "total", "fps", "interval" |
| `frame_count` | int | 10 | Кол-во кадров для "total" режима |
| `fps` | float | None | Кадров/сек для "fps" режима |
| `interval_sec` | float | None | Интервал в сек для "interval" |
| `max_dimension` | int | 1920 | Макс. размер стороны (1080p) |
| `image_format` | str | "webp" | "webp" или "jpeg" |
| `image_quality` | int | 80 | Качество 1-100 |
| `include_audio` | bool | True | Извлекать аудио |
| `audio_bitrate` | int | 64 | 64, 32 или 24 kbps |
| `dry_run` | bool | False | Только оценка размера |
| `model_name` | str | "gemini-2.5-flash" | Gemini модель |

## Ограничения MVP

- ✅ Видео до ~60 минут (зависит от параметров)
- ✅ Проверка < 20 MB перед отправкой
- ❌ Автоматическое разделение длинных видео (версия 2.0)
- ❌ Кеширование контекста (версия 2.0)
- ❌ Извлечение кадров по конкретным timestamp (версия 2.0)

## Поддерживаемые форматы

MP4, MPEG, MOV, AVI, MKV, WEBM и другие форматы, поддерживаемые ffmpeg.
