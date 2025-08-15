#!/usr/bin/env python3
"""
MCP Scout - Automated MCP Discovery and Integration

A FastMCP-based server that automates the discovery and installation of
Model Context Protocol servers using the Smithery Registry API.

Step 1: Implements find_mcp tool for semantic search
Step 2: Will implement find_and_install_mcp tool for automated installation
"""

import asyncio
import base64
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

import aiohttp
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Initialize the FastMCP server
mcp = FastMCP("MCP Scout")

# Constants
REGISTRY_API_BASE = "https://registry.smithery.ai"

# Data models based on actual API response structure
class ServerListItem(BaseModel):
    qualifiedName: str
    displayName: str
    description: str
    homepage: str
    useCount: int  # API returns integer, not string
    isDeployed: Optional[bool] = None  # Field is optional in API response
    createdAt: str

class ServerList(BaseModel):
    servers: List[ServerListItem]
    pagination: Dict[str, Any]

class Connection(BaseModel):
    type: str
    url: Optional[str] = None
    configSchema: Dict[str, Any]

class ServerDetails(BaseModel):
    qualifiedName: str
    displayName: str
    deploymentUrl: str
    connections: List[Connection]

class SmitheryRegistryClient:
    """Python async client for Smithery Registry API, based on TypeScript implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Smithery Registry API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with context.")
        
        async with self.session.get(url, **kwargs) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API request failed: {response.status} {response.reason} - {error_text}")
            
            return await response.json()
    
    async def list_servers(
        self, 
        query: Optional[str] = None, 
        page: int = 1, 
        pageSize: int = 10
    ) -> ServerList:
        """Get a list of servers with optional filtering"""
        url = f"{REGISTRY_API_BASE}/servers"
        params = {
            "page": str(page),
            "pageSize": str(pageSize)
        }
        
        if query:
            params["query"] = query
        
        data = await self._request(url, params=params)
        return ServerList(**data)
    
    async def get_server(self, qualified_name: str) -> ServerDetails:
        """Get details for a specific server"""
        url = f"{REGISTRY_API_BASE}/servers/{qualified_name}"
        data = await self._request(url)
        return ServerDetails(**data)
    
    def create_websocket_url(self, qualified_name: str, config: Dict[str, Any]) -> str:
        """Create a websocket URL with proper config encoding"""
        config_json = json.dumps(config)
        base64_config = base64.b64encode(config_json.encode()).decode()
        return f"https://server.smithery.ai/{qualified_name}/ws?config={base64_config}"

# Step 1: Finder - internal helper
async def find_mcp(query: str) -> Dict[str, Any]:
    """
    Finds the best-matching MCP server from the Smithery Registry using semantic search.
    
    Args:
        query: Natural language description of the desired MCP functionality
               (e.g., "python linter", "web search", "database query")
    
    Returns:
        Dictionary containing the best match with name, description, and install command,
        or an error message if no matches found or API call fails.
    """
    # Validate query input
    if not query or not query.strip():
        return {
            "error": "Query cannot be empty. Please provide a description of the desired MCP functionality."
        }
    
    api_key = os.getenv('SMITHERY_API_KEY')
    if not api_key:
        return {
            "error": "SMITHERY_API_KEY environment variable not set. Please set your API key."
        }
    
    try:
        async with SmitheryRegistryClient(api_key) as client:
            # Search for servers using the query
            server_list = await client.list_servers(query=query, page=1, pageSize=5)
            
            if not server_list.servers:
                return {
                    "error": f"No matching MCP servers found for query: '{query}'"
                }
            
            # Select the top result (best match)
            selected = server_list.servers[0]
            
            # Generate install command based on Smithery patterns
            # Most Smithery MCPs use npx pattern for installation
            install_command = f"npx -y {selected.qualifiedName}"
            
            return {
                "name": selected.displayName,
                "qualifiedName": selected.qualifiedName,
                "description": selected.description,
                "homepage": selected.homepage,
                "useCount": selected.useCount,
                "install_command": install_command,
                "isDeployed": selected.isDeployed if selected.isDeployed is not None else False,
                "createdAt": selected.createdAt
            }
    
    except Exception as e:
        return {
            "error": f"API request failed: {str(e)}"
        }

# Step 2: Installer - internal helper
async def find_and_install_mcp(query: str) -> Dict[str, Any]:
    """
    Finds and automatically installs the best-matching MCP server.
    
    Args:
        query: Natural language description of the desired MCP functionality
    
    Returns:
        Dictionary with installation status, success/error message, and details.
    """
    # First, find the best MCP
    find_result = await find_mcp(query)
    
    if "error" in find_result:
        return find_result
    
    # Extract install command
    install_command = find_result.get("install_command", "")
    qualified_name = find_result.get("qualifiedName", "")
    
    if not install_command or not qualified_name:
        return {
            "status": "error",
            "message": "Invalid MCP data - missing install command or qualified name",
            "details": find_result
        }
    
    # Construct the full claude mcp add command
    # Following Smithery pattern: claude mcp add <name> -- <install_command>
    full_command = f"claude mcp add {qualified_name} -- {install_command}"
    
    try:
        # Execute the installation command
        result = subprocess.run(
            full_command.split(),
            check=True,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        return {
            "status": "success",
            "message": f"Successfully installed {find_result['name']}. Restart your terminal to use the new MCP.",
            "mcp_info": {
                "name": find_result["name"],
                "qualifiedName": qualified_name,
                "description": find_result["description"]
            },
            "install_command": full_command,
            "details": result.stdout
        }
    
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"Installation failed for {find_result['name']}",
            "mcp_info": {
                "name": find_result["name"],
                "qualifiedName": qualified_name
            },
            "install_command": full_command,
            "details": e.stderr
        }
    
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": f"Installation timed out for {find_result['name']}",
            "install_command": full_command,
            "details": "Command exceeded 60 second timeout"
        }
    
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Unexpected error during installation: {str(e)}",
            "install_command": full_command,
            "details": str(e)
        }

# Simple, explicit data models for MCP operations
class SearchRequest(BaseModel):
    """Simple search request for Smithery Registry"""
    query: str = Field(description="Search term")
    limit: int = Field(default=10, description="Maximum results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional Smithery API filters")

class MCPInfo(BaseModel):
    """Basic MCP information"""
    qualified_name: str
    display_name: str
    description: str
    install_command: str
    homepage: Optional[str] = None
    use_count: Optional[int] = None

class InstallRequest(BaseModel):
    """Installation request"""
    qualified_name: str
    install_command: Optional[str] = Field(default=None, description="Override install command")
    timeout_seconds: int = Field(default=60, description="Installation timeout")


@mcp.tool
async def setup_mcp(query: Optional[str] = None, analysis: Optional[Any] = None) -> Dict[str, Any]:
    """
    DEPRECATED: Use the new atomic tools instead: search_registry, install_mcp, verify_installation.
    This tool will be removed in v2.0.

    Simplified setup using new atomic operations.
    """
    # Deprecation warning
    deprecation_msg = "⚠️  DEPRECATED: setup_mcp is deprecated. Use new atomic tools: search_registry, install_mcp, verify_installation"
    
    if not query:
        return {
            "status": "error", 
            "error": "Provide a 'query' parameter. The 'analysis' parameter is deprecated.",
            "deprecation_warning": deprecation_msg
        }

    # 1) Search using new atomic tool
    search_result = await search_registry(query, limit=1)
    if search_result.get("status") != "success" or not search_result.get("results"):
        return {
            "status": "error",
            "error": f"No MCPs found for query: '{query}'",
            "deprecation_warning": deprecation_msg
        }
    
    # Get top result
    top_result = search_result["results"][0]
    qualified_name = top_result["qualified_name"]
    
    # 2) Install using new atomic tool
    install_result = await install_mcp(qualified_name)
    if install_result.get("status") != "success":
        return {
            "status": "error",
            "error": install_result.get("message", "Installation failed"),
            "deprecation_warning": deprecation_msg
        }
    
    # 3) Verify using new atomic tool
    verify_result = await verify_installation(qualified_name)
    verified = verify_result.get("verified", False)
    
    return {
        "status": "success",
        "deprecation_warning": deprecation_msg,
        "discovered": {
            "name": top_result["display_name"],
            "qualifiedName": qualified_name,
            "install_command": top_result["install_command"]
        },
        "installation": {
            "status": install_result["status"],
            "message": install_result["message"]
        },
        "verification": {
            "verified": verified,
            "config_path": verify_result.get("config_path")
        }
    }

@mcp.tool
async def discover_mcps(analysis: Any) -> Dict[str, Any]:
    """
    DEPRECATED: Use search_registry instead for direct semantic search.
    This tool will be removed in v2.0.
    
    Simple discovery using new atomic search.
    """
    deprecation_msg = "⚠️  DEPRECATED: discover_mcps is deprecated. Use search_registry for direct semantic search."
    
    # Simple fallback - just search for generic terms
    try:
        if isinstance(analysis, dict):
            # Extract simple search terms from analysis
            search_terms = []
            
            # Try to extract meaningful search terms from the analysis
            languages = analysis.get("languages", [])
            frameworks = analysis.get("frameworks", [])
            suggested_mcps = analysis.get("suggested_mcps", [])
            
            # Build basic search terms
            search_terms.extend(suggested_mcps[:3])  # Use first 3 suggestions
            search_terms.extend(languages[:2])       # Use first 2 languages
            search_terms.extend(frameworks[:2])      # Use first 2 frameworks
            
            if not search_terms:
                search_terms = ["development tools"]
                
        elif isinstance(analysis, str):
            parsed = json.loads(analysis)
            # Recursively call with parsed dict
            return await discover_mcps(parsed)
        else:
            search_terms = ["development tools"]
            
        # Search using our new atomic tool
        results = []
        for term in search_terms[:3]:  # Limit to 3 searches
            search_result = await search_registry(term, limit=3)
            if search_result.get("status") == "success":
                for result in search_result.get("results", []):
                    results.append({
                        "qualifiedName": result["qualified_name"],
                        "displayName": result["display_name"],
                        "description": result["description"],
                        "relevance_score": 0.5,  # Basic score
                        "reason": f"Found via search: {term}",
                        "install_command": result["install_command"]
                    })
        
        # Remove duplicates and limit results
        seen = set()
        unique_results = []
        for result in results:
            if result["qualifiedName"] not in seen:
                seen.add(result["qualifiedName"])
                unique_results.append(result)
        
        return {
            "status": "success",
            "deprecation_warning": deprecation_msg,
            "project_summary": {
                "type": "unknown",
                "search_terms_used": search_terms[:3]
            },
            "recommendations": unique_results[:10],
            "total_found": len(unique_results)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Discovery failed: {str(e)}",
            "deprecation_warning": deprecation_msg
        }


def calculate_relevance(description: str, languages: List[str], 
                        frameworks: List[str], project_type: str) -> float:
    """
    Calculate relevance score based on description matching project characteristics.
    """
    score = 0.5  # Base score
    
    description_lower = description.lower()
    
    # Check language matches
    for lang in languages:
        if lang.lower() in description_lower:
            score += 0.15
    
    # Check framework matches
    for framework in frameworks:
        if framework.lower() in description_lower:
            score += 0.1
    
    # Check project type keywords
    type_keywords = {
        "web": ["http", "api", "server", "web", "rest"],
        "cli": ["command", "terminal", "cli", "shell"],
        "data": ["database", "sql", "data", "analytics"],
        "ai": ["llm", "ai", "ml", "model", "embedding"]
    }
    
    if project_type in type_keywords:
        for keyword in type_keywords[project_type]:
            if keyword in description_lower:
                score += 0.05
    
    return min(score, 1.0)  # Cap at 1.0












async def check_mcp() -> Dict[str, Any]:
    """
    Check which MCPs are currently installed in Claude Code configuration.
    
    Returns:
        Dictionary with list of installed MCPs
    """
    config_path = Path.home() / ".config" / "claude" / "claude_config.json"
    
    if not config_path.exists():
        return {
            "status": "error",
            "message": "Claude Code configuration not found",
            "config_path": str(config_path)
        }
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        mcps = config.get("mcpServers", {})
        
        installed = []
        for name, details in mcps.items():
            installed.append({
                "name": name,
                "command": details.get("command", ""),
                "args": details.get("args", [])
            })
        
        return {
            "status": "success",
            "installed_mcps": installed,
            "total": len(installed),
            "config_path": str(config_path)
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to read configuration: {str(e)}",
            "config_path": str(config_path)
        }


# New Atomic Tools - Simple, Explicit MCP Operations

@mcp.tool
async def search_registry(
    query: str, 
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Pure semantic search of Smithery Registry.
    
    Args:
        query: Exact search term (no interpretation)
        limit: Maximum results to return
        filters: Optional Smithery API filters (is_deployed, is_verified, etc.)
    
    Returns:
        Raw search results from Smithery
    """
    api_key = os.getenv('SMITHERY_API_KEY')
    if not api_key:
        return {
            "status": "error",
            "error_code": "MISSING_API_KEY",
            "message": "SMITHERY_API_KEY environment variable not set"
        }
    
    try:
        async with SmitheryRegistryClient(api_key) as client:
            # Build search parameters
            params = {"page": 1, "pageSize": limit}
            if query.strip():
                params["query"] = query.strip()
            
            # Add filters if provided
            if filters:
                # Convert common filter patterns
                if filters.get("is_deployed"):
                    query = f"{query} is:deployed" if query.strip() else "is:deployed"
                if filters.get("is_verified"):
                    query = f"{query} is:verified" if query.strip() else "is:verified"
                if filters.get("owner"):
                    query = f"{query} owner:{filters['owner']}" if query.strip() else f"owner:{filters['owner']}"
            
            # Search the registry
            server_list = await client.list_servers(query=query, page=1, pageSize=limit)
            
            # Format results
            results = []
            for server in server_list.servers:
                results.append({
                    "qualified_name": server.qualifiedName,
                    "display_name": server.displayName,
                    "description": server.description,
                    "homepage": server.homepage,
                    "use_count": server.useCount,
                    "is_deployed": server.isDeployed,
                    "created_at": server.createdAt,
                    "install_command": f"npx -y {server.qualifiedName}"
                })
            
            return {
                "status": "success",
                "query": query,
                "total_results": len(results),
                "results": results
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
    Get detailed information about a specific MCP.
    
    Args:
        qualified_name: Exact MCP identifier
    
    Returns:
        Complete MCP details from Smithery
    """
    api_key = os.getenv('SMITHERY_API_KEY')
    if not api_key:
        return {
            "status": "error",
            "error_code": "MISSING_API_KEY", 
            "message": "SMITHERY_API_KEY environment variable not set"
        }
    
    try:
        async with SmitheryRegistryClient(api_key) as client:
            server_details = await client.get_server(qualified_name)
            
            return {
                "status": "success",
                "mcp_info": {
                    "qualified_name": server_details.qualifiedName,
                    "display_name": server_details.displayName,
                    "deployment_url": server_details.deploymentUrl,
                    "connections": server_details.connections,
                    "install_command": f"npx -y {server_details.qualifiedName}"
                }
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_code": "INFO_FAILED",
            "message": f"Failed to get MCP info: {str(e)}"
        }

@mcp.tool
async def install_mcp(
    qualified_name: str,
    install_command: Optional[str] = None,
    timeout_seconds: int = 60
) -> Dict[str, Any]:
    """
    Install a single MCP.
    
    Args:
        qualified_name: MCP to install
        install_command: Optional override for install command
        timeout_seconds: Installation timeout
    
    Returns:
        Installation status and output
    """
    if not qualified_name or not qualified_name.strip():
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "qualified_name is required"
        }
    
    # Use provided install command or generate default
    cmd = install_command or f"npx -y {qualified_name}"
    full_command = f"claude mcp add {qualified_name} -- {cmd}"
    
    try:
        # Execute installation
        result = subprocess.run(
            ["claude", "mcp", "add", qualified_name, "--"] + cmd.split(),
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        return {
            "status": "success", 
            "message": f"Successfully installed {qualified_name}",
            "qualified_name": qualified_name,
            "install_command": full_command,
            "output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "error_code": "INSTALL_FAILED",
            "message": f"Installation failed for {qualified_name}",
            "qualified_name": qualified_name,
            "install_command": full_command,
            "error_output": e.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error_code": "INSTALL_TIMEOUT",
            "message": f"Installation timed out for {qualified_name}",
            "qualified_name": qualified_name,
            "timeout_seconds": timeout_seconds
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_code": "INSTALL_ERROR", 
            "message": f"Unexpected error: {str(e)}",
            "qualified_name": qualified_name
        }

@mcp.tool
async def verify_installation(qualified_name: str) -> Dict[str, Any]:
    """
    Check if an MCP is properly installed.
    
    Args:
        qualified_name: MCP to verify
    
    Returns:
        Verification status
    """
    if not qualified_name or not qualified_name.strip():
        return {
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": "qualified_name is required"
        }
    
    try:
        # Check Claude configuration
        config_check = await check_mcp()
        
        if config_check.get("status") != "success":
            return {
                "status": "error",
                "error_code": "CONFIG_CHECK_FAILED",
                "message": "Could not read Claude configuration",
                "verified": False
            }
        
        # Look for the MCP in installed list
        found = False
        for mcp_entry in config_check.get("installed_mcps", []):
            entry_name = mcp_entry.get("name", "")
            entry_args = " ".join(mcp_entry.get("args", []))
            
            if entry_name == qualified_name or qualified_name in entry_args:
                found = True
                break
        
        return {
            "status": "success",
            "verified": found,
            "qualified_name": qualified_name,
            "config_path": config_check.get("config_path")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_code": "VERIFICATION_ERROR",
            "message": f"Verification failed: {str(e)}",
            "verified": False
        }

@mcp.tool
async def list_installed() -> Dict[str, Any]:
    """
    List all installed MCPs from Claude config.
    
    Returns:
        List of installed MCPs with their configurations
    """
    try:
        result = await check_mcp()
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "installed_mcps": result.get("installed_mcps", []),
                "total_count": result.get("total", 0),
                "config_path": result.get("config_path")
            }
        else:
            return {
                "status": "error",
                "error_code": "CONFIG_READ_FAILED",
                "message": result.get("message", "Failed to read configuration")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_code": "LIST_ERROR",
            "message": f"Failed to list installed MCPs: {str(e)}"
        }

@mcp.tool  
async def uninstall_mcp(qualified_name: str) -> Dict[str, Any]:
    """
    Remove an MCP from Claude configuration.
    
    Args:
        qualified_name: MCP to remove
    
    Returns:
        Removal status
    """
    if not qualified_name or not qualified_name.strip():
        return {
            "status": "error",
            "error_code": "INVALID_INPUT", 
            "message": "qualified_name is required"
        }
    
    config_path = Path.home() / ".config" / "claude" / "claude_config.json"
    
    try:
        if not config_path.exists():
            return {
                "status": "error",
                "error_code": "CONFIG_NOT_FOUND",
                "message": "Claude configuration file not found"
            }
        
        # Read current config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        mcps = config.get("mcpServers", {})
        removed = False
        
        # Look for MCP to remove (by name or in args)
        to_remove = []
        for name, details in mcps.items():
            args = details.get("args", [])
            args_str = " ".join(args)
            
            if name == qualified_name or qualified_name in args_str:
                to_remove.append(name)
                removed = True
        
        # Remove found MCPs
        for name in to_remove:
            del mcps[name]
        
        if removed:
            # Write updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return {
                "status": "success",
                "message": f"Removed {qualified_name} from configuration",
                "qualified_name": qualified_name,
                "removed_entries": to_remove
            }
        else:
            return {
                "status": "error",
                "error_code": "NOT_FOUND",
                "message": f"MCP {qualified_name} not found in configuration"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_code": "UNINSTALL_ERROR",
            "message": f"Failed to uninstall {qualified_name}: {str(e)}"
        }

if __name__ == "__main__":
    # Start the FastMCP server
    mcp.run()