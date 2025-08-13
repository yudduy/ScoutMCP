# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "MCP Scout" - a FastMCP-based Python server for automated MCP discovery and integration. It enables Claude Code to automatically find and install Model Context Protocol servers from the Smithery Registry based on natural language queries. The server acts as an intelligent assistant that streamlines developer workflows by automating MCP discovery and installation.

## Development Commands

- `pip install -r requirements.txt` - Install Python dependencies (fastmcp, aiohttp, pydantic)
- `python server.py` - Run the MCP Scout server in STDIO mode (default)
- `export SMITHERY_API_KEY=your_key` - Set your Smithery API key (required for operation)
- `python -m pytest tests/` - Run tests (when test suite is added)

## Architecture

### Core Components

- **SmitheryRegistryClient** (`server.py:38-96`): Python async client for Smithery Registry API
  - Manages API key authentication via Bearer token
  - Provides async methods for listing servers and getting server details
  - Uses aiohttp for HTTP requests with proper session management
  - Base64 encodes configuration for WebSocket URL generation

- **FastMCP Server** (`server.py:98-225`): Implements the Model Context Protocol server using FastMCP
  - Uses FastMCP framework for simplified MCP server creation
  - Exposes async tools with Pydantic validation
  - Runs in STDIO mode for direct Claude Code integration
  - Handles subprocess execution for MCP installation

### MCP Scout Tools

The server exposes two main tools:

1. **find_mcp** (`server.py:98-148`) - Semantic search for MCPs
   - Takes natural language query (e.g., "python linter", "web search")
   - Searches Smithery Registry using semantic search
   - Returns structured information about the best matching MCP
   - Includes name, description, install command, and metadata

2. **find_and_install_mcp** (`server.py:150-225`) - Automated MCP installation
   - Uses find_mcp to discover the best match
   - Executes `claude mcp add` command via subprocess
   - Reports installation success/failure with detailed output
   - Handles timeouts and error conditions gracefully

### Core Workflow

1. **Code Review & Recommendation**: Claude Code analyzes project and suggests MCP in natural language
2. **Discovery**: MCP Scout queries Smithery Registry for matching MCPs 
3. **Installation**: Executes installation command and reports success
4. **Feedback**: Claude Code informs user of results

### Environment Variables

- `SMITHERY_API_KEY`: Your Smithery Registry API key (required)

### Installation Pattern

- Uses Smithery's standard pattern: `claude mcp add <qualified_name> -- npx -y <qualified_name>`
- Supports timeout handling (60 seconds)
- Captures stdout/stderr for debugging
- Validates commands before execution