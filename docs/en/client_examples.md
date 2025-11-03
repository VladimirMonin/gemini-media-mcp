# Cline Client Configuration Example

This document provides configuration examples for the Cline client. Other MCP clients may have different configuration formats.

## Cline Client

To configure the Cline client, add the following configuration to your Cline settings. Replace `project_full_path` with the absolute path to your project directory.

### Windows Configuration

```json
{
  "gemini-media-mcp": {
    "autoApprove": ["analyze_image", "analyze_audio"],
    "disabled": false,
    "timeout": 300,
    "type": "stdio",
    "command": "project_full_path/venv/Scripts/python.exe",
    "args": ["project_full_path/server.py"],
    "env": {
      "GEMINI_API_KEY": "your_api_key",
      "PYTHONIOENCODING": "utf-8",
      "PYTHONUTF8": "1"
    }
  }
}
```

### macOS/Linux Configuration

```json
{
  "gemini-media-mcp": {
    "autoApprove": ["analyze_image", "analyze_audio"],
    "disabled": false,
    "timeout": 300,
    "type": "stdio",
    "command": "project_full_path/venv/bin/python",
    "args": ["project_full_path/server.py"],
    "env": {
      "GEMINI_API_KEY": "your_api_key",
      "PYTHONIOENCODING": "utf-8",
      "PYTHONUTF8": "1"
    }
  }
}
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
