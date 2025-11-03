# Active Context: Gemini Media MCP

## Current Work Focus
The project has recently been enhanced with new audio analysis capabilities and updated to support the latest Gemini models, including the new Flash Lite model. Documentation has been comprehensively updated to reflect these new features.

Two major new features are now planned for implementation:
- **Video Analysis**: Two-phase approach for analyzing video files (MVP with inline_data, then File API)
- **Web Search**: Internet search capabilities using Google Search API through Gemini

## Recent Changes

### Image Generation Feature (November 2025)
- **Task #5**: ✅ Completed - Implementation of image generation via Gemini API
- **Image Generation Tool**: Added `tools/image_generator.py` with text-to-image and text+image(s)-to-image capabilities
- **Supported Models**: `gemini-2.5-flash-image-preview` for image generation
- **Response Structure**: Returns absolute path to generated image file
- **Integration**: Seamlessly integrated into existing MCP server architecture

### New Audio Analysis Feature (October 2025)
- **Audio Analysis Tool**: Added `tools/audio_analyzer.py` with comprehensive audio processing
- **Supported Formats**: MP3, WAV, AIFF, AAC, OGG, FLAC
- **Analysis Types**: summary, transcription, detailed
- **Response Structure**: Rich audio analysis with title, summary, transcription, participants, hashtags, and action items

### Model Updates
- **New Default Model**: `gemini-2.5-flash-lite` - Fast and efficient
- **Updated Model List**: Now includes Flash, Pro, and Flash Lite variants
- **Model Configuration**: Enhanced config.py with latest model support

### Documentation Overhaul
- **README.MD**: Updated features list and future plans
- **Usage Guides**: Added comprehensive audio analysis sections
- **Quick Start**: Enhanced with audio analysis examples
- **Bilingual Support**: Both English and Russian documentation updated
- **Link Fixes**: Corrected documentation links to point to existing files

### Memory Bank Creation
- Complete memory bank established with all core files
- Detailed technical documentation of new capabilities
- Project context and patterns documented

## Current Status

### ✅ Completed Features
- Image analysis with multiple models and prompts
- Audio analysis with comprehensive response structure
- Multi-language documentation (English and Russian)
- Complete memory bank with project context
- Error handling and validation
- MCP protocol compliance
- **Flexible API Key Management**: New architecture for secure key transmission via client configuration
- **Image Generation**: Text-to-image and text+image(s)-to-image capabilities

### 🔄 Recently Implemented
- **Task #5**: Image generation tool with text-to-image and text+image(s)-to-image capabilities
- Audio analysis tool with multiple analysis types
- Support for Gemini 2.5 Flash Lite model
- Updated configuration with latest models
- Comprehensive documentation updates
- Memory bank creation and population
- **Cross-platform fix**: Resolved macOS server crash by fixing log path creation in `utils/logger.py`
- **Task #2**: Implemented proper API key transmission architecture for local MCP servers
- **Image Generation Debugging**: Resolved text+image(s)-to-image functionality issues

### 📋 Next Steps
- **Task #3**: Implement video analysis with two-phase approach (MVP + File API)
- **Task #4**: Implement web search capabilities using Google Search API
- Monitor user feedback on new audio analysis and image generation
- Consider adding more analysis types for existing media
- **Completed**: Task #1 - Fixed macOS server crash (closed)
- **Completed**: Task #2 - Implemented proper API key transmission (closed)
- **Completed**: Task #5 - Implemented image generation capabilities (closed)

## Active Decisions and Considerations

### Model Selection Strategy
- **Flash Lite as Default**: Chosen for speed and efficiency in most use cases
- **Model Override Support**: Users can specify different models per request
- **Future Model Updates**: Architecture supports easy model additions

### Audio Analysis Design
- **Structured Responses**: Rich JSON responses for programmatic use
- **Multiple Analysis Types**: Summary, transcription, and detailed analysis
- **File Validation**: Comprehensive format and size checking

### Documentation Approach
- **Bilingual Support**: Maintain both English and Russian documentation
- **Real Examples**: Provide practical usage examples
- **Memory Bank**: Ensure project continuity and knowledge retention

## Important Patterns and Preferences

### Code Organization
- Modular tool architecture for easy extension
- Shared utilities for common functionality
- Consistent error handling patterns
- Configuration-driven approach

### Documentation Standards
- Clear, practical examples
- Bilingual content where appropriate
- Regular updates with new features
- Memory bank for project continuity

### Development Workflow
- Feature development with documentation updates
- Memory bank maintenance
- Regular project context reviews

## Learnings and Project Insights

### Successful Patterns
- Modular tool architecture allows easy feature additions
- Structured response models improve client integration
- Bilingual documentation increases accessibility
- Memory bank ensures project continuity

### Technical Insights
- Gemini Flash Lite provides excellent performance for most use cases
- Audio analysis complements image analysis well
- MCP protocol enables broad client compatibility
- Configuration-driven approach simplifies maintenance
- **Image Generation**: Text+image(s)-to-image requires absolute paths for reference images
- **API Limits**: Free tier quotas can cause 429 errors that appear as functional issues

### User Experience Focus
- Clear error messages improve troubleshooting
- Comprehensive examples accelerate adoption
- Flexible model selection meets diverse needs
- Privacy-first approach builds trust
- **Absolute Paths**: Critical requirement for file operations in MCP tools
- **Documentation Clarity**: Explicit path requirements prevent user confusion

### Recent Investigation Insights (November 2025)
- **Image Generation Debugging**: Text+image(s)-to-image functionality was working correctly
- **Root Cause**: API rate limits (429 RESOURCE_EXHAUSTED) were mistaken for code issues
- **Solution**: Code cleanup and documentation improvements
- **Key Finding**: All file paths in MCP tools must be absolute paths
- **Documentation**: Updated to explicitly state absolute path requirements
