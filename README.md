# MCP Scout - MCP Search Engine

A simple MCP discovery and installation engine designed to be orchestrated by Claude Code.

MCP Scout provides atomic operations for searching, installing, and managing MCPs without making assumptions about tools or workflows. All intelligence and preferences are handled by Claude Code.

## What This Does

MCP Scout is basically a search engine for MCPs (Model Context Protocol servers). Instead of trying to be smart about what you want, it just gives you raw search results from the Smithery Registry and lets you (or Claude) decide what to do with them.

## Getting Started

### What You Need

- **Python 3.10 or higher** (FastMCP requires Python 3.10+)
- A Smithery API key (grab one at [smithery.ai](https://smithery.ai))
- Claude CLI installed

First, check your Python version:
```bash
python --version  # Should show 3.10+ 
# If that doesn't work, try: python3 --version
```

### The Easy Way (Two Steps)

⚠️ **Important**: The Claude CLI doesn't remember environment variables between sessions, so you'll need to add your API key manually.

1. **Install ScoutMCP**:
```bash
claude mcp add ScoutMCP -- python /path/to/ScoutMCP/server.py
```

2. **Add your API key**:
Open your Claude config file (`~/.config/claude/claude_config.json`) and find the ScoutMCP entry. Add your API key like this:

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

3. **Restart Claude** to pick up the new config.

### Alternative Ways to Install

#### Option A: Wrapper Script (Easiest)

Create a simple script that includes your API key:

1. Create `scout_wrapper.sh`:
```bash
#!/bin/bash
export SMITHERY_API_KEY="your_smithery_api_key_here"
python /path/to/ScoutMCP/server.py
```

2. Make it runnable and install:
```bash
chmod +x scout_wrapper.sh
claude mcp add ScoutMCP -- ./scout_wrapper.sh
```

#### Option B: System Environment Variable

Add this to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
export SMITHERY_API_KEY="your_smithery_api_key_here"
```

Then restart your terminal and install normally:
```bash
claude mcp add ScoutMCP -- python /path/to/ScoutMCP/server.py
```

### Manual Installation

```bash
# Clone the repo
git clone https://github.com/your-username/mcp-scout.git
cd mcp-scout

# Install Python dependencies (make sure you're using Python 3.10+)
pip install -r requirements.txt

# Install ScoutMCP
claude mcp add ScoutMCP -- python /full/path/to/server.py

# Then manually add API key to Claude config as shown above
```

## When Things Go Wrong

### "ModuleNotFoundError: No module named 'fastmcp'"

This usually means FastMCP isn't installed or you're using the wrong Python version.

**First, check your Python version:**
```bash
python --version  # Must be 3.10+
```

**If that's not the issue, try installing with the right Python:**
```bash
# Find your Python 3.10+ installation
which python3.10  # or python3.11, python3.12, etc.

# Install dependencies with the correct Python
/path/to/python3.10 -m pip install -r requirements.txt

# Update your Claude config to use the right Python path
```

**If you have Anaconda:**
```bash
# Install with Anaconda Python
/opt/anaconda3/bin/pip install -r requirements.txt

# Update Claude config to use Anaconda Python
"command": "/opt/anaconda3/bin/python"
```

### "Failed to connect" Error

This almost always means your API key isn't set up right.

**Check your config:**
Look at your `~/.config/claude/claude_config.json` file and make sure it has:
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

**Test the server manually:**
```bash
export SMITHERY_API_KEY="your_key"
python /path/to/server.py
```
You should see the FastMCP startup screen without any errors.

**Check the server path:**
Make sure the path in your Claude config actually points to the server.py file:
```bash
ls -la /path/to/ScoutMCP/server.py  # Should exist
```

### Python Path Issues

**Find the right Python:**
```bash
# Check all Python versions on your system
ls -la /usr/bin/python*
ls -la /opt/anaconda3/bin/python*

# Test which one has fastmcp installed
/path/to/python -c "import fastmcp; print('FastMCP available')"
```

**Update your Claude config with the right path:**
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

## The Tools

### Search Tools

#### `search_registry`

Pure semantic search of the Smithery Registry. No interpretation, just raw results.

**Parameters:**
- `query` (string): Your exact search term
- `limit` (int, optional): Max results to return (default: 10)
- `filters` (dict, optional): Smithery API filters (is_deployed, is_verified, owner, etc.)

**Returns:**
- Raw search results from Smithery with status and results array

#### `get_mcp_info`

Get the full details about a specific MCP.

**Parameters:**
- `qualified_name` (string): The exact MCP identifier

**Returns:**
- Complete MCP details including connections and deployment info

### Installation Tools

#### `install_mcp`

Install a single MCP.

**Parameters:**
- `qualified_name` (string): MCP to install
- `install_command` (string, optional): Override the install command
- `timeout_seconds` (int, optional): How long to wait for installation (default: 60)

**Returns:**
- Installation status and output

#### `verify_installation`

Check if an MCP is properly installed and working.

**Parameters:**
- `qualified_name` (string): MCP to verify

**Returns:**
- Verification status and config path

### Management Tools

#### `list_installed`

Show all the MCPs currently installed in your Claude config.

**Returns:**
- List of installed MCPs with their configurations

#### `uninstall_mcp`

Remove an MCP from your Claude configuration.

**Parameters:**
- `qualified_name` (string): MCP to remove

**Returns:**
- Removal status

### Old Tools (Don't Use These)

#### `setup_mcp` ⚠️ DEPRECATED

Simple wrapper around the atomic tools. Use `search_registry`, `install_mcp`, `verify_installation` instead.

#### `discover_mcps` ⚠️ DEPRECATED

Old discovery tool. Use `search_registry` for direct semantic search instead.

## How to Use It

### Basic Workflow

#### 1. **Search for MCPs**

```python
# Simple search
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
    
    # Install it
    install_mcp(qualified_name)
    
    # Make sure it worked
    verify_installation(qualified_name)
```

#### 3. **Manage Your MCPs**

```python
# See what's installed
list_installed()

# Remove something you don't want
uninstall_mcp("some-mcp-name")
```

### Real-World Examples

#### Example 1: Finding Testing Tools for a React Project

```python
# Step 1: Claude Code figures out what to search for based on what you asked
user_request = "I need testing tools for my React TypeScript project"

# Step 2: Search with specific queries
search_results = []
for query in ["react testing", "typescript test", "component testing"]:
    result = search_registry(query, limit=3)
    search_results.append(result)

# Step 3: Claude Code looks at the results and shows you options
# Step 4: You pick what you want
# Step 5: Claude Code installs it for you
install_mcp("selected-mcp-qualified-name")
```

#### Example 2: Finding Database Tools

```python
# Claude Code understands what you need and searches appropriately
queries = [
    "postgresql client",
    "database management", 
    "sql tools"
]

for query in queries:
    results = search_registry(query, limit=2, filters={"is_verified": True})
    # Claude Code processes the results and makes recommendations
```

### Search by Concept, Not Just Names

Instead of looking for specific tool names, search for what you want to do:

- **"code quality"** → Finds linters, formatters, static analysis tools
- **"web scraping"** → Finds web crawling and data extraction tools  
- **"file operations"** → Finds file system and file manipulation tools
- **"api testing"** → Finds HTTP clients, API testing frameworks
- **"data processing"** → Finds ETL, analytics, and data transformation tools

### Handling Errors

```python
# Search with error handling
result = search_registry("nonexistent tool")
if result["status"] == "error":
    print(f"Search failed: {result['message']}")
    # Claude Code can try different search terms

# Installation with error handling  
install_result = install_mcp("some-mcp")
if install_result["status"] == "error":
    error_code = install_result["error_code"]
    if error_code == "INSTALL_TIMEOUT":
        # Try again with more time
        install_mcp("some-mcp", timeout_seconds=120)
```

### Moving from the Old Tools

```python
# Old way (don't use this anymore)
setup_mcp(query="python linter")  # This will give you a deprecation warning

# New way (use this instead)
results = search_registry("python linter", limit=3)
# Claude Code looks at the options and your preferences
install_mcp(selected_qualified_name)
verify_installation(selected_qualified_name)
```

## Working with Claude Code

For the best experience with Claude Code and getting good MCP recommendations, check out the complete prompt guide in [PROMPT.md](PROMPT.md).

## License

MIT
