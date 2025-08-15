# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "MCP Scout" - a simple, reliable MCP search and installation engine designed to be orchestrated by Claude Code. It provides atomic operations for discovering and managing MCPs without making assumptions about tools or workflows. All intelligence and preferences are handled by Claude Code in the conversation context.

## Quick Setup

**One-line installation:**
```bash
SMITHERY_API_KEY="your_api_key" claude mcp add ScoutMCP -- python /Users/duy/Documents/build/ScoutMCP/server.py
```

## Development Commands

- `pip install -r requirements.txt` - Install Python dependencies (fastmcp, aiohttp, pydantic)
- `python server.py` - Run the MCP Scout server in STDIO mode (default)
- `export SMITHERY_API_KEY=your_key` - Set your Smithery API key (required for operation)

## Architecture

### Core Philosophy
MCP Scout follows the principle of **separation of concerns**:
- **MCP Scout**: Pure search and installation engine (no opinions)
- **Claude Code**: Intelligence, orchestration, and user preferences

### Components

- **SmitheryRegistryClient** (`server.py:55-116`): Python async client for Smithery Registry API
  - Manages API key authentication via Bearer token
  - Provides async methods for listing servers and getting server details
  - Uses aiohttp for HTTP requests with proper session management

- **FastMCP Server** (`server.py:25`): Implements the Model Context Protocol server using FastMCP
  - Uses FastMCP framework for simplified MCP server creation
  - Exposes atomic tools with Pydantic validation
  - Runs in STDIO mode for direct Claude Code integration

### Atomic Tools

The server exposes 6 simple, single-purpose tools:

#### Search Tools
1. **search_registry** - Pure semantic search of Smithery Registry
   - Takes explicit query string, limit, and optional filters
   - Returns raw search results with no interpretation
   - Supports Smithery filters (is_deployed, is_verified, owner)

2. **get_mcp_info** - Get detailed information about a specific MCP
   - Takes qualified_name parameter
   - Returns complete MCP details from Smithery

#### Installation Tools  
3. **install_mcp** - Install a single MCP
   - Takes qualified_name and optional install_command override
   - Uses subprocess with proper security (list args, not shell)
   - Returns installation status and output

4. **verify_installation** - Check if an MCP is properly installed
   - Takes qualified_name parameter
   - Checks Claude configuration file
   - Returns verification status

#### Management Tools
5. **list_installed** - List all installed MCPs from Claude config
   - No parameters required
   - Returns list of installed MCPs with configurations

6. **uninstall_mcp** - Remove an MCP from Claude configuration
   - Takes qualified_name parameter
   - Safely removes from config file

#### Legacy Tools (Deprecated)
- **setup_mcp** ⚠️ DEPRECATED - Wrapper around atomic tools with deprecation warnings
- **discover_mcps** ⚠️ DEPRECATED - Legacy discovery with deprecation warnings

### Workflow

1. **Claude Code Orchestration**: Claude Code analyzes user request and generates specific search queries
2. **Pure Search**: MCP Scout executes searches without interpretation using `search_registry`
3. **User Choice**: Claude Code presents options and user selects preferred MCP
4. **Atomic Installation**: MCP Scout installs specific MCP using `install_mcp`
5. **Verification**: Optional verification using `verify_installation`

### Data Models

Simple, explicit models for clear API contracts:

- **SearchRequest**: query, limit, filters
- **MCPInfo**: qualified_name, display_name, description, install_command, etc.
- **InstallRequest**: qualified_name, install_command, timeout_seconds

### Environment Variables

- `SMITHERY_API_KEY`: Your Smithery Registry API key (required)

### Usage Patterns for Claude Code

#### Recommended Workflow
1. **Analyze user request** and generate specific search terms
2. **Use `search_registry`** with concept-based queries (not tool names)
3. **Present multiple options** to user with explanations
4. **Let user choose** their preferred tool
5. **Use `install_mcp`** to install the selected MCP
6. **Optionally verify** using `verify_installation`

#### Example Claude Code Integration
```python
# Instead of: "install eslint" (opinionated)
# Do: Search for concept and let user choose
search_results = search_registry("code quality tools", limit=5)
# Present options: eslint, biome, oxlint, etc.
# User picks their preference
install_mcp(user_selected_qualified_name)
```

#### Key Principles
- **No assumptions**: Don't assume user wants specific tools (ESLint vs Biome)
- **Multiple options**: Present alternatives, let user decide
- **Concept-based search**: Use "testing" not "jest", use "formatting" not "prettier"
- **Explicit installation**: Always use qualified_name from search results

### Migration from Legacy System

Old approach (deprecated):
```python
setup_mcp(analysis=complex_project_analysis)
```

New approach (recommended):
```python
# Claude Code orchestrates the workflow
queries = generate_queries_from_user_request(user_input)
for query in queries:
    results = search_registry(query, limit=3)
    # Evaluate and present options to user
# User selects preferred MCP
install_mcp(selected_qualified_name)
```

### Installation Pattern

- Uses secure subprocess execution: `["claude", "mcp", "add", name, "--"] + cmd.split()`
- Supports timeout handling (60 seconds default, configurable)
- Captures stdout/stderr for debugging
- Returns structured error codes for programmatic handling