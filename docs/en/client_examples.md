# MCP Client Configuration Examples

This document provides examples of how to configure different MCP clients to use the Gemini Media MCP server.

## Claude Desktop (`servers_config.json`)

To configure the Claude Desktop client, you need to add the following to your `servers_config.json` file. This file is usually located in `~/.claude/servers_config.json`.

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "python",
      "args": ["-m", "server"],
      "env": {
        "GEMINI_API_KEY": "sk-your-actual-key-here"
      }
    }
  }
}
```

Replace `"sk-your-actual-key-here"` with your actual Gemini API key.

## Manual Installation

You can also install the server manually by cloning the repository and configuring your MCP client directly.

### Step 1: Clone and Install

```bash
git clone https://github.com/VladimirMonin/gemini-media-mcp.git
cd gemini-media-mcp
pip install -r requirements.txt
```

### Step 2: Configure MCP Client

Configure your MCP client to use the server with the API key:

```json
{
  "mcpServers": {
    "gemini-media-analyzer": {
      "command": "python",
      "args": ["-m", "server"],
      "env": {
        "GEMINI_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

### Step 3: Test the Server

You can test the server manually:

```bash
python server.py
```

However, for regular use, you should let your MCP client manage the server lifecycle.
