# System Patterns: Gemini Media MCP

## Architecture Overview
The system follows a modular MCP server architecture with separate tools for different media types, built on FastMCP framework.

## Core Components

### Server Structure
- **server.py**: Main MCP server entry point
- **config.py**: Configuration management with environment variables
- **models/**: Pydantic models for structured responses
- **tools/**: Individual analysis tools (image_analyzer.py, audio_analyzer.py, video_analyzer.py, web_search.py)
- **utils/**: Shared utilities (gemini_client.py, file_utils.py, logger.py)

### Tool Registration Pattern
```python
# Tools are imported and registered in server.py
from tools.image_analyzer import analyze_image
from tools.audio_analyzer import analyze_audio

mcp.tool()(analyze_image)
mcp.tool()(analyze_audio)
```

## Key Technical Decisions

### Media Analysis Architecture
- **Separation of Concerns**: Each media type has its own analyzer tool
- **Shared Gemini Client**: Common client for all Gemini API interactions
- **Structured Responses**: Pydantic models ensure consistent response formats
- **Error Handling**: Comprehensive error responses with details

### Configuration Management
- Environment variables for sensitive data (API keys)
- Default configuration values in config.py
- Support for multiple Gemini models
- File format and size validation
- **Flexible API Key Loading**: Priority-based key loading from environment variables
- **CLI Installation Tools**: Automated server setup with environment configuration

## New Audio Analysis Capabilities

### Audio Analysis Tool (tools/audio_analyzer.py)
- **Supported Formats**: MP3, WAV, AIFF, AAC, OGG, FLAC
- **Analysis Types**: summary, transcription, detailed
- **Response Structure**: Title, summary, transcription, participants, hashtags, action_items
- **File Size Limit**: 19.5 MB maximum

### Audio Analysis Response Model
```python
class AudioAnalysisResponse(BaseModel):
    title: Optional[str] = Field(default=None, description="Suggested title for the audio.")
    summary: Optional[str] = Field(default=None, description="Brief summary of the audio content.")
    transcription: Optional[str] = Field(default=None, description="Full transcription of the audio.")
    participants: Optional[list[str]] = Field(default=None, description="List of identified participants.")
    hashtags: Optional[list[str]] = Field(default=None, description="Keywords or topics as hashtags.")
    action_items: Optional[list[str]] = Field(default=None, description="List of action items mentioned.")
    raw_text: str = Field(..., description="Raw text response from the model.")
```

## Model Support

### Available Gemini Models
- `gemini-2.5-flash-lite` - Fast and efficient (default)
- `gemini-2.5-flash` - Balanced performance  
- `gemini-2.5-pro` - Highest quality

### Model Selection
- Configurable via environment variables
- Override per request in tool parameters
- Default model: gemini-2.5-flash-lite

## Error Handling Patterns

### Structured Error Responses
```python
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error description.")
    details: Optional[str] = Field(default=None, description="Additional error details.")
    raw_response: Optional[str] = Field(default=None, description="Raw model response if format mismatch occurred.")
```

### Common Error Scenarios
- File not found
- Unsupported file format
- File size exceeded
- API errors from Gemini
- JSON parsing failures

## Extension Patterns

### Adding New Media Types
1. Create new tool in tools/ directory
2. Define response model in models/analysis.py
3. Register tool in server.py
4. Update configuration if needed
5. Add documentation

### Configuration Extensions
- Add new environment variables to config.py
- Update validation logic
- Provide default values
- Document new options
