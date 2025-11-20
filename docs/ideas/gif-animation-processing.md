# GIF Animation Processing Strategy

## Проблема

При попытке отправить GIF-анимацию через Gemini API возникает ошибка:

```json
{
  "error": "Image analysis failed",
  "details": "cannot write mode P as JPEG",
  "raw_response": null
}
```

**Причина:** GIF-изображения используют палитровый режим PIL (`mode 'P'`), который SDK Google Gemini не может напрямую конвертировать в JPEG (SDK автоматически конвертирует PIL изображения в JPEG при отправке).

## Требования пользователя

Пользователь создает **UHD GIF-анимации** (разрешение до 3840×2160) для инструкций по работе с графическими интерфейсами программ, включая:

- Запуск терминала с кодом
- Пошаговые действия в UI
- Демонстрации с текстом и деталями

**Критичные требования:**

1. **Читаемость текста** - шрифты не должны превращаться в кашу
2. **Контроль частоты кадров** - возможность регулировать количество извлекаемых кадров
3. **Баланс стоимость/качество** - оптимизация токенов без потери качества

## Решение на основе официальной документации

### 1. Конвертация режима изображения

Согласно документации [`image_understainding.md`](gem/image_understainding.md), Gemini поддерживает следующие форматы:

- PNG (`image/png`)
- JPEG (`image/jpeg`)
- WEBP (`image/webp`)
- HEIC/HEIF

**GIF НЕ указан** в списке поддерживаемых форматов.

SDK автоматически конвертирует PIL изображения, но падает на палитровом режиме. **Решение:** конвертировать режим изображения перед отправкой:

```python
# Convert palette mode (P) and other incompatible modes to RGB
if image.mode in ('P', 'LA', 'PA'):
    image = image.convert('RGB')
elif image.mode == 'RGBA':
    pass  # Keep RGBA - it's supported
elif image.mode not in ('RGB', 'L'):
    image = image.convert('RGB')
```

### 2. Извлечение кадров из анимации

Согласно документации [`video.md`](gem/video.md), Gemini поддерживает **множественные изображения** в одном запросе:

```python
contents = [prompt, image1, image2, image3, ...]  # До 3,600 изображений
```

Также документация [`image_understainding.md`](gem/image_understainding.md) подтверждает возможность отправки множественных изображений:

> You can provide multiple images in a single prompt by including multiple image `Part` objects in the `contents` array.

**Решение:** Извлекать кадры из GIF и отправлять как последовательность изображений.

### 3. Контроль частоты извлечения кадров

Пользователь хочет регулировать частоту **в секундах**, а не по номерам кадров:

- `gif_fps=1.0` → 1 кадр в секунду
- `gif_fps=0.5` → 1 кадр каждые 2 секунды
- `gif_fps=2.0` → 2 кадра в секунду

**Реализация:**

```python
def extract_gif_frames(
    image: Image.Image,
    fps: float = 1.0
) -> list[Image.Image]:
    """Extract frames from animated GIF at specified FPS.
    
    Args:
        image: PIL Image object (animated GIF)
        fps: Frames per second to extract (e.g., 1.0 = 1 frame/sec)
    
    Returns:
        List of extracted frames as PIL Images
    """
    if not getattr(image, 'is_animated', False):
        return [image]
    
    frames = []
    
    # Get GIF info
    gif_duration = image.info.get('duration', 100)  # milliseconds per frame
    gif_fps = 1000.0 / gif_duration  # GIF's native FPS
    
    # Calculate frame step
    frame_step = max(1, int(gif_fps / fps))
    
    # Extract frames
    for frame_num in range(0, image.n_frames, frame_step):
        image.seek(frame_num)
        frame = image.copy()
        
        # Convert mode for compatibility
        if frame.mode in ('P', 'LA', 'PA'):
            frame = frame.convert('RGB')
        elif frame.mode not in ('RGB', 'RGBA', 'L'):
            frame = frame.convert('RGB')
        
        frames.append(frame)
    
    return frames
```

### 4. Контроль качества изображения

#### Токенизация изображений (из документации)

Согласно [`image_understainding.md`](gem/image_understainding.md):

- **≤ 384px** (обе стороны): **258 токенов** (минимум)
- **> 384px**: изображение делится на тайлы **768×768px**, каждый = **258 токенов**

**Формула:**

```
crop_unit = floor(min(width, height) / 1.5)
tiles_count = (width / crop_unit) × (height / crop_unit)
total_tokens = tiles_count × 258
```

**Примеры:**

- 384×384 → **258 токенов**
- 960×540 → 6 тайлов → **1,548 токенов**
- 1920×1080 → ~6 тайлов → **~1,500 токенов**
- 3840×2160 → ~24 тайла → **~6,000 токенов**

#### Стратегия качества для GIF-анимаций

**Проблема:** UHD анимации с мелким текстом требуют высокого разрешения для читаемости.

**Грейды качества:**

```python
GIF_QUALITY_PRESETS = {
    'uhd': None,           # Без ресайза (3840×2160) - максимум деталей
    'fhd': 1920,           # Full HD - текст 12pt+ читается отлично
    'hd': 1280,            # HD - текст 14pt+ читается хорошо
    'balanced': 960,       # Баланс - крупный текст читается
    'economy': 768,        # Экономия - только крупный текст
}
```

**Рекомендации:**

- Для **UI-инструкций с текстом**: `quality='fhd'` (1920px)
- Для **общих анимаций**: `quality='hd'` (1280px)
- Для **длинных анимаций** (>30 сек): `quality='balanced'` (960px)

#### Ресайз изображения

```python
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
```

### 5. Специальный промпт для анимаций

Согласно документации [`video.md`](gem/video.md), при отправке кадров видео Gemini понимает контекст временной последовательности.

**Адаптация для GIF:**

```python
def create_animation_prompt(
    user_prompt: str,
    frame_count: int,
    gif_fps: float
) -> str:
    """Create context-aware prompt for GIF animation analysis.
    
    Args:
        user_prompt: User's original prompt
        frame_count: Number of extracted frames
        gif_fps: Extraction rate (frames per second)
    
    Returns:
        Enhanced prompt with animation context
    """
    time_per_frame = 1.0 / gif_fps
    
    context_prompt = f"""This is a sequence of {frame_count} frames extracted from an animated GIF.
Frames are sampled at {gif_fps} FPS (1 frame every {time_per_frame:.1f} seconds).
This is a UI/software instruction showing step-by-step actions in a graphical interface.

Pay attention to:
- Text labels, buttons, menus, and UI elements
- Mouse cursor position and movements
- Changes between frames (what action was performed)
- Sequential progression of steps

User request: {user_prompt}"""
    
    return context_prompt
```

## Расчёт стоимости

### Пример 1: UHD GIF-инструкция (5 секунд)

**Параметры:**

- Разрешение: 3840×2160
- Длительность: 5 секунд
- Настройки: `gif_fps=1.0`, `quality='fhd'`

**Расчёт:**

- Кадров: 5 сек × 1.0 FPS = **5 кадров**
- Разрешение после ресайза: 1920×1080
- Токенов на кадр: ~6 тайлов × 258 = **~1,500 токенов**
- **Итого: ~7,500 токенов**

### Пример 2: Экономный вариант

**Параметры:**

- Настройки: `gif_fps=0.5`, `quality='balanced'`

**Расчёт:**

- Кадров: 5 сек × 0.5 FPS = **3 кадра**
- Разрешение: 960×540
- Токенов на кадр: ~6 тайлов × 258 = **~1,500 токенов**
- **Итого: ~4,500 токенов**

### Пример 3: Максимальное качество

**Параметры:**

- Настройки: `gif_fps=1.0`, `quality='uhd'` (без ресайза)

**Расчёт:**

- Кадров: **5 кадров**
- Разрешение: 3840×2160 (оригинал)
- Токенов на кадр: ~24 тайла × 258 = **~6,000 токенов**
- **Итого: ~30,000 токенов** ⚠️ ДОРОГО

## Итоговая реализация

### Функция обработки GIF

```python
def process_gif_animation(
    image_path: str,
    prompt: str,
    gif_fps: float = 1.0,
    quality: str = 'fhd',
    add_animation_context: bool = True
) -> dict:
    """Process GIF animation for Gemini API.
    
    Args:
        image_path: Path to GIF file
        prompt: User's analysis prompt
        gif_fps: Frame extraction rate (frames per second)
        quality: Quality preset ('uhd', 'fhd', 'hd', 'balanced', 'economy')
        add_animation_context: Add special prompt for animation context
    
    Returns:
        dict with processed frames and enhanced prompt
    """
    # Quality presets
    QUALITY_PRESETS = {
        'uhd': None,
        'fhd': 1920,
        'hd': 1280,
        'balanced': 960,
        'economy': 768,
    }
    
    max_dimension = QUALITY_PRESETS.get(quality, 1920)
    
    # Load GIF
    image = Image.open(image_path)
    
    # Extract frames
    frames = extract_gif_frames(image, fps=gif_fps)
    
    # Resize frames
    processed_frames = [
        resize_image(frame, max_dimension)
        for frame in frames
    ]
    
    # Create enhanced prompt
    if add_animation_context:
        enhanced_prompt = create_animation_prompt(
            prompt,
            len(processed_frames),
            gif_fps
        )
    else:
        enhanced_prompt = prompt
    
    # Calculate estimated tokens
    estimated_tokens = estimate_tokens(processed_frames)
    
    return {
        'frames': processed_frames,
        'prompt': enhanced_prompt,
        'frame_count': len(processed_frames),
        'estimated_tokens': estimated_tokens,
        'quality': quality,
        'fps': gif_fps
    }
```

### Вспомогательные функции

```python
def estimate_tokens(frames: list[Image.Image]) -> int:
    """Estimate token count for frames.
    
    Args:
        frames: List of PIL Images
    
    Returns:
        Estimated total tokens
    """
    total_tokens = 0
    
    for frame in frames:
        width, height = frame.size
        
        # Simple estimation based on documentation formula
        if width <= 384 and height <= 384:
            tokens = 258
        else:
            min_dim = min(width, height)
            crop_unit = int(min_dim / 1.5)
            tiles_w = (width + crop_unit - 1) // crop_unit
            tiles_h = (height + crop_unit - 1) // crop_unit
            tokens = tiles_w * tiles_h * 258
        
        total_tokens += tokens
    
    return total_tokens
```

## Рекомендации

### Для UI-инструкций с текстом

- **Quality:** `'fhd'` (1920px) - отличная читаемость текста 12pt+
- **FPS:** `1.0` - достаточно для пошаговых инструкций
- **Стоимость:** ~7,500 токенов на 5 сек анимации

### Для длинных анимаций (>30 сек)

- **Quality:** `'balanced'` (960px) - баланс стоимость/качество
- **FPS:** `0.5` - экономия кадров
- **Стоимость:** ~2,700 токенов на 5 сек анимации

### Для демонстраций без текста

- **Quality:** `'hd'` (1280px) или `'balanced'` (960px)
- **FPS:** `1.0`
- **Стоимость:** ~3,000-5,000 токенов на 5 сек анимации

### Лимиты

- **Максимум изображений:** 3,600 на запрос
- **Максимум размер:** 20MB на inline-данные (используйте Files API для больших файлов)

## Преимущества подхода

1. ✅ **Совместимость:** Обход ограничения на GIF через конвертацию
2. ✅ **Контроль:** Точная настройка частоты кадров и качества
3. ✅ **Экономия:** Оптимизация токенов без потери читаемости
4. ✅ **Гибкость:** Грейды качества под разные сценарии
5. ✅ **Контекст:** Специальный промпт для понимания анимации

## Ограничения

1. ⚠️ **Память:** Извлечение кадров требует RAM (особенно UHD)
2. ⚠️ **Стоимость:** UHD анимации очень дорогие (30,000+ токенов)
3. ⚠️ **Обработка:** Конвертация и ресайз занимают время
