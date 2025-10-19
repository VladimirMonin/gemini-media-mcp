# 💡 Usage Guide

## Basic Usage

### Analyze Image with Default Settings

```python
# In your MCP client (Claude, Cursor, etc.)
Analyze image: /path/to/image.jpg
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
  "model": "gemini-2.5-pro",
  "custom_prompt": "Describe this image in detail"
}
```

## Supported Formats

- **Images:** JPEG, PNG, GIF, WEBP, HEIC, HEIF
- **Max file size:** 20 MB

## Parameters Reference

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_path` | string | ✅ | Absolute path to image |
| `custom_prompt` | string | ❌ | Custom analysis prompt |
| `system_instruction_name` | string | ❌ | Preset prompt name |
| `model` | string | ❌ | Gemini model to use |

## Response Format

```json
{
  "success": true,
  "description": "Analysis result...",
  "summary": "Brief summary...",
  "key_elements": ["element1", "element2"],
  "colors": ["red", "blue"],
  "mood": "calm",
  "technical_details": {
    "resolution": "1920x1080",
    "format": "JPEG"
  }
}
```

## Next Steps

- [📚 API Reference](api-reference.md) - Complete API documentation
- [🎯 Examples](examples.md) - Real usage examples

---

**Issues?** Check [Common Issues](common-issues.md)
