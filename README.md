# Smithery Registry MCP Server

An MCP server that interfaces with the Smithery Registry API, allowing AI agents to search for MCP servers, get server details, and create connection URLs.

This server implements the functionality described in [llms.txt](https://smithery.ai/docs/registry/llms.txt), providing a programmatic way to search and obtain launch configurations for Model Context Protocol (MCP) servers.

## Features

- **Search for Servers**: Find MCP servers using semantic search or specific filters
- **Get Server Details**: Retrieve detailed information about specific servers
- **Create Connection URLs**: Generate correctly formatted WebSocket URLs with encoded configurations

## Installation

```bash
# Clone the repository
git clone https://github.com/aloshy-ai/smithery-registry-mcp.git
cd smithery-registry-mcp

# Install dependencies
npm install

# Build the project
npm run build
```

## Usage

### Start the Server

You can run the server in two modes:

**STDIO Mode** (default, for use with LLM clients):
```bash
npm start
```

**SSE Mode** (for web applications):
```bash
npm run sse
```

### Environment Variables

- `PORT`: The port to listen on when running in SSE mode (default: 3000)
- `HOST`: The host to bind to when running in SSE mode (default: localhost)
- `ENDPOINT`: The endpoint path for SSE connections (default: /sse)
- `USE_SSE`: Set to "true" to run in SSE mode instead of STDIO mode

### Using the Server with Smithery CLI

```bash
# Install the server using Smithery CLI
npx @smithery/cli install @aloshy-ai/smithery-registry-mcp

# Use with various clients
npx @smithery/cli run @aloshy-ai/smithery-registry-mcp --client claude
```

## API Tools

### `authenticate`

Set up authentication with your Smithery API key.

Parameters:
- `apiKey`: Your Smithery API key

### `listServers`

Search and retrieve a list of servers from the Smithery Registry.

Parameters:
- `query` (optional): Search query (semantic search)
- `page` (optional, default: 1): Page number for pagination
- `pageSize` (optional, default: 10): Number of items per page

### `getServer`

Get detailed information about a specific server by its qualified name.

Parameters:
- `qualifiedName`: The qualified name of the server to get details for

### `createConnectionUrl`

Create a WebSocket connection URL for a server with the provided configuration.

Parameters:
- `qualifiedName`: The qualified name of the server
- `config`: Configuration object matching the server's schema

## Examples

Here's how you might use this server with an AI assistant:

1. First authenticate with your API key:
```
authenticate({ apiKey: "your-smithery-api-key" })
```

2. Search for servers related to a topic:
```
listServers({ query: "web search capabilities" })
```

3. Get detailed information about a specific server:
```
getServer({ qualifiedName: "brave-search" })
```

4. Create a connection URL with the appropriate configuration:
```
createConnectionUrl({
  qualifiedName: "brave-search",
  config: { apiKey: "your-brave-api-key" }
})
```

## License

MIT
