// smithery-registry-mcp
//
// An MCP server that interfaces with the Smithery Registry API
// Allows AI agents to search for MCP servers, get server details,
// and create connection URLs as described in llms.txt

import { z } from 'zod';
import { createServer } from '@modelcontextprotocol/server';
import fetch from 'node-fetch';

// Types
type ServerListItem = {
  qualifiedName: string;
  displayName: string;
  description: string;
  homepage: string;
  useCount: string;
  isDeployed: boolean;
  createdAt: string;
};

type ServerList = {
  servers: ServerListItem[];
  pagination: {
    currentPage: number;
    pageSize: number;
    totalPages: number;
    totalCount: number;
  };
};

type Connection = {
  type: string;
  url?: string;
  configSchema: Record<string, any>;
};

type ServerDetails = {
  qualifiedName: string;
  displayName: string;
  deploymentUrl: string;
  connections: Connection[];
};

// Constants
const REGISTRY_API_BASE = 'https://registry.smithery.ai';

// API Client for Smithery Registry
class SmitheryRegistryClient {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  // Helper method to make authenticated requests
  private async request<T>(url: string, options: any = {}): Promise<T> {
    const headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json() as Promise<T>;
  }

  // Get a list of servers with optional filtering
  async listServers(
    query?: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<ServerList> {
    const url = new URL(`${REGISTRY_API_BASE}/servers`);
    
    if (query) {
      url.searchParams.append('q', query);
    }
    
    url.searchParams.append('page', page.toString());
    url.searchParams.append('pageSize', pageSize.toString());
    
    return this.request<ServerList>(url.toString());
  }

  // Get details for a specific server
  async getServer(qualifiedName: string): Promise<ServerDetails> {
    const url = `${REGISTRY_API_BASE}/servers/${qualifiedName}`;
    return this.request<ServerDetails>(url);
  }

  // Create a websocket URL with the proper config encoding
  createWebSocketUrl(qualifiedName: string, config: Record<string, any>): string {
    const base64Config = Buffer.from(JSON.stringify(config)).toString('base64');
    return `https://server.smithery.ai/${qualifiedName}/ws?config=${base64Config}`;
  }
}

// Create the MCP Server
async function main() {
  // Initialize the server
  const registry = createServer({
    name: 'smithery-registry',
    description: 'MCP server for interacting with the Smithery Registry API',
    version: '1.0.0',
  });

  // Type definitions for tool parameters and returns
  const listServersSchema = z.object({
    query: z.string().optional().describe('Search query (semantic search)'),
    page: z.number().default(1).describe('Page number for pagination (default: 1)'),
    pageSize: z.number().default(10).describe('Number of items per page (default: 10)'),
  });

  const getServerSchema = z.object({
    qualifiedName: z.string().describe('The qualified name of the server to get details for'),
  });

  const createConnectionUrlSchema = z.object({
    qualifiedName: z.string().describe('The qualified name of the server'),
    config: z.record(z.any()).describe('Configuration object matching the server\'s schema'),
  });

  // Handle authentication with the API key
  registry.methods.add('authenticate', {
    description: 'Set up authentication with your Smithery API key',
    parameters: z.object({
      apiKey: z.string().describe('Your Smithery API key'),
    }),
    handler: ({ apiKey }) => {
      // Store the API key for subsequent requests
      registry.state.set('apiKey', apiKey);
      return { success: true, message: 'Authentication successful' };
    },
  });

  // Register tools
  registry.methods.add('listServers', {
    description: 'Search and retrieve a list of servers from the Smithery Registry',
    parameters: listServersSchema,
    handler: async ({ query, page, pageSize }) => {
      const apiKey = registry.state.get('apiKey');
      if (!apiKey) {
        throw new Error('Authentication required. Call authenticate() first.');
      }

      const client = new SmitheryRegistryClient(apiKey);
      return await client.listServers(query, page, pageSize);
    },
  });

  registry.methods.add('getServer', {
    description: 'Get detailed information about a specific server by its qualified name',
    parameters: getServerSchema,
    handler: async ({ qualifiedName }) => {
      const apiKey = registry.state.get('apiKey');
      if (!apiKey) {
        throw new Error('Authentication required. Call authenticate() first.');
      }

      const client = new SmitheryRegistryClient(apiKey);
      return await client.getServer(qualifiedName);
    },
  });

  registry.methods.add('createConnectionUrl', {
    description: 'Create a WebSocket connection URL for a server with the provided configuration',
    parameters: createConnectionUrlSchema,
    handler: async ({ qualifiedName, config }) => {
      const apiKey = registry.state.get('apiKey');
      if (!apiKey) {
        throw new Error('Authentication required. Call authenticate() first.');
      }

      const client = new SmitheryRegistryClient(apiKey);
      
      // Optionally verify the server exists and get its config schema
      const serverDetails = await client.getServer(qualifiedName);
      
      // Could add validation here that config matches schema
      
      const wsUrl = client.createWebSocketUrl(qualifiedName, config);
      return { url: wsUrl };
    },
  });

  // Start the server
  const port = process.env.PORT ? parseInt(process.env.PORT) : 3000;
  
  // Different start options based on environment
  if (process.env.USE_SSE === 'true') {
    // Start using Server-Sent Events (SSE)
    await registry.listen.sse({
      port,
      host: process.env.HOST || 'localhost',
      endpoint: process.env.ENDPOINT || '/sse',
    });
    console.log(`Smithery Registry MCP server running in SSE mode on port ${port}`);
  } else {
    // Start using standard STDIO
    await registry.listen.stdio();
    console.log('Smithery Registry MCP server running in STDIO mode');
  }
}

// Run the server
main().catch((error) => {
  console.error('Error starting server:', error);
  process.exit(1);
});
