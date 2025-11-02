# Technical Context: Gemini Media MCP

## Technology Stack

### Core Technologies

- **Python 3.8+**: Primary programming language
- **FastMCP**: MCP server framework
- **Google Gemini API**: AI model provider
- **Pydantic**: Data validation and serialization
- **python-dotenv**: Environment variable management

### Dependencies (requirements.txt)

- `mcp` - Model Context Protocol framework
- `google-generativeai` - Gemini API client
- `pydantic` - Data validation
- `python-dotenv` - Environment variables
- `mimetypes` - File type detection

## Development Setup

### Environment Requirements

- Python 3.8 or higher
- Google Gemini API key
- Virtual environment recommended

### Installation Steps

```bash
# Clone repository
git clone https://github.com/VladimirMonin/gemini-media-mcp.git
cd gemini-media-mcp

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional - can also use CLI installer)
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Or use CLI installer for automatic setup
python scripts/install_server.py
```

### Running the Server

```bash
python server.py
```

## Configuration

### Environment Variables

- `GEMINI_API_KEY` (required): Google Gemini API key
- Default model configuration in config.py

### Supported Models

- `gemini-2.5-flash-lite` - Default, fast and efficient
- `gemini-2.5-flash` - Balanced performance
- `gemini-2.5-pro` - Highest quality

### File Format Support

#### Images

- JPEG, PNG, GIF, WEBP, HEIC, HEIF
- Maximum file size: 20 MB

#### Audio

- MP3, WAV, AIFF, AAC, OGG, FLAC
- Maximum file size: 19.5 MB

#### Video (planned)
- Support for common video formats
- Two-phase approach: MVP with inline_data (≤20MB), then File API (up to 2GB)
- Structured response with events, transcription, and file_uri for reuse

#### Web Search (planned)
- Internet search using Google Search API
- Structured responses with sources and search queries
- Integration with Gemini API for search grounding

## Project Structure

```
gemini-media-mcp/
├── server.py              # Main MCP server
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── docs/                 # Documentation (en/ and ru/)
├── memory-bank/          # Project memory bank
├── models/               # Pydantic models
│   ├── __init__.py
│   └── analysis.py       # Response models
├── tools/                # Analysis tools
│   ├── __init__.py
│   ├── image_analyzer.py # Image analysis tool
│   └── audio_analyzer.py # Audio analysis tool
└── utils/                # Shared utilities
    ├── __init__.py
    ├── gemini_client.py  # Gemini API client
    ├── file_utils.py     # File handling utilities
    └── logger.py         # Logging configuration
```

## Tool Usage Patterns

### Image Analysis

```python
analyze_image(
    image_path: str,
    user_prompt: str = "",
    model_name: Optional[str] = None,
    system_instruction_name: str = "default",
    system_instruction_override: Optional[str] = None,
    system_instruction_file_path: Optional[str] = None
)
```

### Audio Analysis

```python
analyze_audio(
    audio_path: str,
    user_prompt: str,
    analysis_type: str = "summary",
    model_name: Optional[str] = None,
    output_path: Optional[str] = None
)
```

## Development Workflow

### Testing

- Test files in tests/ directory
- Manual testing with MCP clients
- Error scenario testing

### Documentation

- Bilingual documentation (English and Russian)
- Comprehensive usage examples
- Troubleshooting guides
- Memory bank for project context

### Deployment

- Local MCP server deployment
- Compatible with Claude Desktop, Cursor, etc.
- No external dependencies beyond Gemini API

## Technical Constraints

### API Limitations

- Gemini API rate limits apply
- File size limits enforced
- Supported formats limited by Gemini API

### Platform Support

- Windows, Linux, macOS
- Python 3.8+ required
- MCP client compatibility required

### Security Considerations

- API keys stored locally
- No data sent to external services beyond Gemini
- File validation before processing
