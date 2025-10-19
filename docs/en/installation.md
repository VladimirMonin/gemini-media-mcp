# 📥 Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## Step 1: Clone Repository

```bash
git clone https://github.com/your-username/gemini-media-mcp.git
cd gemini-media-mcp
```

## Step 2: Create Virtual Environment

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Verify Installation

```bash
python server.py --help
```

If you see help information, installation was successful!

## Next Steps

- [⚙️ Configuration](configuration.md) - Set up API keys and settings
- [🚀 Quick Start](quick-start.md) - Run your first analysis

---

**Having issues?** Check [Troubleshooting](troubleshooting.md)
