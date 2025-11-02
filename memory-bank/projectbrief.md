# Project Brief: Gemini Media MCP

## Project Overview
MCP (Model Context Protocol) server for analyzing multimedia content using Google Gemini AI. Built with modular architecture for easy functionality extension.

## Core Requirements
- Provide image analysis capabilities using Gemini AI
- Provide audio analysis capabilities using Gemini AI  
- Provide video analysis capabilities using Gemini AI (planned)
- Provide web search capabilities using Google Search API (planned)
- Support multiple Gemini models (Flash, Pro, Flash Lite)
- Maintain privacy by running locally with user's API key
- Follow MCP protocol standards for tool integration

## Key Features
- **Image Analysis**: AI-powered image descriptions and analysis
- **Audio Analysis**: Recognition, transcription, and analysis of audio files
- **Video Analysis**: Analysis of video files with event detection and transcription (planned)
- **Web Search**: Internet search capabilities with structured responses and sources (planned)
- **Flexible Prompts**: Custom system prompts for different analysis types
- **Multiple Models**: Support for Gemini 2.5 Flash, Pro, and Flash Lite models
- **Privacy First**: Local execution with user's API key

## Technical Scope
- Python-based MCP server using FastMCP
- Modular architecture with separate tools for different media types
- Configuration-driven approach for models and prompts
- Comprehensive error handling and logging
- Support for common image, audio, and video formats
- Integration with Google Search API for web search
- Two-phase approach for video analysis (MVP with inline_data, then File API)

## Success Criteria
- Users can analyze images and audio through MCP clients
- Support for multiple analysis types and custom prompts
- Reliable error handling and user feedback
- Clear documentation for setup and usage
- Extensible architecture for future media types
