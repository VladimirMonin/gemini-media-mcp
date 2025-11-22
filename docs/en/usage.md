# 💡 Usage Guide

## Basic Usage

### Analyze Image with Default Settings

```python
# In your MCP client (Claude, Cursor, etc.)
Analyze image: /path/to/image.jpg
```

### Analyze Audio with Default Settings

```python
# In your MCP client (Claude, Cursor, etc.)
Analyze audio: /path/to/audio.mp3
```

### Custom Analysis Prompt

```python
Analyze /path/to/photo.jpg and describe the emotions and atmosphere
```

## Advanced Usage

### Using System Instructions

Available preset prompts in `config.py`:

- `"default"` - Comprehensive analysis
- `"technical"` - Technical details (resolution, format, quality)
- `"creative"` - Artistic and creative description

**Example:**

```json
{
  "image_path": "/path/to/image.jpg",
  "system_instruction_name": "technical"
}
```

### Custom Model Selection

```json
{
  "image_path": "/path/to/photo.jpg",
  "model_name": "gemini-2.5-pro",
  "user_prompt": "Describe this image in detail"
}
```

## Image Generation

### Model Selection

The image generation tool supports two models with different capabilities:

| Model | Speed | Resolution | Quality | Best For |
|-------|-------|------------|---------|----------|
| **fast** (gemini-2.5-flash-image) | ⚡ Fast | 1K only | Good | Quick drafts, iterations, speed priority |
| **pro** (gemini-3-pro-image-preview) | 🎨 Slower | 1K, 2K, 4K | Excellent | High-quality art, precise text rendering, complex scenes |

**Default:** `fast` model for most use cases.

### Text-to-Image Generation

**Basic generation (fast model):**

```json
{
  "prompt": "A cat wearing a hat, pixel art style",
  "output_path": "/path/to/save/cat.png"
}
```

**High-quality generation (pro model):**

```json
{
  "prompt": "A futuristic city with neon signs at night, cyberpunk style",
  "output_path": "/path/to/save/city.png",
  "model_type": "pro",
  "resolution": "2K",
  "aspect_ratio": "16:9"
}
```

### Text+Image(s)-to-Image Generation

**Image editing/style transfer:**

```json
{
  "prompt": "Create a similar image in cyberpunk style",
  "image_paths": ["/path/to/reference1.jpg", "/path/to/reference2.png"],
  "output_path": "/path/to/save/result.png"
}
```

**Pro model with multiple references (up to 14 images):**

```json
{
  "prompt": "Combine these elements into a professional product photo",
  "image_paths": [
    "/path/to/product.jpg",
    "/path/to/background.jpg",
    "/path/to/lighting_ref.jpg"
  ],
  "output_path": "/path/to/save/composite.png",
  "model_type": "pro",
  "resolution": "2K"
}
```

### Advanced Features (Pro Model)

**4K Resolution Output:**

```json
{
  "prompt": "Da Vinci style anatomical sketch of a butterfly",
  "output_path": "/path/to/save/butterfly.png",
  "model_type": "pro",
  "resolution": "4K",
  "aspect_ratio": "1:1"
}
```

**Precise Text Rendering:**

```json
{
  "prompt": "A modern tech company logo with the text 'AI Studio' in a clean sans-serif font",
  "output_path": "/path/to/save/logo.png",
  "model_type": "pro",
  "resolution": "2K"
}
```

### Aspect Ratios

Available aspect ratios for both models:
- `1:1` - Square
- `16:9` - Widescreen landscape (default)
- `9:16` - Vertical portrait
- `4:3` - Classic landscape
- `3:4` - Classic portrait
- `2:3`, `3:2`, `4:5`, `5:4`, `21:9` - Specialized ratios

**Example:**

```json
{
  "prompt": "Panoramic mountain landscape at sunset",
  "output_path": "/path/to/save/panorama.png",
  "aspect_ratio": "21:9"
}
```

### Generation with Custom Output Path

```json
{
  "prompt": "Futuristic city with neon lights",
  "output_path": "/path/to/save/image.png"
}
```

## GIF Animation Analysis

### Basic GIF Analysis (Recommended Settings)

Analyze UI tutorials, software demos, or any animated GIF with intelligent frame sampling:

```json
{
  "image_path": "/path/to/tutorial.gif",
  "prompt": "This is a VS Code feature demo. Describe each step.",
  "frame_count": 5,
  "quality": "fhd"
}
```

**Default settings:**

- **Mode:** `total` - evenly distributed frames
- **Frame count:** 5 frames (adjustable: 5-15+)
- **Quality:** `fhd` (1920px) - best for text readability
- **Model:** `gemini-2.5-flash`

### Frame Extraction Modes

#### 1. Total Mode (Recommended)

Extract fixed number of evenly distributed frames - perfect for UI tutorials:

```json
{
  "image_path": "/path/to/animation.gif",
  "mode": "total",
  "frame_count": 10,
  "quality": "fhd"
}
```

**Use cases:**

- 5 frames: Quick demos (10-30s)
- 10 frames: Detailed tutorials (30-90s)
- 15+ frames: Long sessions (2+ min)

#### 2. FPS Mode

Extract frames at specified rate (frames per second):

```json
{
  "image_path": "/path/to/animation.gif",
  "mode": "fps",
  "gif_fps": 1.0,
  "quality": "hd"
}
```

**Example:** `gif_fps: 1.0` = 1 frame every second

#### 3. Interval Mode

Extract frames at fixed time intervals:

```json
{
  "image_path": "/path/to/long_session.gif",
  "mode": "interval",
  "interval_sec": 5.0,
  "quality": "balanced"
}
```

**Example:** `interval_sec: 5.0` = one frame every 5 seconds

### Quality Presets

Choose quality based on your needs:

| Preset | Resolution | Best For | Token Cost |
|--------|------------|----------|------------|
| `fhd` | 1920px | UI tutorials with text (DEFAULT) | ~1,500/frame |
| `hd` | 1280px | General animations | ~1,000/frame |
| `balanced` | 960px | Budget-friendly | ~800/frame |
| `economy` | 768px | Minimal quality | ~600/frame |
| `uhd` | Original | Maximum detail | Varies |

### Advanced GIF Analysis

Add context to improve results:

```json
{
  "image_path": "/path/to/demo.gif",
  "prompt": "This demonstrates a chatbot conversation workflow. Analyze the user interaction patterns and UI responses.",
  "mode": "total",
  "frame_count": 8,
  "quality": "fhd",
  "model": "gemini-2.5-flash"
}
```

### Getting Guidelines

Get comprehensive usage guidelines and best practices:

```python
get_gif_guidelines()
```

Returns detailed information about:

- Frame count selection
- Quality preset recommendations
- Cost estimation
- Recommended workflows
- Example use cases

### Cost Estimation

**1080p (FHD) frames:**

- 5 frames ≈ 7,500 tokens
- 10 frames ≈ 15,000 tokens

**Balanced (960px) frames:**

- 10 frames ≈ 8,000 tokens

**Tip:** Use `get_gif_guidelines()` for detailed cost breakdown and recommendations.

## Audio Analysis

### Basic Audio Analysis

```json
{
  "audio_path": "/path/to/audio.mp3",
  "user_prompt": "Summarize this audio content",
  "analysis_type": "summary"
}
```

### Audio Transcription

```json
{
  "audio_path": "/path/to/audio.wav",
  "user_prompt": "Transcribe this audio",
  "analysis_type": "transcription"
}
```

### Advanced Audio Analysis

```json
{
  "audio_path": "/path/to/meeting.mp3",
  "user_prompt": "Extract action items and participants from this meeting",
  "analysis_type": "detailed",
  "model_name": "gemini-2.5-flash-lite",
  "output_path": "/path/to/analysis.json"
}
```

## Supported Formats

- **Images:** JPEG, PNG, GIF (static), WEBP, HEIC, HEIF (Max size: 20 MB)
- **GIF Animations:** Animated GIF files (processed frame-by-frame)
- **Audio:** MP3, WAV, AIFF, AAC, OGG, FLAC (Max size: 19.5 MB)

## Parameters Reference

### Image Analysis

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_path` | string | ✅ | Absolute path to the image file. |
| `user_prompt` | string | ❌ | A custom prompt for the analysis. |
| `system_instruction_name` | string | ❌ | The name of a preset system instruction (e.g., "default", "technical"). |
| `system_instruction_override` | string | ❌ | A custom system instruction to override the preset. |
| `system_instruction_file_path` | string | ❌ | Path to a file containing a custom system instruction. |
| `model_name` | string | ❌ | The specific Gemini model to use (e.g., "gemini-2.5-pro"). |

### Image Generation

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | ✅ | Text description for image generation (use detailed, descriptive English prompts) |
| `output_path` | string | ✅ | Absolute path where to save the generated image (e.g., "C:/Users/User/Desktop/result.png") |
| `image_paths` | string[] | ❌ | List of absolute paths to reference images for editing/style transfer (max 5 for fast, max 14 for pro) |
| `aspect_ratio` | string | ❌ | Output aspect ratio: '1:1', '16:9', '9:16', '4:3', '3:4', '2:3', '3:2', '4:5', '5:4', '21:9' (default: '16:9') |
| `resolution` | string | ❌ | Output resolution: '1K', '2K', '4K'. Note: 4K only available with pro model, fast model only supports 1K (default: '1K') |
| `model_type` | string | ❌ | Model selection: 'fast' (gemini-2.5-flash-image) or 'pro' (gemini-3-pro-image-preview) (default: 'fast') |

### Audio Analysis

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audio_path` | string | ✅ | Absolute path to audio file |
| `user_prompt` | string | ✅ | Custom analysis request |
| `analysis_type` | string | ❌ | Type of analysis (summary, transcription, detailed) |
| `model_name` | string | ❌ | Gemini model to use |
| `output_path` | string | ❌ | Path to save analysis result as JSON |

## Response Format

### Image Analysis Response

The server returns a structured JSON response based on the `ImageAnalysisResponse` model.

```json
{
  "alt_text": "A brief, accessible description of the image.",
  "detailed_analysis": "A comprehensive and detailed breakdown of the image content, context, and composition.",
  "summary": "An optional short summary of the analysis."
}
```

### Image Generation Response

```json
{
  "status": "success",
  "image_path": "/full/path/to/generated/image.png"
}
```

### Audio Analysis Response

```json
{
  "title": "Meeting Discussion",
  "summary": "Brief summary of the audio content",
  "transcription": "Full transcription of the audio",
  "participants": ["John Doe", "Jane Smith"],
  "hashtags": ["#meeting", "#discussion", "#action-items"],
  "action_items": ["Complete project documentation", "Schedule follow-up meeting"],
  "raw_text": "Raw text response from the model"
}
```

## Available Models

**Analysis Models:**
- `gemini-2.5-flash-lite` - Fast and efficient (default)
- `gemini-2.5-flash` - Balanced performance
- `gemini-2.5-pro` - Highest quality

**Image Generation Models:**
- `gemini-2.5-flash-image` (fast) - Quick drafts, iterations, 1K resolution only
- `gemini-3-pro-image-preview` (pro) - High-quality art, precise text rendering, up to 4K resolution, complex scenes

**Text-to-Speech Models:**
- `gemini-2.5-flash-preview-tts` - Standard quality (default)
- `gemini-2.5-pro-preview-tts` - Premium quality

## Audio Generation

### Get Generation Guide

Get list of available voices (30 prebuilt voices across 24 languages) and YAML structure examples:

```python
get_audio_generation_guide()
```

### Generate Speech from YAML Script

#### Single Voice Example

Create a YAML script `podcast.yaml`:

```yaml
cast:
  - name: "Host"
    voice: "Kore"

script:
  - speaker: "Host"
    text: "Welcome to our technology podcast!"
  - speaker: "Host"
    text: "Today we'll discuss the latest in AI."
```

Generate:

```python
generate_audio_from_yaml(yaml_path="/path/to/podcast.yaml")
# Result: output_audio/podcast.wav
```

#### Multi-Speaker Example

```yaml
cast:
  - name: "Grandpa"
    voice: "Orus"
  - name: "Grandma"
    voice: "Aoede"

style_prompt: "Russian folk tale, dramatic narration"

script:
  - speaker: "Grandpa"
    text: "Bake me a bun, grandma."
  - speaker: "Grandma"
    text: "What shall I bake it from? We have no flour."
  - speaker: "Grandpa"
    text: "Oh, grandma! Scrape the cupboard, sweep the flour bin."
```

Generate with custom path:

```python
generate_audio_from_yaml(
    yaml_path="/path/to/tale.yaml",
    model="gemini-2.5-pro-preview-tts",
    output_path="/path/to/save/tale.wav"
)
```

### Audio Generation Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `yaml_path` | string | ✅ | Absolute path to YAML script file |
| `model` | string | ❌ | TTS model (default: gemini-2.5-flash-preview-tts) |
| `output_path` | string | ❌ | Absolute path for output WAV (default: output_audio/filename.wav) |

### YAML Script Structure

```yaml
# Optional: style instruction for tone/accent control
style_prompt: "Calm and professional tone, news anchor style"

# Required: character list
cast:
  - name: "Name1"    # Character name
    voice: "Kore"    # Voice name (case-sensitive, capitalized)
  - name: "Name2"
    voice: "Orus"

# Required: dialogue/text
script:
  - speaker: "Name1"
    text: "First line of dialogue"
  - speaker: "Name2"
    text: "Response line"
```

### Audio Generation Features

- **Speaker Count:** 1-2 speakers (Gemini API limitation)
- **Voices:** 30 prebuilt voices with different characteristics
- **Languages:** Auto-detection from 24 supported languages
- **Output Format:** WAV, 24kHz, mono, 16-bit PCM
- **Style Prompt:** Optional instruction for speech manner control

## Next Steps

- [📚 Configuration Guide](configuration.md) - Complete configuration documentation
- [🔧 Troubleshooting](troubleshooting.md) - Common issues and solutions
- [❓ Common Issues](common-issues.md) - Frequently asked questions

---

**Issues?** Check [Troubleshooting](troubleshooting.md)
