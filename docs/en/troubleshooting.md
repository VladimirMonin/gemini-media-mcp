# 🔧 Troubleshooting

## Server Won't Start

### ❌ Error: "Module not found"

**Solution:**

```bash
pip install -r requirements.txt
```

### ❌ Error: "GEMINI_API_KEY not set"

**Solution:**

1. Check `.env` file exists in project root
2. Verify key format: `GEMINI_API_KEY="your_key_here"`
3. Restart server

### ❌ Error: "Permission denied"

**Solution (Windows):**

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Connection Issues

### ❌ MCP Client Can't Connect

**Check:**

1. Virtual environment path in config is correct
2. Server path points to `server.py`
3. Restart MCP client completely

**Test manually:**

```bash
python server.py
```

### ❌ Server Running But Not Responding

**Solution:**

1. Check logs in console
2. Verify API key is valid
3. Test API key:

```bash
python -c "from config import GEMINI_API_KEY; print('Key loaded' if GEMINI_API_KEY else 'Missing')"
```

## API Errors

### ❌ Error: "Invalid API key"

**Solution:**

1. Get new key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Update `.env` file
3. Restart server

### ❌ Error: "Rate limit exceeded"

**Solution:**

- Wait a few minutes before trying again
- Consider upgrading API plan

### ❌ Error: "File too large"

**Solution:**

- Maximum file size is 20 MB for images and 19.5 MB for audio.
- Resize or re-encode the media file before analysis.

## Image Analysis Issues

### ❌ Error: "Unsupported image format"

**Supported formats:**

- JPEG, PNG, GIF, WEBP, HEIC, HEIF

**Solution:**
Convert image using online tools or:

```bash
pip install pillow
python -c "from PIL import Image; Image.open('input.bmp').save('output.jpg')"
```

### ❌ Error: "Image file not found"

**Solution:**

- Use absolute paths: `C:\Users\Name\Pictures\photo.jpg`
- Check file exists and readable

## Audio Analysis Issues

### ❌ Error: "Unsupported audio format"

**Supported formats:**

- MP3, WAV, AIFF, AAC, OGG, FLAC

**Solution:**
Convert the audio file using a tool like FFmpeg or an online converter.

### ❌ Error: "Invalid analysis_type"

**Solution:**
Ensure you are using one of the supported analysis types: `summary`, `transcription`, or `detailed`.

## Getting More Help

- [Common Issues](common-issues.md) - Specific error scenarios
- [GitHub Issues](https://github.com/VladimirMonin/gemini-media-mcp/issues)

---

**Still stuck?** Open an issue with:

- Error message
- Operating system
- Python version (`python --version`)
