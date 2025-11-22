# MCP Client Configuration Examples

This document provides configuration examples for MCP clients including Cline, VS Code Native, and Qwen CLI. Other MCP clients may have different configuration formats.

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
| `args` | array | Path to `server.py` file (include `-u` flag for unbuffered output) |
| `env.GEMINI_API_KEY` | string | Your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `autoApprove` | array | Tools that don't require manual approval (see warning below) |
| `timeout` | number | **CRITICAL:** Maximum execution time. **Seconds** for VS Code/Cline (600 = 10 min), **Milliseconds** for Qwen CLI (120000 = 2 min) |

## Timeout Configuration by Client

| Client | Unit | Example Value | Real Time |
|--------|------|---------------|-----------|
| **Cline** | Seconds | 600 | 10 minutes |
| **VS Code Native** | Seconds | 600 | 10 minutes |
| **Qwen CLI** | **Milliseconds** | 120000 | 2 minutes |

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
   - You should see 8 registered tools:
     - `analyze_image`
     - `analyze_gif`
     - `analyze_audio`
     - `analyze_video`
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
Tool 'analyze_video' registered successfully.
Tool 'generate_image' registered successfully.
Tool 'generate_audio_from_yaml' registered successfully.
Tool 'get_audio_generation_guide' registered successfully.
Tool 'analyze_gif' registered successfully.
Tool 'get_gif_guidelines' registered successfully.
```

## Qwen CLI Configuration

Qwen CLI is a Node.js-based MCP client that requires special attention to timeout configuration.

### Configuration File Location

Create or edit `.qwen/settings.json` in your project root or `~/.qwen/settings.json` globally.

### ⚠️ CRITICAL: Timeout Configuration

**Qwen CLI uses milliseconds for timeouts, NOT seconds!**

This is different from VS Code and Cline (which use seconds). If you use a small number like 600, Qwen will wait only 0.6 seconds and report that the tool was not found.

**Recommended timeout: 120000 milliseconds = 2 minutes**

### Qwen CLI Configuration Example (Windows)

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "C:/Projects/gemini-media-mcp/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/Projects/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1"
      },
      "autoApprove": [
        "analyze_image",
        "analyze_audio",
        "get_gif_guidelines",
        "get_audio_generation_guide"
      ],
      "disabled": false,
      "type": "stdio",
      "timeout": 120000
    }
  }
}
```

### Important Qwen CLI Notes

1. **Always use forward slashes `/` in paths**, even on Windows (e.g., `C:/Projects/...` not `C:\Projects\...`)
2. **Timeout is in milliseconds**: 120000 = 120,000 milliseconds = 2 minutes
3. **Include `-u` argument** and `PYTHONUNBUFFERED` environment variable for proper output buffering
4. **Add `type: "stdio"`** field for Qwen CLI compatibility

### Why such a large timeout?

Python servers with ML libraries (NumPy, Pillow, etc.) can take significant time to start. A 2-minute timeout ensures the server has enough time to initialize properly, especially on the first run.

## VS Code Native MCP Support

VS Code has built-in MCP support that appears in the sidebar or integrates with Copilot.

### Configuration File Location

**Windows:** `%APPDATA%\Code\User\profiles\{Profile_ID}\mcp.json` (or in main User folder for single profile)
**macOS/Linux:** `~/Library/Application Support/Code/User/profiles/{Profile_ID}/mcp.json`

### VS Code Native Configuration Example (Windows)

```json
{
  "servers": {
    "gemini-media-analyzer": {
      "command": "C:/Projects/gemini-media-mcp/.venv/Scripts/python.exe",
      "args": [
        "-u",
        "C:/Projects/gemini-media-mcp/server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1"
      },
      "autoApprove": [],
      "disabled": false,
      "timeout": 600
    }
  },
  "$version": 1
}
```

### VS Code Native Notes

1. **Root object is `"servers"`**, not `"mcpServers"` (different from Cline/Qwen)
2. **Timeout is in seconds**: 600 = 10 minutes
3. **Requires window reload** after configuration changes
4. **Strict JSON validation** - make sure the structure is exactly correct

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
