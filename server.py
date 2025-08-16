#!/usr/bin/env python3
"""
MCP Scout - Atomic MCP Discovery and Management Server

A FastMCP-based server that provides atomic operations for discovering, installing,
and managing Model Context Protocol (MCP) servers using the Smithery Registry API.

This server follows the principle of separation of concerns:
- MCP Scout: Pure search and installation engine (no opinions)
- Claude Code: Intelligence, orchestration, and user preferences

Author: MCP Scout Team
Version: 2.0
"""

import base64
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

import aiohttp
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Initialize the FastMCP server
mcp = FastMCP("MCP Scout")

# Constants
REGISTRY_API_BASE = "https://registry.smithery.ai"
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_PAGE_SIZE = 10


class ServerListItem(BaseModel):
    """
    Represents a single MCP server item from the Smithery Registry list response.
    
    This model matches the actual API response structure from the Smithery Registry.
    """
    qualifiedName: str = Field(description="Unique identifier for the MCP server")
    displayName: str = Field(description="Human-readable name for display")
    description: str = Field(description="Description of the server's functionality")
    homepage: str = Field(description="URL to the server's homepage or repository")
    useCount: int = Field(description="Number of times this server has been used")
    isDeployed: Optional[bool] = Field(
        default=None, 
        description="Whether the server is deployed and available"
    )
    createdAt: str = Field(description="ISO timestamp of when the server was created")


class ServerList(BaseModel):
    """
    Represents the complete response from the Smithery Registry list servers endpoint.
    """
    servers: List[ServerListItem] = Field(description="List of MCP servers")
    pagination: Dict[str, Any] = Field(description="Pagination metadata")


class Connection(BaseModel):
    """
    Represents a connection configuration for an MCP server.
    """
    type: str = Field(description="Type of connection (e.g., 'websocket', 'stdio')")
    url: Optional[str] = Field(default=None, description="Connection URL if applicable")
    configSchema: Dict[str, Any] = Field(description="Configuration schema for the connection")


class SecurityInfo(BaseModel):
    """
    Represents security scan information for an MCP server.
    """
    scanPassed: bool = Field(description="Whether the server has passed security scanning")


class ToolInfo(BaseModel):
    """
    Represents a tool provided by an MCP server.
    """
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of what the tool does")
    inputSchema: Dict[str, Any] = Field(description="JSON schema for tool input")


class ServerDetails(BaseModel):
    """
    Represents detailed information about a specific MCP server.
    """
    qualifiedName: str = Field(description="Unique identifier for the MCP server")
    displayName: str = Field(description="Human-readable name for display")
    description: Optional[str] = Field(default=None, description="Description of the server's functionality")
    iconUrl: Optional[str] = Field(default=None, description="URL to the server's icon")
    remote: Optional[bool] = Field(default=None, description="Whether the server is deployed remotely")
    deploymentUrl: Optional[str] = Field(default=None, description="URL where the server is deployed")
    connections: List[Connection] = Field(description="Available connection configurations")
    security: Optional[SecurityInfo] = Field(default=None, description="Security scan information")
    tools: Optional[List[ToolInfo]] = Field(default=None, description="List of tools provided by the server")


class SmitheryRegistryClient:
    """
    Asynchronous HTTP client for interacting with the Smithery Registry API.
    
    This client provides methods for searching and retrieving MCP server information
    from the Smithery Registry, handling authentication and proper session management.
    
    Usage:
        async with SmitheryRegistryClient(api_key) as client:
            servers = await client.list_servers(query="database")
            details = await client.get_server("example/postgres-mcp")
    """
    
    def __init__(self, api_key: str) -> None:
        """
        Initialize the Smithery Registry client.
        
        Args:
            api_key: Authentication token for the Smithery Registry API
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> 'SmitheryRegistryClient':
        """
        Async context manager entry - creates the HTTP session with authentication headers.
        
        Returns:
            Self for use in the async context
        """
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        """
        Async context manager exit - properly closes the HTTP session.
        
        Args:
            _exc_type: Exception type (if any) - unused but required by context manager protocol
            _exc_val: Exception value (if any) - unused but required by context manager protocol
            _exc_tb: Exception traceback (if any) - unused but required by context manager protocol
        """
        if self.session:
            await self.session.close()
    
    async def _request(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Make an authenticated HTTP GET request to the Smithery Registry API.
        
        Args:
            url: The complete URL to request
            **kwargs: Additional arguments to pass to aiohttp.get()
        
        Returns:
            Parsed JSON response as a dictionary
        
        Raises:
            RuntimeError: If the client session is not initialized
            Exception: If the API request fails with detailed error information
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        async with self.session.get(url, **kwargs) as response:
            if response.status != 200:
                error_text = await response.text()
                # Enhanced error reporting for debugging
                params_info = f"URL: {url}"
                if 'params' in kwargs:
                    params_info += f", Params: {kwargs['params']}"
                raise Exception(
                    f"API request failed: {response.status} {response.reason} - {error_text}. {params_info}"
                )
            
            return await response.json()
    
    async def list_servers(
        self, 
        query: Optional[str] = None, 
        page: int = 1, 
        pageSize: int = DEFAULT_PAGE_SIZE
    ) -> ServerList:
        """
        Retrieve a paginated list of MCP servers from the registry.
        
        Args:
            query: Optional search query to filter servers by name or description
            page: Page number for pagination (1-based)
            pageSize: Number of servers to return per page
        
        Returns:
            ServerList containing matching servers and pagination metadata
        
        Raises:
            Exception: If the API request fails
        """
        url = f"{REGISTRY_API_BASE}/servers"
        params = {
            "page": str(page),
            "pageSize": str(pageSize)
        }
        
        if query:
            params["q"] = query
        
        data = await self._request(url, params=params)
        return ServerList(**data)
    
    async def get_server(self, qualified_name: str) -> ServerDetails:
        """
        Retrieve detailed information about a specific MCP server.
        
        Args:
            qualified_name: The unique identifier of the server (e.g., "example/postgres-mcp")
        
        Returns:
            ServerDetails containing comprehensive server information
        
        Raises:
            Exception: If the API request fails or server is not found
        """
        url = f"{REGISTRY_API_BASE}/servers/{qualified_name}"
        data = await self._request(url)
        return ServerDetails(**data)
    
    def create_websocket_url(self, qualified_name: str, config: Dict[str, Any]) -> str:
        """
        Generate a WebSocket URL for connecting to a deployed MCP server.
        
        Args:
            qualified_name: The unique identifier of the server
            config: Configuration parameters to encode in the URL
        
        Returns:
            Complete WebSocket URL with base64-encoded configuration
        """
        config_json = json.dumps(config)
        base64_config = base64.b64encode(config_json.encode()).decode()
        return f"https://server.smithery.ai/{qualified_name}/ws?config={base64_config}"


def get_api_key() -> Optional[str]:
    """
    Retrieve the Smithery API key from environment variables or Claude configuration.
    
    This function first checks the SMITHERY_API_KEY environment variable, then falls
    back to searching for the key in the Claude configuration file.
    
    Returns:
        API key string if found, None otherwise
    """
    # First try environment variable
    api_key = os.getenv('SMITHERY_API_KEY')
    if api_key:
        return api_key
    
    # Fallback: try to read from Claude config file
    try:
        config_path = Path.home() / ".config" / "claude" / "claude_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Look for ScoutMCP config with env.SMITHERY_API_KEY
            mcp_servers = config.get("mcpServers", {})
            for server_config in mcp_servers.values():
                env_vars = server_config.get("env", {})
                if "SMITHERY_API_KEY" in env_vars:
                    return env_vars["SMITHERY_API_KEY"]
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        pass  # Silent fallback failure
    
    return None


async def get_installed_mcps() -> Dict[str, Any]:
    """
    Read Claude configuration files to get a list of currently installed MCPs.
    
    Checks both local project config (.claude.json) and global config 
    (.config/claude/claude_config.json), with local config taking precedence.
    
    Returns:
        Dictionary containing installation status and list of installed MCPs
    """
    # Check local project config first (takes precedence)
    # Try current directory first, then home directory
    local_config_path = Path.cwd() / ".claude.json"
    home_config_path = Path.home() / ".claude.json"
    global_config_path = Path.home() / ".config" / "claude" / "claude_config.json"
    
    all_mcps = {}
    config_sources = []
    
    # Try to read local project config first (current directory)
    if local_config_path.exists():
        try:
            with open(local_config_path, 'r', encoding='utf-8') as f:
                local_config = json.load(f)
            
            local_mcps = local_config.get("mcpServers", {})
            if local_mcps:
                all_mcps.update(local_mcps)
                config_sources.append(f"local_project: {local_config_path}")
        except (json.JSONDecodeError, PermissionError):
            pass  # Continue to home config if local fails
    
    # Try to read home directory config (user-specific with project configs)
    if home_config_path.exists():
        try:
            with open(home_config_path, 'r', encoding='utf-8') as f:
                home_config = json.load(f)
            
            # Check for direct mcpServers (root level)
            home_mcps = home_config.get("mcpServers", {})
            if home_mcps:
                # Add home MCPs that aren't already in local config
                for name, details in home_mcps.items():
                    if name not in all_mcps:
                        all_mcps[name] = details
                config_sources.append(f"local_home: {home_config_path}")
            
            # Check for project-specific MCPs
            projects = home_config.get("projects", {})
            current_dir = str(Path.cwd())
            
            # First, check current project directory
            if current_dir in projects:
                project_mcps = projects[current_dir].get("mcpServers", {})
                if project_mcps:
                    for name, details in project_mcps.items():
                        if name not in all_mcps:
                            all_mcps[name] = details
                    config_sources.append(f"project_current: {current_dir}")
            
            # Then check all other projects for additional MCPs
            for project_path, project_config in projects.items():
                if project_path != current_dir:  # Skip current dir as we already checked it
                    project_mcps = project_config.get("mcpServers", {})
                    if project_mcps:
                        for name, details in project_mcps.items():
                            if name not in all_mcps:
                                all_mcps[name] = details
                        config_sources.append(f"project_other: {project_path}")
                        
        except (json.JSONDecodeError, PermissionError):
            pass  # Continue to global config if home fails
    
    # Try to read global config
    if global_config_path.exists():
        try:
            with open(global_config_path, 'r', encoding='utf-8') as f:
                global_config = json.load(f)
            
            global_mcps = global_config.get("mcpServers", {})
            if global_mcps:
                # Add global MCPs that aren't already in local config
                for name, details in global_mcps.items():
                    if name not in all_mcps:
                        all_mcps[name] = details
                config_sources.append(f"global: {global_config_path}")
        except (json.JSONDecodeError, PermissionError):
            pass  # Continue even if global config fails
    
    # If no configs found or readable
    if not config_sources:
        return {
            "status": "error",
            "error_code": "CONFIG_NOT_FOUND",
            "message": "No Claude configuration found",
            "checked_paths": [str(local_config_path), str(home_config_path), str(global_config_path)]
        }
    
    # Build installed MCPs list
    installed = []
    for name, details in all_mcps.items():
        installed.append({
            "name": name,
            "command": details.get("command", ""),
            "args": details.get("args", []),
            "env": details.get("env", {})
        })
    
    return {
        "status": "success",
        "installed_mcps": installed,
        "total": len(installed),
        "config_sources": config_sources,
        "checked_paths": [str(local_config_path), str(home_config_path), str(global_config_path)]
    }


# Native Capability Exclusion Framework
# Prevents recommending MCPs that duplicate Claude's native capabilities

WEB_HTTP_EXCLUSIONS = [
    "web search", "http client", "api testing", "web scraping basic",
    "url fetch", "web request", "http request", "api client basic",
    "fetch web content", "search the web", "make http requests",
    "web api calls", "download web pages", "browse websites",
    "http get post", "rest api client", "web content retrieval"
]

FILE_SYSTEM_EXCLUSIONS = [
    "file system", "file operations", "file management", "directory listing",
    "file reading", "file writing", "text editing", "file search",
    "read files", "write files", "edit files", "list directories",
    "find files", "file manipulation", "text file processing",
    "file glob patterns", "directory traversal", "file tree"
]

DEVELOPMENT_EXCLUSIONS = [
    "code analysis", "syntax highlighting", "basic testing", "git operations",
    "terminal tools", "shell commands", "documentation access",
    "analyze code", "read documentation", "run commands", "execute scripts",
    "git commands", "terminal access", "shell scripting", "code review basic"
]

TEXT_DATA_EXCLUSIONS = [
    "json processing", "csv basic", "text manipulation", "string operations",
    "markdown processing", "yaml parsing", "xml parsing basic",
    "parse json", "read csv", "process text", "manipulate strings",
    "convert markdown", "yaml files", "xml documents", "text formatting"
]

ALL_EXCLUSIONS = (
    WEB_HTTP_EXCLUSIONS + 
    FILE_SYSTEM_EXCLUSIONS + 
    DEVELOPMENT_EXCLUSIONS + 
    TEXT_DATA_EXCLUSIONS
)


def should_exclude_search_query(query: str) -> bool:
    """
    Determine if a search query would return mostly redundant results.
    
    This function checks if the query targets capabilities that Claude already
    has natively available, helping to filter out redundant MCP recommendations.
    
    Args:
        query: The search query to evaluate
    
    Returns:
        True if the query should be filtered out, False otherwise
    """
    query_lower = query.lower()
    
    for exclusion_term in ALL_EXCLUSIONS:
        if exclusion_term in query_lower:
            return True
    
    return False


def is_redundant_mcp(result: Dict[str, Any]) -> bool:
    """
    Check if an MCP result duplicates Claude's native capabilities.
    
    Args:
        result: Dictionary containing MCP information with 'description' and 'display_name' keys
    
    Returns:
        True if the MCP duplicates native capabilities, False otherwise
    """
    description = result.get('description', '').lower()
    name = result.get('display_name', '').lower()
    
    for exclusion_term in ALL_EXCLUSIONS:
        if exclusion_term in description or exclusion_term in name:
            return True
    
    return False


def filter_redundant_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out MCPs that duplicate Claude's native capabilities.
    
    Args:
        results: List of MCP search results
    
    Returns:
        Filtered list with redundant MCPs removed
    """
    return [result for result in results if not is_redundant_mcp(result)]


def suggest_alternatives_for_excluded_query(query: str) -> List[str]:
    """
    When a query is excluded, suggest better alternative search terms.
    
    This function analyzes the excluded query and suggests more specific
    alternatives that would find useful MCPs without duplicating native capabilities.
    
    Args:
        query: The excluded search query
    
    Returns:
        List of suggested alternative search terms
    """
    query_lower = query.lower()
    suggestions = []
    
    # Web/HTTP → Service integrations
    if any(term in query_lower for term in ["web", "http", "api"]):
        suggestions.extend([
            "github api client", "stripe payments", "slack integration",
            "aws services", "google cloud api", "supabase database"
        ])
    
    # File operations → Specialized processing
    if any(term in query_lower for term in ["file", "document", "text"]):
        suggestions.extend([
            "pdf manipulation", "image processing", "excel advanced",
            "email templates", "document generation"
        ])
    
    # Generic development → Database tools
    if any(term in query_lower for term in ["development", "tools", "utility"]):
        suggestions.extend([
            "postgresql client", "mongodb tools", "redis client",
            "database schema", "orm tools"
        ])
    
    return suggestions[:3]  # Return top 3 suggestions


# Atomic MCP Tools - Simple, Explicit Operations

@mcp.tool
async def search_registry(
    query: str, 
    limit: int = 10,
    filters: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Perform a semantic search of the Smithery Registry with intelligent filtering.
    
    This tool searches for MCP servers that match the given query while automatically
    filtering out results that would duplicate Claude's native capabilities.
    
    Args:
        query: Search term describing the desired MCP functionality
        limit: Maximum number of results to return (default: 10)
        filters: Optional Smithery API filters as Python dict or JSON string:
                - is_deployed: Only show deployed servers
                - is_verified: Only show verified servers  
                - owner: Filter by server owner
                Examples: {"is_deployed": true} or '{"is_deployed": true}'
    
    Returns:
        Dictionary containing:
        - status: "success", "filtered", or "error"
        - results: List of matching MCPs (if successful)
        - total_results: Number of results returned
        - filtered_count: Number of results filtered out
        - error_code: Specific error code (if error)
        - message: Human-readable status message
    """
    # Parse filters parameter: Handle both JSON strings and Python dictionaries
    parsed_filters = None
    if filters is not None:
        if isinstance(filters, str):
            try:
                parsed_filters = json.loads(filters)
                if not isinstance(parsed_filters, dict):
                    return {
                        "status": "error",
                        "error_code": "INVALID_FILTERS_FORMAT",
                        "message": "Filters must be a JSON object/dictionary, not an array or primitive value",
                        "example": '{"is_deployed": true, "is_verified": true}'
                    }
            except json.JSONDecodeError as e:
                return {
                    "status": "error", 
                    "error_code": "INVALID_FILTERS_JSON",
                    "message": f"Invalid JSON in filters parameter: {str(e)}",
                    "example": '{"is_deployed": true, "is_verified": true}'
                }
        elif isinstance(filters, dict):
            parsed_filters = filters
        else:
            return {
                "status": "error",
                "error_code": "INVALID_FILTERS_TYPE", 
                "message": f"Filters must be a dictionary or JSON string, got {type(filters).__name__}",
                "example": '{"is_deployed": true, "is_verified": true}'
            }
    
    # Pre-search filtering: Check if query targets capabilities Claude already has
    if should_exclude_search_query(query):
        alternatives = suggest_alternatives_for_excluded_query(query)
        return {
            "status": "filtered",
            "error_code": "REDUNDANT_CAPABILITY",
            "message": f"Query '{query}' targets capabilities Claude already has natively",
            "claude_native_capabilities": (
                "Claude has WebSearch, WebFetch, Read/Write/Edit/LS/Glob, and Bash tools"
            ),
            "alternatives": alternatives,
            "recommendation": (
                "Try searching for database integrations, external service APIs, "
                "or specialized processing tools instead"
            )
        }
    
    api_key = get_api_key()
    if not api_key:
        return {
            "status": "error",
            "error_code": "MISSING_API_KEY",
            "message": (
                "SMITHERY_API_KEY not found in environment variable or Claude config. "
                "Please set your API key to use the registry search."
            )
        }
    
    try:
        async with SmitheryRegistryClient(api_key) as client:
            # Build search query with filters - improved for semantic search
            search_query = query.strip()
            
            # Add filters if provided - use space separation for better semantic search
            if parsed_filters:
                filter_parts = []
                if parsed_filters.get("is_deployed"):
                    filter_parts.append("is:deployed")
                if parsed_filters.get("is_verified"):
                    filter_parts.append("is:verified")
                if parsed_filters.get("owner"):
                    filter_parts.append(f"owner:{parsed_filters['owner']}")
                
                if filter_parts:
                    if search_query:
                        search_query = f"{search_query} {' '.join(filter_parts)}"
                    else:
                        search_query = ' '.join(filter_parts)
            
            # Search with extra results for filtering
            server_list = await client.list_servers(
                query=search_query if search_query else None, 
                page=1, 
                pageSize=limit * 2
            )
            
            # Format raw results
            raw_results = []
            for server in server_list.servers:
                raw_results.append({
                    "qualified_name": server.qualifiedName,
                    "display_name": server.displayName,
                    "description": server.description,
                    "homepage": server.homepage,
                    "use_count": server.useCount,
                    "is_deployed": server.isDeployed,
                    "created_at": server.createdAt
                })
            
            # Post-search filtering: Remove MCPs that duplicate Claude's capabilities
            filtered_results = filter_redundant_results(raw_results)
            
            # Limit to requested count after filtering
            final_results = filtered_results[:limit]
            
            # Add debugging information for empty results
            if len(final_results) == 0:
                debugging_info = {
                    "no_results_reason": "No MCPs found matching your query in the Smithery Registry",
                    "suggestions": [
                        "Try broader search terms (e.g., 'redis' instead of 'upstash redis')",
                        "Search for general categories (e.g., 'database', 'vector', 'monitoring')",
                        "Check if the specific tool you're looking for exists in the registry"
                    ],
                    "popular_categories": [
                        "database (PostgreSQL, MongoDB, Redis)",
                        "vector (Qdrant, Pinecone, Chroma)", 
                        "api (GitHub, Slack, AWS)",
                        "document (PDF processing, document analysis)",
                        "monitoring (performance, logging)"
                    ]
                }
            else:
                debugging_info = {}
            
            return {
                "status": "success",
                "query": query,
                "search_query_sent": search_query,
                "total_results": len(final_results),
                "results": final_results,
                "raw_results_count": len(raw_results),
                "filtered_count": len(raw_results) - len(filtered_results),
                "filtering_note": (
                    "Results filtered to exclude capabilities Claude already has natively"
                ),
                "api_endpoint": f"{REGISTRY_API_BASE}/servers",
                **debugging_info
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "error_code": "SEARCH_FAILED",
            "message": f"Search failed: {str(e)}"
        }


@mcp.tool
async def get_mcp_info(qualified_name: str) -> Dict[str, Any]:
    """
    Retrieve detailed information about a specific MCP server.
    
    This tool fetches comprehensive details about an MCP server from the
    Smithery Registry, including deployment information and connection options.
    
    Args:
        qualified_name: The unique identifier of the MCP server (e.g., "example/postgres-mcp")
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - mcp_info: Detailed server information (if successful)
        - error_code: Specific error code (if error)
        - message: Human-readable status message
    """
    if not qualified_name or not qualified_name.strip():
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "qualified_name parameter is required and cannot be empty"
        }
    
    api_key = get_api_key()
    if not api_key:
        return {
            "status": "error",
            "error_code": "MISSING_API_KEY", 
            "message": (
                "SMITHERY_API_KEY not found in environment variable or Claude config. "
                "Please set your API key to retrieve MCP information."
            )
        }
    
    try:
        async with SmitheryRegistryClient(api_key) as client:
            server_details = await client.get_server(qualified_name.strip())
            
            # Build comprehensive MCP info
            mcp_info = {
                "qualified_name": server_details.qualifiedName,
                "display_name": server_details.displayName,
                "connections": [
                    {
                        "type": conn.type,
                        "url": conn.url,
                        "config_schema": conn.configSchema
                    }
                    for conn in server_details.connections
                ]
            }
            
            # Add optional fields if present
            if server_details.description:
                mcp_info["description"] = server_details.description
            if server_details.iconUrl:
                mcp_info["icon_url"] = server_details.iconUrl
            if server_details.remote is not None:
                mcp_info["remote"] = server_details.remote
            if server_details.deploymentUrl:
                mcp_info["deployment_url"] = server_details.deploymentUrl
            if server_details.security:
                mcp_info["security"] = {
                    "scan_passed": server_details.security.scanPassed
                }
            if server_details.tools:
                mcp_info["tools"] = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    for tool in server_details.tools
                ]
            
            return {
                "status": "success",
                "mcp_info": mcp_info,
                "install_instructions": {
                    "smithery_cli": f"npx -y @smithery/cli@latest install {server_details.qualifiedName} --client claude",
                    "note": "Use the install_mcp tool for automated installation with proper client and config support"
                }
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_code": "INFO_FAILED",
            "message": f"Failed to get MCP info for '{qualified_name}': {str(e)}"
        }


def _sanitize_mcp_name(qualified_name: str) -> str:
    """
    Sanitize MCP qualified name for Claude CLI compatibility.
    
    Claude CLI names can only contain letters, numbers, hyphens, and underscores.
    This function converts scoped NPM packages like @redis/mcp-redis to redis-mcp-redis.
    
    Args:
        qualified_name: Original qualified name (e.g., @redis/mcp-redis)
        
    Returns:
        Sanitized name safe for Claude CLI (e.g., redis-mcp-redis)
    """
    # Remove @ symbol and replace / with -
    sanitized = qualified_name.replace("@", "").replace("/", "-")
    
    # Replace any other invalid characters with hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '-', sanitized)
    
    # Remove consecutive hyphens and leading/trailing hyphens
    sanitized = re.sub(r'-+', '-', sanitized).strip('-')
    
    return sanitized


def _is_exact_match_in_args(qualified_name: str, args_list: List[str]) -> bool:
    """
    Check if qualified_name appears as a complete word/argument in the args list.
    
    This prevents false positives where "redis" would match "redis-cli" or vice versa.
    
    Args:
        qualified_name: The MCP name to search for
        args_list: List of command arguments to search in
        
    Returns:
        True if qualified_name appears as an exact argument, False otherwise
    """
    if not qualified_name or not args_list:
        return False
    
    # Check exact matches in the argument list
    for arg in args_list:
        if arg == qualified_name:
            return True
    
    return False


def _detect_api_requirements(qualified_name: str) -> Dict[str, Any]:
    """
    Detect if an MCP requires API keys based on its name and common patterns.
    
    Args:
        qualified_name: The MCP qualified name
        
    Returns:
        Dictionary with requires_api_key boolean and setup_instructions
    """
    # Common MCPs that require API keys
    api_key_mcps = {
        "redis": {
            "env_var": "REDIS_URL",
            "instructions": "Set REDIS_URL environment variable with your Redis connection string"
        },
        "datadog": {
            "env_var": "DD_API_KEY", 
            "instructions": "Set DD_API_KEY environment variable with your Datadog API key"
        },
        "slack": {
            "env_var": "SLACK_BOT_TOKEN",
            "instructions": "Set SLACK_BOT_TOKEN environment variable with your Slack bot token"
        },
        "github": {
            "env_var": "GITHUB_TOKEN",
            "instructions": "Set GITHUB_TOKEN environment variable with your GitHub personal access token"
        },
        "aws": {
            "env_var": "AWS_ACCESS_KEY_ID",
            "instructions": "Configure AWS credentials via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
        }
    }
    
    name_lower = qualified_name.lower()
    for service, config in api_key_mcps.items():
        if service in name_lower:
            return {
                "requires_api_key": True,
                "env_var": config["env_var"],
                "instructions": config["instructions"]
            }
    
    return {"requires_api_key": False}


@mcp.tool
async def install_mcp(
    qualified_name: str,
    client: str = "claude",
    config: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Install a single MCP server using the official Smithery CLI.
    
    This tool executes the installation command to add an MCP server to the
    specified client configuration, handling timeouts and providing detailed error reporting.
    Uses the official Smithery CLI for proper installation.
    
    Args:
        qualified_name: The unique identifier of the MCP to install (e.g., @redis/mcp-redis)
        client: Target client for installation (claude, cursor, windsurf, etc.) (default: claude)
        config: Optional configuration object to pass to the MCP
        timeout_seconds: Maximum time to wait for installation (default: 60)
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Human-readable status message
        - qualified_name: The original MCP qualified name
        - client: The target client
        - install_command: The full command that was executed
        - output: Installation output (if successful)
        - error_output: Error details (if failed)
        - error_code: Specific error code (if error)
        - api_requirements: Information about required API keys
    """
    if not qualified_name or not qualified_name.strip():
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "qualified_name parameter is required and cannot be empty"
        }
    
    # Detect API key requirements
    api_requirements = _detect_api_requirements(qualified_name)
    
    # Build official Smithery CLI command
    cmd_parts = ["npx", "-y", "@smithery/cli@latest", "install", qualified_name.strip(), "--client", client]
    
    # Add config if provided
    if config:
        config_json = json.dumps(config)
        # Pass config directly - subprocess.run handles argument separation properly
        cmd_parts.extend(["--config", config_json])
    
    full_command = " ".join(cmd_parts)
    
    # Retry logic for transient failures
    max_retries = 2
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Execute installation using secure subprocess with official Smithery CLI
            # Provide automatic "yes" response to any prompts
            result = subprocess.run(
                cmd_parts,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                input="y\n"
            )
            
            # Build success message with API key guidance if needed
            success_message = f"Successfully installed {qualified_name} for {client} client. Restart your terminal to use the new MCP."
            if api_requirements.get("requires_api_key"):
                success_message += f"\n\nIMPORTANT: This MCP requires API configuration:\n{api_requirements['instructions']}"
            
            return {
                "status": "success", 
                "message": success_message,
                "qualified_name": qualified_name.strip(),
                "client": client,
                "install_command": full_command,
                "output": result.stdout,
                "api_requirements": api_requirements
            }
            
        except subprocess.CalledProcessError as e:
            # Don't retry on command execution failures (likely permanent)
            error_message = f"Installation failed for {qualified_name} on {client} client"
            
            return {
                "status": "error",
                "error_code": "INSTALL_FAILED",
                "message": error_message,
                "qualified_name": qualified_name.strip(),
                "client": client,
                "install_command": full_command,
                "error_output": e.stderr,
                "api_requirements": api_requirements
            }
            
        except subprocess.TimeoutExpired as e:
            last_error = e
            # Retry on timeout (might be transient network issue)
            if attempt < max_retries - 1:
                continue
            
            return {
                "status": "error",
                "error_code": "INSTALL_TIMEOUT",
                "message": f"Installation timed out after {timeout_seconds}s (tried {max_retries} times). Try running manually: {full_command}",
                "qualified_name": qualified_name.strip(),
                "client": client,
                "timeout_seconds": timeout_seconds,
                "install_command": full_command,
                "api_requirements": api_requirements,
                "retry_attempts": max_retries
            }
            
        except Exception as e:
            last_error = e
            # Retry on unexpected errors (might be transient)
            if attempt < max_retries - 1:
                continue
            
            return {
                "status": "error",
                "error_code": "INSTALL_ERROR", 
                "message": f"Unexpected error during installation (tried {max_retries} times): {str(e)}",
                "qualified_name": qualified_name.strip(),
                "client": client,
                "install_command": full_command,
                "api_requirements": api_requirements,
                "retry_attempts": max_retries
            }


@mcp.tool
async def verify_installation(qualified_name: str) -> Dict[str, Any]:
    """
    Verify that an MCP server is properly installed and configured.
    
    This tool checks the Claude configuration file to confirm that the specified
    MCP server has been successfully installed and is available for use.
    Checks both the original qualified name and the sanitized name used by Claude CLI.
    
    Args:
        qualified_name: The unique identifier of the MCP to verify (e.g., @redis/mcp-redis)
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - verified: Boolean indicating if the MCP is installed
        - qualified_name: The original MCP qualified name that was checked
        - sanitized_name: The sanitized name used by Claude CLI
        - found_name: The actual name found in Claude config (if verified)
        - config_path: Path to the Claude configuration file
        - error_code: Specific error code (if error)
        - message: Human-readable status message
    """
    if not qualified_name or not qualified_name.strip():
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "qualified_name parameter is required and cannot be empty"
        }
    
    try:
        # Check Claude configuration
        config_result = await get_installed_mcps()
        
        if config_result.get("status") != "success":
            return {
                "status": "error",
                "error_code": "CONFIG_CHECK_FAILED",
                "message": "Could not read Claude configuration file",
                "verified": False,
                "qualified_name": qualified_name.strip()
            }
        
        # Look for the MCP in installed list
        qualified_name_clean = qualified_name.strip()
        sanitized_name = _sanitize_mcp_name(qualified_name_clean)
        found = False
        found_name = None
        
        for mcp_entry in config_result.get("installed_mcps", []):
            entry_name = mcp_entry.get("name", "")
            entry_args = mcp_entry.get("args", [])
            
            # Check if the qualified name, sanitized name, or original name appears in entry or args
            # Use exact matching for args to prevent false positives (e.g., "redis" vs "redis-cli")
            if (entry_name == qualified_name_clean or 
                entry_name == sanitized_name or
                _is_exact_match_in_args(qualified_name_clean, entry_args) or
                _is_exact_match_in_args(sanitized_name, entry_args)):
                found = True
                found_name = entry_name
                break
        
        if found:
            message = f"MCP '{qualified_name_clean}' is installed as '{found_name}'"
        else:
            message = f"MCP '{qualified_name_clean}' is not installed. Expected sanitized name: '{sanitized_name}'"
        
        return {
            "status": "success",
            "verified": found,
            "qualified_name": qualified_name_clean,
            "sanitized_name": sanitized_name,
            "found_name": found_name,
            "config_path": config_result.get("config_path"),
            "message": message
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_code": "VERIFICATION_ERROR",
            "message": f"Verification failed for '{qualified_name}': {str(e)}",
            "verified": False,
            "qualified_name": qualified_name.strip()
        }


@mcp.tool
async def list_installed() -> Dict[str, Any]:
    """
    List all currently installed MCP servers from the Claude configuration.
    
    This tool reads the Claude configuration file and returns information about
    all MCP servers that are currently installed and configured.
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - installed_mcps: List of installed MCP configurations (if successful)
        - total_count: Number of installed MCPs
        - config_path: Path to the Claude configuration file
        - error_code: Specific error code (if error)
        - message: Human-readable status message
    """
    try:
        result = await get_installed_mcps()
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "installed_mcps": result.get("installed_mcps", []),
                "total_count": result.get("total", 0),
                "config_path": result.get("config_path"),
                "message": f"Found {result.get('total', 0)} installed MCPs"
            }
        else:
            return {
                "status": "error",
                "error_code": result.get("error_code", "CONFIG_READ_FAILED"),
                "message": result.get("message", "Failed to read Claude configuration")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_code": "LIST_ERROR",
            "message": f"Failed to list installed MCPs: {str(e)}"
        }



@mcp.tool
async def collect_config(qualified_name: str) -> Dict[str, Any]:
    """
    Collect configuration schema and requirements for a specific MCP server.
    
    This tool retrieves detailed configuration information needed to properly
    set up an MCP server, including required environment variables, connection
    types, and configuration schemas.
    
    Args:
        qualified_name: The unique identifier of the MCP server (e.g., @redis/mcp-redis)
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - config_info: Configuration details and requirements (if successful)
        - error_code: Specific error code (if error)
        - message: Human-readable status message
    """
    if not qualified_name or not qualified_name.strip():
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "qualified_name parameter is required and cannot be empty"
        }
    
    api_key = get_api_key()
    if not api_key:
        return {
            "status": "error",
            "error_code": "MISSING_API_KEY",
            "message": (
                "SMITHERY_API_KEY not found in environment variable or Claude config. "
                "Please set your API key to collect configuration information."
            )
        }
    
    try:
        async with SmitheryRegistryClient(api_key) as client:
            server_details = await client.get_server(qualified_name.strip())
            
            # Collect configuration information
            config_info = {
                "qualified_name": server_details.qualifiedName,
                "display_name": server_details.displayName,
                "connections": []
            }
            
            # Process each connection type and its configuration schema
            for conn in server_details.connections:
                connection_info = {
                    "type": conn.type,
                    "url": conn.url,
                    "config_schema": conn.configSchema
                }
                
                # Extract required fields from config schema
                if conn.configSchema and isinstance(conn.configSchema, dict):
                    schema = conn.configSchema
                    required_fields = schema.get("required", [])
                    properties = schema.get("properties", {})
                    
                    connection_info["required_fields"] = required_fields
                    connection_info["field_descriptions"] = {}
                    
                    for field in required_fields:
                        if field in properties:
                            field_info = properties[field]
                            connection_info["field_descriptions"][field] = {
                                "type": field_info.get("type", "string"),
                                "description": field_info.get("description", "")
                            }
                
                config_info["connections"].append(connection_info)
            
            # Add API key requirements detection
            api_requirements = _detect_api_requirements(qualified_name)
            if api_requirements.get("requires_api_key"):
                config_info["api_requirements"] = api_requirements
            
            # Add security information
            if server_details.security:
                config_info["security"] = {
                    "scan_passed": server_details.security.scanPassed
                }
            
            return {
                "status": "success",
                "config_info": config_info,
                "setup_guidance": {
                    "step_1": "Review required configuration fields",
                    "step_2": "Set up any required API keys or environment variables",
                    "step_3": "Use install_mcp tool with proper config parameter",
                    "example": f"install_mcp(qualified_name='{qualified_name}', client='claude', config={{'key': 'value'}})"
                }
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_code": "CONFIG_COLLECTION_FAILED",
            "message": f"Failed to collect config for '{qualified_name}': {str(e)}"
        }


@mcp.tool  
async def uninstall_mcp(qualified_name: str) -> Dict[str, Any]:
    """
    Remove an MCP server from the Claude configuration.
    
    This tool safely removes an MCP server from the Claude configuration file,
    effectively uninstalling it from the system.
    
    Args:
        qualified_name: The unique identifier of the MCP to remove
    
    Returns:
        Dictionary containing:
        - status: "success" or "error"
        - message: Human-readable status message
        - qualified_name: The MCP that was removed
        - removed_entries: List of configuration entries that were removed
        - error_code: Specific error code (if error)
    """
    if not qualified_name or not qualified_name.strip():
        return {
            "status": "error",
            "error_code": "INVALID_INPUT", 
            "message": "qualified_name parameter is required and cannot be empty"
        }
    
    config_path = Path.home() / ".config" / "claude" / "claude_config.json"
    qualified_name_clean = qualified_name.strip()
    
    try:
        if not config_path.exists():
            return {
                "status": "error",
                "error_code": "CONFIG_NOT_FOUND",
                "message": f"Claude configuration file not found at {config_path}"
            }
        
        # Read current configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        mcps = config.get("mcpServers", {})
        removed_entries = []
        
        # Find MCP entries to remove (by name or in args)
        to_remove = []
        for name, details in mcps.items():
            args = details.get("args", [])
            
            # Check if the qualified name matches either the entry name or appears exactly in args
            # Use exact matching for args to prevent false positives (e.g., "redis" vs "redis-cli")
            if name == qualified_name_clean or _is_exact_match_in_args(qualified_name_clean, args):
                to_remove.append(name)
                removed_entries.append({
                    "name": name,
                    "command": details.get("command", ""),
                    "args": args
                })
        
        # Remove found MCPs
        for name in to_remove:
            del mcps[name]
        
        if removed_entries:
            # Write updated configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return {
                "status": "success",
                "message": f"Successfully removed '{qualified_name_clean}' from configuration",
                "qualified_name": qualified_name_clean,
                "removed_entries": removed_entries,
                "config_path": str(config_path)
            }
        else:
            return {
                "status": "error",
                "error_code": "NOT_FOUND",
                "message": f"MCP '{qualified_name_clean}' not found in configuration",
                "qualified_name": qualified_name_clean
            }
            
    except (json.JSONDecodeError, PermissionError) as e:
        return {
            "status": "error",
            "error_code": "UNINSTALL_ERROR",
            "message": f"Failed to uninstall '{qualified_name_clean}': {str(e)}",
            "qualified_name": qualified_name_clean
        }


if __name__ == "__main__":
    # Start the FastMCP server in STDIO mode
    mcp.run()