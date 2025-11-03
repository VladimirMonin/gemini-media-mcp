# ⚙️ Configuration

## API Key Setup

### Step 1: Get Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the generated key

### Step 2: Configure Environment

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env` and add your key:

```env
GEMINI_API_KEY="your_actual_api_key_here"
```

## MCP Client Configuration

See [Client Configuration Examples](client_examples.md) for detailed setup instructions for various MCP clients, including Cline.

## Model Configuration

You can change the default model by editing the `config.py` file. The default is `gemini-2.5-flash-lite` for its balance of speed and performance.

```python
# In config.py
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"  # Fast and efficient (Default)
# DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"      # Balanced performance
# DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"        # Highest quality
```

You can also override the model for a specific request. See the [Usage Guide](usage.md) for details.

## Next Steps

- [🚀 Quick Start](quick-start.md) - Run your first analysis
- [💡 Usage Guide](usage.md) - Learn how to use the tool

---

**Need help?** See [Common Issues](common-issues.md)
