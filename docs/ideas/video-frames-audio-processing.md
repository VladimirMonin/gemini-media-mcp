# Video Processing: Frames + Audio Strategy

## Идея пользователя

Вместо использования дорогого нативного Video API, **извлекать кадры из видео** и **аудио-дорожку отдельно**, затем отправлять их в одном запросе к Gemini API как набор изображений + аудио.

**Потенциальные преимущества:**

- Контроль над количеством кадров (экономия токенов)
- Возможность применить ресайз к кадрам (дополнительная экономия)
- Гибкость в выборе качества vs стоимость

## Анализ официальной документации

### Поддержка Video API

Согласно [`video.md`](gem/video.md):

**Нативный Video API:**

```python
myfile = client.files.upload(file="path/to/sample.mp4")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[myfile, "Summarize this video"]
)
```

**Токенизация видео (из документации):**

> - **Individual frames** (sampled at 1 FPS):
>   - If `mediaResolution` is set to **low**: **66 tokens per frame**
>   - Otherwise: **258 tokens per frame**
> - **Audio**: **32 tokens per second**
> - **Total**: Approximately **300 tokens per second** at default media resolution, or **100 tokens per second** at low media resolution

**Лимиты:**

- Модели с 2M контекстом: до **2 часов** видео (default) или **6 часов** (low resolution)
- Модели с 1M контекстом: до **1 часа** видео (default) или **3 часа** (low resolution)

### Поддержка множественных медиа в одном запросе

Согласно [`image_understainding.md`](gem/image_understainding.md):

```python
contents = [prompt, image1, image2, image3, ...]
```

> You can provide multiple images in a single prompt by including multiple image `Part` objects in the `contents` array.

**Лимит:** До **3,600 изображений** на запрос.

Согласно [`audio.md`](gem/audio.md), аудио также можно отправлять как `Part`:

```python
myfile = client.files.upload(file="path/to/sample.mp3")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=["Describe this audio clip", myfile]
)
```

### Комбинирование изображений и аудио

**ВЫВОД:** Документация явно НЕ запрещает миксовать изображения и аудио в одном запросе.

Согласно [`video.md`](gem/video.md), видео состоит из:

- Кадров (изображений)
- Аудио-дорожки

Это означает, что **теоретически** можно отправить:

```python
contents = [prompt, frame1, frame2, frame3, audio_part]
```

**НО:** В документации нет явного примера такого использования.

## Сравнение: Нативное Video API vs Frames + Audio

### Нативное Video API

**10 секунд видео, default media resolution:**

- Кадры: 10 сек × 1 FPS × 258 токенов = **2,580 токенов**
- Аудио: 10 сек × 32 токена = **320 токенов**
- **Итого: ~3,000 токенов** (с учетом метаданных)

**10 секунд видео, low media resolution:**

- Кадры: 10 сек × 1 FPS × 66 токенов = **660 токенов**
- Аудио: 10 сек × 32 токена = **320 токенов**
- **Итого: ~1,000 токенов**

### Подход "Frames + Audio"

**10 секунд видео, настройки: fps=1.0, quality='fhd' (1920px):**

- Кадры: 10 кадров × ~1,500 токенов = **15,000 токенов**
- Аудио: 10 сек × 32 токена = **320 токенов**
- **Итого: ~15,320 токенов** ❌ **В 5 РАЗ ДОРОЖЕ**

**10 секунд видео, настройки: fps=0.5, quality='balanced' (960px):**

- Кадры: 5 кадров × ~1,500 токенов = **7,500 токенов**
- Аудио: 10 сек × 32 токена = **320 токенов**
- **Итого: ~7,820 токенов** ❌ **В 2.5 РАЗА ДОРОЖЕ**

**10 секунд видео, настройки: fps=0.5, quality='economy' (384px):**

- Кадры: 5 кадров × 258 токенов = **1,290 токенов**
- Аудио: 10 сек × 32 токена = **320 токенов**
- **Итого: ~1,610 токенов** ✅ **Сопоставимо с low resolution**

## Выводы

### Когда нативное Video API лучше

1. ✅ **Полное видео:** Когда нужно проанализировать всё видео целиком
2. ✅ **Длинные видео:** >1 минуты (эффективнее по токенам)
3. ✅ **Простота:** Не требует извлечения кадров и аудио
4. ✅ **Стоимость:** **В 2-5 раз дешевле** при сопоставимом качестве
5. ✅ **Метаданные:** Автоматические временные метки каждую секунду

### Когда подход "Frames + Audio" может быть полезен

1. ✅ **UHD видео с мелким текстом:** Нативное API ограничено 1 FPS и автоматическим разрешением
2. ✅ **Специфические моменты:** Когда нужны точные кадры в конкретные моменты времени
3. ✅ **Контроль качества:** Полный контроль над разрешением каждого кадра
4. ✅ **Анализ статики:** Видео с редкими изменениями (лекции, презентации)

### Рекомендация

**ИСПОЛЬЗОВАТЬ НАТИВНОЕ VIDEO API** в 95% случаев, так как:

- **Дешевле** в 2-5 раз
- **Проще** в использовании
- **Оптимизировано** Google для видео-анализа
- Поддерживает **настройку FPS** и **clipping**

## Случаи для подхода "Frames + Audio"

### Сценарий 1: UHD видео-инструкция с текстом

**Проблема:** Нативное Video API сэмплирует на 1 FPS с автоматическим разрешением, которое может быть недостаточным для читаемости мелкого текста.

**Решение:**

```python
def analyze_uhd_video_with_text(
    video_path: str,
    prompt: str,
    fps: float = 1.0,
    frame_quality: str = 'fhd'
):
    """Analyze UHD video with high-quality frames for text readability.
    
    Args:
        video_path: Path to video file
        prompt: Analysis prompt
        fps: Frame extraction rate (default: 1.0 = 1 frame/sec)
        frame_quality: Quality preset ('fhd', 'uhd')
    """
    # Extract video frames
    frames = extract_video_frames(video_path, fps=fps)
    
    # Resize frames based on quality preset
    QUALITY_PRESETS = {
        'uhd': None,    # No resize
        'fhd': 1920,    # Full HD
        'hd': 1280,     # HD
    }
    
    max_dimension = QUALITY_PRESETS.get(frame_quality, 1920)
    processed_frames = [
        resize_image(frame, max_dimension)
        for frame in frames
    ]
    
    # Extract audio
    audio_bytes = extract_audio(video_path)
    audio_part = types.Part(
        inline_data=types.Blob(
            data=audio_bytes,
            mime_type='audio/mp3'
        )
    )
    
    # Create content with frames + audio
    contents = [prompt] + processed_frames + [audio_part]
    
    # Generate response
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents
    )
    
    return response.text
```

**Стоимость (10 сек, fps=1.0, quality='fhd'):**

- ~15,000 токенов (дорого, но текст читается)

**VS Нативное API:**

- ~3,000 токенов, но текст может быть нечитаемым

### Сценарий 2: Выборочный анализ ключевых моментов

**Проблема:** Нужно проанализировать только определенные моменты длинного видео (например, каждые 30 секунд).

**Решение:**

```python
def analyze_key_moments(
    video_path: str,
    prompt: str,
    timestamps: list[float],  # [5.0, 15.0, 45.0, 90.0]
    frame_quality: str = 'hd'
):
    """Extract and analyze specific frames at given timestamps.
    
    Args:
        video_path: Path to video file
        prompt: Analysis prompt
        timestamps: List of timestamps in seconds
        frame_quality: Quality preset
    """
    frames = extract_frames_at_timestamps(video_path, timestamps)
    
    # Process frames
    QUALITY_PRESETS = {'fhd': 1920, 'hd': 1280, 'balanced': 960}
    max_dimension = QUALITY_PRESETS.get(frame_quality, 1280)
    
    processed_frames = [
        resize_image(frame, max_dimension)
        for frame in frames
    ]
    
    # Extract audio segments around timestamps (±5 sec each)
    audio_segments = extract_audio_segments(
        video_path,
        timestamps,
        duration=10  # 10 sec segments
    )
    
    # Create prompt with timestamp context
    timestamp_context = f"Analyzing {len(timestamps)} key moments at: " + \
                       ", ".join([f"{t:.1f}s" for t in timestamps])
    
    enhanced_prompt = f"{timestamp_context}\n\n{prompt}"
    
    # Build content
    contents = [enhanced_prompt]
    for i, (frame, audio) in enumerate(zip(processed_frames, audio_segments)):
        contents.append(f"Frame at {timestamps[i]:.1f}s:")
        contents.append(frame)
        if audio:
            contents.append(audio)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents
    )
    
    return response.text
```

**Стоимость (4 ключевых момента, quality='hd'):**

- 4 кадра × ~3,000 токенов = **~12,000 токенов**
- Аудио: 4 сегмента × 10 сек × 32 = **~1,280 токенов**
- **Итого: ~13,280 токенов**

**VS Нативное API (анализ всего 90-сек видео):**

- 90 сек × ~100 токенов (low res) = **~9,000 токенов** ✅ Дешевле
- Но анализируется ВСЁ видео, а не только ключевые моменты

### Сценарий 3: Сравнение кадров до/после

**Проблема:** Нужно сравнить визуальные изменения между двумя моментами времени.

**Решение:**

```python
def compare_video_moments(
    video_path: str,
    timestamp_before: float,
    timestamp_after: float,
    prompt: str = "What changed between these two moments?"
):
    """Compare two specific frames from video.
    
    Args:
        video_path: Path to video
        timestamp_before: First timestamp (seconds)
        timestamp_after: Second timestamp (seconds)
        prompt: Comparison prompt
    """
    frame_before = extract_frame_at_timestamp(video_path, timestamp_before)
    frame_after = extract_frame_at_timestamp(video_path, timestamp_after)
    
    # High quality for comparison
    frame_before = resize_image(frame_before, 1920)
    frame_after = resize_image(frame_after, 1920)
    
    # Optional: extract audio between timestamps
    audio_segment = extract_audio_segment(
        video_path,
        start=timestamp_before,
        end=timestamp_after
    )
    
    enhanced_prompt = f"""Compare these two frames from a video:
- Frame 1: at {timestamp_before:.1f}s
- Frame 2: at {timestamp_after:.1f}s
Time difference: {timestamp_after - timestamp_before:.1f}s

{prompt}"""
    
    contents = [
        enhanced_prompt,
        "Frame BEFORE:",
        frame_before,
        "Frame AFTER:",
        frame_after
    ]
    
    if audio_segment:
        contents.append("Audio between frames:")
        contents.append(audio_segment)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents
    )
    
    return response.text
```

**Стоимость:**

- 2 кадра × ~1,500 токенов = **~3,000 токенов**
- Аудио: ~320 токенов
- **Итого: ~3,320 токенов**

Сопоставимо с нативным API, но **точечный анализ** вместо всего видео.

## Реализация: Вспомогательные функции

### Извлечение кадров из видео

```python
import cv2
from PIL import Image
import numpy as np

def extract_video_frames(
    video_path: str,
    fps: float = 1.0
) -> list[Image.Image]:
    """Extract frames from video at specified FPS.
    
    Args:
        video_path: Path to video file
        fps: Frames per second to extract
    
    Returns:
        List of PIL Images
    """
    cap = cv2.VideoCapture(video_path)
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / fps)
    
    frames = []
    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_idx % frame_interval == 0:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            frames.append(pil_image)
        
        frame_idx += 1
    
    cap.release()
    return frames


def extract_frame_at_timestamp(
    video_path: str,
    timestamp: float
) -> Image.Image:
    """Extract single frame at specific timestamp.
    
    Args:
        video_path: Path to video file
        timestamp: Time in seconds
    
    Returns:
        PIL Image
    """
    cap = cv2.VideoCapture(video_path)
    
    # Seek to timestamp
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError(f"Could not extract frame at {timestamp}s")
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)


def extract_frames_at_timestamps(
    video_path: str,
    timestamps: list[float]
) -> list[Image.Image]:
    """Extract frames at multiple timestamps.
    
    Args:
        video_path: Path to video file
        timestamps: List of timestamps in seconds
    
    Returns:
        List of PIL Images
    """
    return [
        extract_frame_at_timestamp(video_path, ts)
        for ts in timestamps
    ]
```

### Извлечение аудио

```python
from pydub import AudioSegment
import io

def extract_audio(
    video_path: str,
    format: str = 'mp3'
) -> bytes:
    """Extract full audio track from video.
    
    Args:
        video_path: Path to video file
        format: Audio format (mp3, wav, etc.)
    
    Returns:
        Audio bytes
    """
    audio = AudioSegment.from_file(video_path)
    
    buffer = io.BytesIO()
    audio.export(buffer, format=format)
    
    return buffer.getvalue()


def extract_audio_segment(
    video_path: str,
    start: float,
    end: float,
    format: str = 'mp3'
) -> bytes:
    """Extract audio segment between timestamps.
    
    Args:
        video_path: Path to video
        start: Start time in seconds
        end: End time in seconds
        format: Audio format
    
    Returns:
        Audio bytes
    """
    audio = AudioSegment.from_file(video_path)
    
    # Extract segment (pydub uses milliseconds)
    segment = audio[int(start * 1000):int(end * 1000)]
    
    buffer = io.BytesIO()
    segment.export(buffer, format=format)
    
    return buffer.getvalue()


def extract_audio_segments(
    video_path: str,
    timestamps: list[float],
    duration: float = 10.0,
    format: str = 'mp3'
) -> list[bytes]:
    """Extract audio segments around timestamps.
    
    Args:
        video_path: Path to video
        timestamps: List of center timestamps
        duration: Duration of each segment in seconds
        format: Audio format
    
    Returns:
        List of audio bytes
    """
    segments = []
    half_duration = duration / 2
    
    for ts in timestamps:
        start = max(0, ts - half_duration)
        end = ts + half_duration
        
        segment = extract_audio_segment(video_path, start, end, format)
        segments.append(segment)
    
    return segments
```

### Создание Parts для Gemini

```python
from google.genai import types

def create_audio_part(audio_bytes: bytes, mime_type: str = 'audio/mp3') -> types.Part:
    """Create audio Part for Gemini API.
    
    Args:
        audio_bytes: Audio data
        mime_type: MIME type
    
    Returns:
        Part object
    """
    return types.Part(
        inline_data=types.Blob(
            data=audio_bytes,
            mime_type=mime_type
        )
    )


def create_video_analysis_content(
    frames: list[Image.Image],
    audio_bytes: bytes,
    prompt: str,
    frame_timestamps: Optional[list[float]] = None
) -> list:
    """Create content array for Gemini with frames + audio.
    
    Args:
        frames: List of PIL Images
        audio_bytes: Audio data
        prompt: Analysis prompt
        frame_timestamps: Optional timestamps for context
    
    Returns:
        Content array for generateContent
    """
    contents = [prompt]
    
    # Add frames with optional timestamps
    for i, frame in enumerate(frames):
        if frame_timestamps:
            contents.append(f"Frame at {frame_timestamps[i]:.1f}s:")
        contents.append(frame)
    
    # Add audio
    if audio_bytes:
        contents.append("Audio track:")
        contents.append(create_audio_part(audio_bytes))
    
    return contents
```

## Итоговая рекомендация

### Используйте нативное Video API для

1. ✅ Обычного анализа видео (описание, резюме, Q&A)
2. ✅ Длинных видео (>1 минута)
3. ✅ Видео без мелкого текста
4. ✅ Когда важна экономия токенов

**Настройки:**

```python
# Для экономии
config = types.GenerateContentConfig(
    media_resolution='LOW'  # 66 tokens/frame
)

# Для длинных видео
video_metadata = types.VideoMetadata(
    fps=0.5  # 1 кадр каждые 2 секунды
)
```

### Используйте подход "Frames + Audio" для

1. ✅ UHD видео с мелким текстом (инструкции, презентации)
2. ✅ Анализа конкретных моментов (не всего видео)
3. ✅ Сравнения кадров до/после
4. ✅ Когда нужен полный контроль над качеством кадров

**Настройки:**

```python
# Для UHD с текстом
analyze_uhd_video_with_text(
    video_path='tutorial.mp4',
    fps=1.0,
    frame_quality='fhd'  # 1920px max
)

# Для выборочного анализа
analyze_key_moments(
    video_path='lecture.mp4',
    timestamps=[30.0, 120.0, 300.0],  # Ключевые моменты
    frame_quality='hd'
)
```

## Зависимости

Для реализации понадобятся:

```python
# requirements.txt
opencv-python>=4.8.0     # Извлечение кадров
pydub>=0.25.0            # Извлечение аудио
ffmpeg-python>=0.2.0     # Работа с видео/аудио
Pillow>=10.0.0           # Обработка изображений
google-genai>=1.0.0      # Gemini API
```

**Системные зависимости:**

- FFmpeg (для pydub и opencv)

## Лимиты и ограничения

1. **Размер запроса:** 20MB для inline-данных (используйте Files API для больших файлов)
2. **Максимум изображений:** 3,600 на запрос
3. **Обработка:** Извлечение кадров и аудио требует CPU/RAM
4. **Стоимость:** В большинстве случаев **дороже нативного Video API**
