# Cline Client Configuration Example

This document provides configuration examples for the Cline client. Other MCP clients may have different configuration formats.

## Configuration File Location

**macOS/Linux:**

```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

**Windows:**

```
%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

## Cline Client Configuration

To configure the Cline client, add the following configuration to your `cline_mcp_settings.json` file. Replace paths with the absolute path to your project directory.

### macOS Configuration Example

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "/Users/username/Documents/gemini-media-mcp/.venv/bin/python",
      "args": [
        "/Users/username/Documents/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines",
        "get_audio_generation_guide"
      ],
      "timeout": 600
    }
  }
}
```

**Real-world example (macOS):**

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "/Users/john/Documents/py/gemini-media-mcp/.venv/bin/python",
      "args": [
        "/Users/john/Documents/py/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "AIzaSyD1234567890abcdefghijklmnopqrstuvw"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines"
      ],
      "timeout": 600
    }
  }
}
```

**How to find your paths (macOS):**

```bash
# Navigate to your project
cd ~/Documents/gemini-media-mcp

# Get Python path
echo "$(pwd)/.venv/bin/python"

# Get server.py path
echo "$(pwd)/server.py"
```

### Windows Configuration Example

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "C:\\Users\\username\\Documents\\gemini-media-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\username\\Documents\\gemini-media-mcp\\server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines",
        "get_audio_generation_guide"
      ],
      "timeout": 600
    }
  }
}
```

**Real-world example (Windows):**

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "C:\\Projects\\gemini-media-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Projects\\gemini-media-mcp\\server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "AIzaSyD1234567890abcdefghijklmnopqrstuvw",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines"
      ],
      "timeout": 600
    }
  }
}
```

**How to find your paths (Windows PowerShell):**

```powershell
# Navigate to your project
cd C:\Projects\gemini-media-mcp

# Get Python path
Write-Host "$PWD\.venv\Scripts\python.exe"

# Get server.py path
Write-Host "$PWD\server.py"
```

### Linux Configuration Example

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "/home/username/projects/gemini-media-mcp/.venv/bin/python",
      "args": [
        "/home/username/projects/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines"
      ],
      "timeout": 600
    }
  }
}
```

## Configuration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | string | **Full path** to Python interpreter in virtual environment |
| `args` | array | Path to `server.py` file |
| `env.GEMINI_API_KEY` | string | Your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `autoApprove` | array | Tools that don't require manual approval (see warning below) |
| `timeout` | number | Maximum execution time in seconds (default: 600 for media processing) |

## Platform-Specific Notes

### macOS/Linux

- Python binary location: `.venv/bin/python`
- Use forward slashes `/` in paths
- Paths are case-sensitive

### Windows

- Python binary location: `.venv\Scripts\python.exe`
- Use double backslashes `\\` in JSON paths
- Add encoding environment variables for Unicode support

## Testing Your Configuration

After adding the configuration:

1. **Reload VS Code window:**
   - Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Reload Window" and press Enter

2. **Check server registration:**
   - Open Cline chat
   - Look for "gemini-media-analyzer" in available MCP servers
   - You should see 7 registered tools:
     - `analyze_image`
     - `analyze_gif`
     - `analyze_audio`
     - `generate_image`
     - `generate_audio_from_yaml`
     - `get_gif_guidelines`
     - `get_audio_generation_guide`

3. **Test manually (optional):**

**macOS/Linux:**

```bash
cd /path/to/gemini-media-mcp
source .venv/bin/activate
python server.py
```

**Windows:**

```powershell
cd C:\path\to\gemini-media-mcp
.venv\Scripts\Activate.ps1
python server.py
```

You should see:

```
Tool 'analyze_image' registered successfully.
Tool 'analyze_audio' registered successfully.
Tool 'generate_image' registered successfully.
Tool 'generate_audio_from_yaml' registered successfully.
Tool 'get_audio_generation_guide' registered successfully.
Tool 'analyze_gif' registered successfully.
Tool 'get_gif_guidelines' registered successfully.
```

## ⚠️ Important Security and Cost Warnings

### Auto-Approval Warning

**NEVER enable auto-approval for tools unless you are 100% confident in what you're doing or are using the free tier exclusively.**

The `autoApprove` setting allows tools to run without explicit user confirmation. This can be dangerous for paid tools or tools that may incur costs. Only use auto-approval if you fully understand the implications and are using free-tier features.

### Image Generation Costs

**Image generation (`generate_image` tool) is a paid feature with no free tier.**

- Current cost: approximately $0.04 per image
- This feature uses Google's paid image generation API
- Be aware of potential costs before using this tool extensively
- Consider setting up usage limits or monitoring your API usage
