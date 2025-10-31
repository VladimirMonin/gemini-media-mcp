# 🚀 Quick Start

## 1. Test Server Manually

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Run server
python server.py
```

**Expected output:**

```
INFO - Запуск Gemini Image Analyzer MCP сервера...
```

Press `Ctrl+C` to stop.

## 2. Connect to MCP Client

### Claude Desktop

1. Edit config file (see [Configuration](configuration.md))
2. Restart Claude Desktop
3. Check server is available in Claude

### Cursor

1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "MCP Settings"
3. Add server configuration
4. Restart Cursor

## 3. First Analysis

### Image Analysis
In your MCP client, ask:

```
Analyze this image: C:\Users\YourName\Pictures\photo.jpg
```

### Audio Analysis
In your MCP client, ask:

```
Analyze this audio: C:\Users\YourName\Music\audio.mp3
```

## 4. Custom Prompts

### Image Analysis
```
Analyze C:\Photos\sunset.jpg and describe the colors and mood
```

### Audio Analysis
```
Summarize this audio: C:\Users\YourName\Recordings\meeting.mp3
```

## Common Commands

| Task | Command |
|------|---------|
| Basic image analysis | `Analyze image: /path/to/image.jpg` |
| Basic audio analysis | `Analyze audio: /path/to/audio.mp3` |
| Custom image prompt | `Describe emotions in /path/to/photo.jpg` |
| Audio transcription | `Transcribe this audio: /path/to/audio.wav` |
| Technical analysis | Use `system_instruction_name: "technical"` |

## Next Steps

- [💡 Usage Guide](usage.md) - Detailed usage instructions and examples

---

**Issues?** Check [Troubleshooting](troubleshooting.md)
