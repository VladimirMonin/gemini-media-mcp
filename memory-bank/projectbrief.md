# Project Brief: Gemini Media MCP

## Project Overview
MCP (Model Context Protocol) server for analyzing multimedia content using Google Gemini AI. Built with modular architecture for easy functionality extension.

## Core Requirements
- Provide image analysis capabilities using Gemini AI
- Provide audio analysis capabilities using Gemini AI  
- Support multiple Gemini models (Flash, Pro, Flash Lite)
- Maintain privacy by running locally with user's API key
- Follow MCP protocol standards for tool integration

## Key Features
- **Image Analysis**: AI-powered image descriptions and analysis
- **Audio Analysis**: Recognition, transcription, and analysis of audio files
- **Flexible Prompts**: Custom system prompts for different analysis types
- **Multiple Models**: Support for Gemini 2.5 Flash, Pro, and Flash Lite models
- **Privacy First**: Local execution with user's API key

## Technical Scope
- Python-based MCP server using FastMCP
- Modular architecture with separate tools for different media types
- Configuration-driven approach for models and prompts
- Comprehensive error handling and logging
- Support for common image and audio formats

## Success Criteria
- Users can analyze images and audio through MCP clients
- Support for multiple analysis types and custom prompts
- Reliable error handling and user feedback
- Clear documentation for setup and usage
- Extensible architecture for future media types
