# MCP Scout - Automated MCP Discovery and Integration

A FastMCP-based Python server that automates the discovery and installation of Model Context Protocol (MCP) servers using the Smithery Registry API.

MCP Scout enables Claude Code to recommend MCPs based on project analysis, semantically search for matches using natural language queries, and automatically install them via system commands, streamlining developer workflows.

## Features

- **Semantic Search**: Find MCP servers using natural language queries (e.g., "python linter", "web search")
- **Automated Installation**: Automatically install discovered MCPs using `claude mcp add` commands
- **Intelligent Matching**: Select the best MCP from search results based on relevance
- **Error Handling**: Comprehensive error handling for API failures and installation issues
- **FastMCP Integration**: Built with FastMCP for seamless Claude Code integration

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-scout.git
cd mcp-scout

# Install Python dependencies
pip install -r requirements.txt

# Set your Smithery API key
export SMITHERY_API_KEY=your_smithery_api_key
```

### Prerequisites

- Python 3.8+
- Smithery API key (get one at [smithery.ai](https://smithery.ai))
- Claude CLI installed (`claude mcp add` commands)

## Usage

### Start the Server

**STDIO Mode** (default, for use with Claude Code):
```bash
python server.py
```

### Integration with Claude Code

Add MCP Scout to your Claude Code configuration:

```json
{
  "mcpServers": {
    "mcp-scout": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/mcp-scout/server.py"],
      "env": {
        "SMITHERY_API_KEY": "your_smithery_api_key"
      }
    }
  }
}
```

### Environment Variables

- `SMITHERY_API_KEY`: Your Smithery Registry API key (required)

## MCP Scout Tools

### `find_mcp`

Finds the best-matching MCP server using semantic search.

**Parameters:**
- `query` (string): Natural language description of desired MCP functionality
  - Examples: "python linter", "web search", "database query", "code formatter"

**Returns:**
- MCP information including name, description, install command, and metadata
- Error message if no matches found or API call fails

### `find_and_install_mcp`

Finds and automatically installs the best-matching MCP server.

**Parameters:**
- `query` (string): Natural language description of desired MCP functionality

**Returns:**
- Installation status (success/error)
- MCP information and installation details  
- Error details if installation fails

## Examples

### Core Workflow

1. **Claude Code analyzes your project and recommends an MCP:**
```
"This Python project needs a linter for code quality."
```

2. **Find suitable MCP:**
```python
find_mcp("python linter")
```
Returns information about Ruff or similar Python linting MCPs.

3. **Install the MCP automatically:**
```python
find_and_install_mcp("python linter")
```
Executes: `claude mcp add ruff-mcp -- npx -y @modelcontextprotocol/server-ruff`

4. **Restart your terminal and use the new MCP**

### Example Usage Scenarios

- **"Add a web search capability"** → Finds and installs Brave Search MCP
- **"Need database query tools"** → Finds and installs SQLite or PostgreSQL MCP  
- **"Add code formatting"** → Finds and installs Prettier or Black formatter MCP
- **"Need file system operations"** → Finds and installs filesystem MCP

## License

MIT
