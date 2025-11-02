# Installation Guide

There are two primary methods for installing the Gemini Media MCP server.

## Method 1: Using the Installer Script (Recommended)

This is the simplest method and is recommended for most users.

### Step 1: Install the Package

First, install the package along with the necessary CLI dependencies. From the root of the project directory, run:

```bash
pip install .[cli]
```

### Step 2: Run the Installer

Next, run the installer script and provide your Gemini API key. This will automatically configure your MCP client.

```bash
install-gemini-mcp --gemini-api-key "your_gemini_api_key"
```

Replace `"your_gemini_api_key"` with your actual Gemini API key.

That's it! The server is now configured and ready to be used by your MCP client.

## Method 2: Manual Installation

This method is for advanced users or for development purposes.

### Step 1: Clone the Repository

```bash
git clone https://github.com/VladimirMonin/gemini-media-mcp.git
cd gemini-media-mcp
```

### Step 2: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 3: Configure Your MCP Client

You need to configure your MCP client to launch the server and pass the `GEMINI_API_KEY` as an environment variable.

See the [Client Configuration Examples](client_examples.md) for detailed instructions for different clients.

### Step 4: Run the Server Manually

You can run the server directly for testing purposes:

```bash
python server.py
```

However, for regular use, you should let your MCP client manage the server lifecycle.
