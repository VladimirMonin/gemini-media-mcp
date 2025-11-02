# Product Context: Gemini Media MCP

## Why This Project Exists
The project addresses the need for local, privacy-focused multimedia analysis using state-of-the-art AI models. Users want to analyze images and audio files without sending data to external services, maintaining full control over their data.

## Problems Solved
- **Privacy Concerns**: Users can analyze media locally without data leaving their machine
- **Accessibility**: Provides AI-powered descriptions for images, transcriptions for audio, and analysis for video
- **Information Access**: Enables web search capabilities for up-to-date information
- **Flexibility**: Supports multiple analysis types and custom prompts
- **Integration**: Works seamlessly with MCP-compatible clients like Claude Desktop and Cursor

## How It Should Work
1. Users configure the server with their Gemini API key
2. MCP clients can access image, audio, video analysis, and web search tools
3. Users provide media files, search queries, or analysis requests
4. Server processes requests using Gemini AI models and Google Search API
5. Structured responses are returned to the client with sources and metadata

## User Experience Goals
- **Simple Setup**: Easy configuration with environment variables
- **Reliable Analysis**: Consistent, high-quality media analysis
- **Clear Documentation**: Comprehensive guides for setup and usage
- **Error Handling**: Helpful error messages and troubleshooting guidance
- **Extensibility**: Easy to add new media types and analysis capabilities

## Target Users
- **Developers**: Integrating media analysis into applications
- **Content Creators**: Analyzing images and audio for accessibility
- **Researchers**: Processing multimedia data with AI assistance
- **Accessibility Professionals**: Generating alt-text and transcriptions

## Key Value Propositions
- **Privacy-First**: Local processing with user's API key
- **Multi-Modal**: Support for images, audio, video analysis, and web search
- **Model Choice**: Multiple Gemini models for different use cases
- **Open Standards**: Built on MCP protocol for broad compatibility
- **Extensible**: Modular architecture for future enhancements
- **Comprehensive Analysis**: Rich structured responses with events, transcriptions, and sources
