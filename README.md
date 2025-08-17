# MCP Scout - Pure MCP Search Engine

A simple, reliable MCP discovery and installation engine designed to be orchestrated by Claude Code.

MCP Scout provides atomic operations for searching, installing, and managing MCPs without making assumptions about tools or workflows. All intelligence and preferences are handled by Claude Code.

## Philosophy

- **No Opinions**: We don't choose tools for you
- **Pure Search**: Direct Smithery Registry access  
- **Atomic Operations**: Each tool does one thing well
- **Claude Orchestrated**: Intelligence lives in Claude Code conversation context

## Features

- **Pure Semantic Search**: Direct Smithery Registry search with no interpretation
- **Atomic Operations**: Single-purpose tools for search, install, verify, list, remove
- **Explicit Parameters**: No guessing or hidden assumptions
- **Structured Errors**: Clear error codes for programmatic handling
- **FastMCP Integration**: Built with FastMCP for seamless Claude Code integration

## Installation

### Prerequisites

- **Python 3.10 or higher** (FastMCP requires Python 3.10+)
- Smithery API key (get one at [smithery.ai](https://smithery.ai))
- Claude CLI installed

Check your Python version:
```bash
python --version  # Should show 3.10+ 
# If not, try: python3 --version
```

### Recommended Installation (Two Steps)

⚠️ **Important**: The Claude CLI doesn't persist environment variables, so API keys must be added manually.

1. **Install ScoutMCP**:
```bash
claude mcp add ScoutMCP -- python /path/to/ScoutMCP/server.py
```

2. **Add API key manually**:
Edit your Claude config file (`~/.config/claude/claude_config.json`) and find the ScoutMCP entry. Update it to include the API key:

```json
{
  "mcpServers": {
    "ScoutMCP": {
      "type": "stdio",
      "command": "python", 
      "args": ["/path/to/ScoutMCP/server.py"],
      "env": {
        "SMITHERY_API_KEY": "your_smithery_api_key_here"
      }
    }
  }
}
```

3. **Restart Claude** to load the new configuration.

### Alternative Installation Methods

#### Option A: Wrapper Script (Recommended for simplicity)

Create a wrapper script that includes the API key:

1. Create `scout_wrapper.sh`:
```bash
#!/bin/bash
export SMITHERY_API_KEY="your_smithery_api_key_here"
python /path/to/ScoutMCP/server.py
```

2. Make it executable and install:
```bash
chmod +x scout_wrapper.sh
claude mcp add ScoutMCP -- ./scout_wrapper.sh
```

#### Option B: System Environment Variable

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export SMITHERY_API_KEY="your_smithery_api_key_here"
```

Then restart your terminal and install normally:
```bash
claude mcp add ScoutMCP -- python /path/to/ScoutMCP/server.py
```

### Manual Installation (Alternative)

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-scout.git
cd mcp-scout

# Install Python dependencies (make sure you're using Python 3.10+)
pip install -r requirements.txt

# Install ScoutMCP
claude mcp add ScoutMCP -- python /full/path/to/server.py

# Then manually add API key to Claude config as shown above
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastmcp'"

This means FastMCP isn't installed or you're using the wrong Python version.

**Fix 1: Check Python version**
```bash
python --version  # Must be 3.10+
```

**Fix 2: Install with correct Python**
```bash
# Find your Python 3.10+ installation
which python3.10  # or python3.11, python3.12, etc.

# Install dependencies with correct Python
/path/to/python3.10 -m pip install -r requirements.txt

# Update Claude config to use correct Python path
```

**Fix 3: Use Anaconda/Conda if available**
```bash
# If you have Anaconda
/opt/anaconda3/bin/pip install -r requirements.txt

# Update Claude config to use Anaconda Python
"command": "/opt/anaconda3/bin/python"
```

### "Failed to connect" Error

This usually means the API key isn't properly configured.

**Fix 1: Verify API key in config**
Check your `~/.config/claude/claude_config.json` file has:
```json
{
  "mcpServers": {
    "ScoutMCP": {
      "env": {
        "SMITHERY_API_KEY": "your_actual_key_here"
      }
    }
  }
}
```

**Fix 2: Test server manually**
```bash
export SMITHERY_API_KEY="your_key"
python /path/to/server.py
```
Should show FastMCP startup screen without errors.

**Fix 3: Check server path**
Ensure the path in your Claude config points to the actual server.py file:
```bash
ls -la /path/to/ScoutMCP/server.py  # Should exist
```

### Python Path Issues

**Find correct Python path:**
```bash
# Check all Python versions
ls -la /usr/bin/python*
ls -la /opt/anaconda3/bin/python*

# Test which one has fastmcp
/path/to/python -c "import fastmcp; print('FastMCP available')"
```

**Update Claude config with correct path:**
```json
{
  "mcpServers": {
    "ScoutMCP": {
      "command": "/correct/path/to/python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

### Environment Variables

- `SMITHERY_API_KEY`: Your Smithery Registry API key (required)

## MCP Scout Tools

### Search Tools

#### `search_registry`

Pure semantic search of Smithery Registry.

**Parameters:**
- `query` (string): Exact search term (no interpretation)
- `limit` (int, optional): Maximum results to return (default: 10)
- `filters` (dict, optional): Smithery API filters (is_deployed, is_verified, owner, etc.)

**Returns:**
- Raw search results from Smithery with status and results array

#### `get_mcp_info`

Get detailed information about a specific MCP.

**Parameters:**
- `qualified_name` (string): Exact MCP identifier

**Returns:**
- Complete MCP details including connections and deployment info

### Installation Tools

#### `install_mcp`

Install a single MCP.

**Parameters:**
- `qualified_name` (string): MCP to install
- `install_command` (string, optional): Override for install command
- `timeout_seconds` (int, optional): Installation timeout (default: 60)

**Returns:**
- Installation status and output

#### `verify_installation`

Check if an MCP is properly installed.

**Parameters:**
- `qualified_name` (string): MCP to verify

**Returns:**
- Verification status and config path

### Management Tools

#### `list_installed`

List all installed MCPs from Claude config.

**Returns:**
- List of installed MCPs with their configurations

#### `uninstall_mcp`

Remove an MCP from Claude configuration.

**Parameters:**
- `qualified_name` (string): MCP to remove

**Returns:**
- Removal status

### Legacy Tools (Deprecated)

#### `setup_mcp` ⚠️ DEPRECATED

Simple wrapper around atomic tools. Use `search_registry`, `install_mcp`, `verify_installation` instead.

#### `discover_mcps` ⚠️ DEPRECATED

Legacy discovery tool. Use `search_registry` for direct semantic search instead.

## Examples

### Basic Atomic Operations

#### 1. **Search for MCPs**

```python
# Basic search
search_registry("testing tools")

# Search with filters
search_registry("database", filters={"is_deployed": True})

# Specific search
search_registry("react development")
```

#### 2. **Install an MCP**

```python
# Search first
results = search_registry("python linter", limit=1)
if results["status"] == "success" and results["results"]:
    qualified_name = results["results"][0]["qualified_name"]
    
    # Install the MCP
    install_mcp(qualified_name)
    
    # Verify installation
    verify_installation(qualified_name)
```

#### 3. **Manage Installed MCPs**

```python
# List all installed MCPs
list_installed()

# Remove an MCP
uninstall_mcp("some-mcp-name")
```

### Claude Code Orchestration Examples

#### Example 1: Find Testing Tools for React Project

```python
# Step 1: Claude Code generates search queries based on user request
user_request = "I need testing tools for my React TypeScript project"

# Step 2: Claude Code searches with specific queries
search_results = []
for query in ["react testing", "typescript test", "component testing"]:
    result = search_registry(query, limit=3)
    search_results.append(result)

# Step 3: Claude Code evaluates results and presents options to user
# Step 4: User selects preferred tool
# Step 5: Claude Code installs selected MCP
install_mcp("selected-mcp-qualified-name")
```

#### Example 2: Database Tools Discovery

```python
# Claude Code understands user needs and searches appropriately
queries = [
    "postgresql client",
    "database management", 
    "sql tools"
]

for query in queries:
    results = search_registry(query, limit=2, filters={"is_verified": True})
    # Claude Code processes results and makes recommendations
```

### Concept-Based Search Examples

Instead of hard-coded tool names, use concepts:

- **"code quality"** → Finds linters, formatters, static analysis tools
- **"web scraping"** → Finds web crawling and data extraction tools  
- **"file operations"** → Finds file system and file manipulation tools
- **"api testing"** → Finds HTTP clients, API testing frameworks
- **"data processing"** → Finds ETL, analytics, and data transformation tools

### Error Handling Examples

```python
# Search with error handling
result = search_registry("nonexistent tool")
if result["status"] == "error":
    print(f"Search failed: {result['message']}")
    # Claude Code can retry with different terms

# Installation with error handling  
install_result = install_mcp("some-mcp")
if install_result["status"] == "error":
    error_code = install_result["error_code"]
    if error_code == "INSTALL_TIMEOUT":
        # Retry with longer timeout
        install_mcp("some-mcp", timeout_seconds=120)
```

### Migration from Legacy Tools

```python
# Old approach (deprecated)
setup_mcp(query="python linter")  # Returns deprecation warning

# New approach (recommended)
results = search_registry("python linter", limit=3)
# Claude Code evaluates options and user preferences
install_mcp(selected_qualified_name)
verify_installation(selected_qualified_name)
```

## Claude Code Integration

For optimal Claude Code integration and MCP recommendations, see the complete prompt guide in [PROMPT.md](PROMPT.md).

## License

MIT
