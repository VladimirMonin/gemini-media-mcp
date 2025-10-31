# 📝 Common Issues & Solutions

## Installation Problems

### Issue: pip install fails with SSL error

**Symptoms:**

```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Issue: Python version too old

**Symptoms:**

```
ERROR: Python 3.7 is not supported
```

**Solution:**

- Install Python 3.8 or higher
- Check version: `python --version`

## Configuration Problems

### Issue: API key not recognized

**Symptoms:**

```
Error: GEMINI_API_KEY environment variable not set
```

**Solution:**

1. Check `.env` file format (no spaces):

   ```
   GEMINI_API_KEY="AIza..."
   ```

2. Verify file encoding is UTF-8
3. Restart terminal after editing

### Issue: MCP client config not working

**Symptoms:**

- Server doesn't appear in client
- Connection timeout

**Solution:**

1. Verify JSON syntax (use [jsonlint.com](https://jsonlint.com))
2. Check paths use forward slashes or escaped backslashes:

   ```json
   "command": "C:/Python38/python.exe"
   ```

3. Restart client application completely

## Runtime Problems

### Issue: "Image encoding failed"

**Symptoms:**

```
Error encoding image to base64
```

**Solution:**

1. Check image is not corrupted
2. Try opening in image viewer
3. Convert to standard format (JPEG/PNG)

### Issue: Analysis returns empty response

**Symptoms:**

- No error but the response is empty or lacks detail.

**Solution:**

1. Try a more specific or different prompt.
2. Check the quality of the media file (e.g., not too blurry or noisy).
3. Switch to a more powerful model like `gemini-2.5-pro` for complex tasks.

### Issue: Slow analysis performance

**Symptoms:**

- Takes >30 seconds per image

**Solution:**

1. Use `gemini-2.5-flash` for speed
2. Reduce image size before analysis
3. Check network connection

## Windows-Specific Issues

### Issue: PowerShell script execution disabled

**Symptoms:**

```
cannot be loaded because running scripts is disabled
```

**Solution:**

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Issue: Path contains spaces

**Symptoms:**

- Config file errors with paths

**Solution:**
Use quotes in JSON:

```json
"args": ["C:/Program Files/Python/server.py"]
```

## Getting Diagnostic Information

Run diagnostic script:

```bash
python -c "import sys; print(f'Python: {sys.version}'); from config import GEMINI_API_KEY; print('API Key:', 'Set' if GEMINI_API_KEY else 'Missing')"
```

---

**Still need help?**

- [Troubleshooting Guide](troubleshooting.md)
- [GitHub Issues](https://github.com/VladimirMonin/gemini-media-mcp/issues)
