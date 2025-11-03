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

### Text-to-Image Generation

```json
{
  "user_prompt": "A cat wearing a hat, pixel art style"
}
```

### Text+Image(s)-to-Image Generation

```json
{
  "user_prompt": "Create a similar image in cyberpunk style",
  "image_paths": ["/path/to/reference1.jpg", "/path/to/reference2.png"]
}
```

### Generation with Custom Output Path

```json
{
  "user_prompt": "Futuristic city with neon lights",
  "output_path": "/path/to/save/image.png"
}
```

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

- **Images:** JPEG, PNG, GIF, WEBP, HEIC, HEIF (Max size: 20 MB)
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
| `user_prompt` | string | ✅ | Text description for image generation |
| `image_paths` | string[] | ❌ | List of absolute paths to reference images |
| `output_path` | string | ❌ | Path to save the generated image |

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

- `gemini-2.5-flash-lite` - Fast and efficient (default)
- `gemini-2.5-flash` - Balanced performance
- `gemini-2.5-pro` - Highest quality
- `gemini-2.5-flash-image-preview` - Image generation model

## Next Steps

- [📚 Configuration Guide](configuration.md) - Complete configuration documentation
- [🔧 Troubleshooting](troubleshooting.md) - Common issues and solutions
- [❓ Common Issues](common-issues.md) - Frequently asked questions

---

**Issues?** Check [Troubleshooting](troubleshooting.md)
