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

# New models for codebase analysis
class CodebaseAnalysis(BaseModel):
    """Structure for codebase analysis results from Claude Code"""
    languages: List[str] = Field(description="Programming languages detected")
    frameworks: List[str] = Field(description="Frameworks and libraries identified")
    project_type: str = Field(description="Type of project (web, cli, library, etc.)")
    dependencies: Optional[List[str]] = Field(default=None, description="Key dependencies")
    suggested_mcps: List[str] = Field(description="Natural language MCP suggestions")

class MCPRecommendation(BaseModel):
    """MCP recommendation with relevance score"""
    qualifiedName: str
    displayName: str
    description: str
    relevance_score: float = Field(ge=0, le=1, description="Relevance score 0-1")
    reason: str = Field(description="Why this MCP is recommended")
    install_command: str

@mcp.tool
async def setup_mcp(query: Optional[str] = None, analysis: Optional[Any] = None) -> Dict[str, Any]:
    """
    Discover, install, and verify an MCP in one step.

    Args:
        query: Natural language description of desired MCP functionality (e.g., "python linter").
        analysis: Codebase analysis (object or JSON string) used to discover relevant MCPs.

    Returns:
        Dictionary with discovery result, installation status, and verification.
    """
    api_key = os.getenv('SMITHERY_API_KEY')
    if not api_key:
        return {
            "status": "error",
            "error": "SMITHERY_API_KEY environment variable not set. If running via Claude Code, add it under env in claude_config.json and fully restart the app."
        }

    if not query and analysis is None:
        return {"status": "error", "error": "Provide either 'query' or 'analysis'"}

    # 1) Discover target MCP
    selected: Optional[Dict[str, Any]] = None

    if query:
        found = await find_mcp(query)
        if "error" in found:
            return {"status": "error", "error": found["error"]}
        selected = found
    else:
        # Normalize analysis
        try:
            if isinstance(analysis, CodebaseAnalysis):
                analysis_model = analysis
            elif isinstance(analysis, dict):
                analysis_model = CodebaseAnalysis(**analysis)
            elif isinstance(analysis, str):
                parsed = json.loads(analysis)
                if not isinstance(parsed, dict):
                    return {"status": "error", "error": "Invalid analysis payload: expected JSON object after parsing string"}
                analysis_model = CodebaseAnalysis(**parsed)
            else:
                return {"status": "error", "error": "Invalid analysis payload: expected object or JSON string"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to parse analysis payload: {str(e)}"}

        recs = await discover_mcps(analysis_model)
        if recs.get("status") != "success" or not recs.get("recommendations"):
            return {"status": "error", "error": recs.get("error", "No recommendations found")}
        top = recs["recommendations"][0]
        selected = {
            "name": top.get("displayName"),
            "qualifiedName": top.get("qualifiedName"),
            "description": top.get("description", ""),
            "install_command": top.get("install_command")
        }

    if not selected or not selected.get("qualifiedName") or not selected.get("install_command"):
        return {"status": "error", "error": "Discovery did not return a qualifiedName and install_command"}

    qualified_name = selected["qualifiedName"]
    install_command = selected["install_command"]

    # 2) Install via Claude CLI
    full_command = f"claude mcp add {qualified_name} -- {install_command}"
    try:
        result = subprocess.run(
            full_command.split(),
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        install_status = {
            "status": "success",
            "message": f"Installed {selected['name']} ({qualified_name}). Restart your terminal/Claude to use it.",
            "install_command": full_command,
            "details": result.stdout,
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "error": f"Installation failed for {selected.get('name', qualified_name)}",
            "install_command": full_command,
            "details": e.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": f"Installation timed out for {selected.get('name', qualified_name)}",
            "install_command": full_command,
            "details": "Command exceeded 60 second timeout"
        }

    # 3) Verify config contains the MCP
    verification = await check_mcp()
    verified = False
    if verification.get("status") == "success":
        for entry in verification.get("installed_mcps", []):
            entry_name = entry.get("name", "")
            entry_args = " ".join(entry.get("args", []))
            if entry_name == qualified_name or (qualified_name and qualified_name in entry_args):
                verified = True
                break

    return {
        "status": "success",
        "discovered": {
            "name": selected["name"],
            "qualifiedName": qualified_name,
            "install_command": install_command
        },
        "installation": install_status,
        "verification": {
            "verified": verified,
            "config_path": verification.get("config_path"),
            "installed_count": verification.get("total") if verification.get("status") == "success" else None
        }
    }

@mcp.tool
async def discover_mcps(analysis: Any) -> Dict[str, Any]:
    """
    Takes codebase analysis from Claude Code and recommends relevant MCPs.
    
    Args:
        analysis: Codebase analysis results including languages, frameworks, and suggestions.
                  Accepts either an object (preferred) or a JSON string. If a string is
                  provided, the server will attempt to parse it as JSON.
    
    Returns:
        Dictionary with recommended MCPs ranked by relevance
    """
    api_key = os.getenv('SMITHERY_API_KEY')
    if not api_key:
        return {
            "error": "SMITHERY_API_KEY environment variable not set. If running via Claude Code, add it under env in claude_config.json and fully restart the app."
        }
    
    # Normalize input to CodebaseAnalysis
    try:
        if isinstance(analysis, CodebaseAnalysis):
            analysis_model = analysis
        elif isinstance(analysis, dict):
            analysis_model = CodebaseAnalysis(**analysis)
        elif isinstance(analysis, str):
            parsed = json.loads(analysis)
            if not isinstance(parsed, dict):
                return {"error": "Invalid analysis payload: expected JSON object after parsing string"}
            analysis_model = CodebaseAnalysis(**parsed)
        else:
            return {"error": "Invalid analysis payload: expected object or JSON string"}
    except Exception as e:
        return {"error": f"Failed to parse analysis payload: {str(e)}"}

    recommendations = []
    
    try:
        async with SmitheryRegistryClient(api_key) as client:
            # Search for each suggested MCP
            for suggestion in analysis_model.suggested_mcps:
                result = await find_mcp(suggestion)
                
                if "error" not in result:
                    # Calculate relevance based on project characteristics
                    relevance = calculate_relevance(
                        result.get("description", ""),
                        analysis_model.languages,
                        analysis_model.frameworks,
                        analysis_model.project_type
                    )
                    
                    recommendations.append(MCPRecommendation(
                        qualifiedName=result["qualifiedName"],
                        displayName=result["name"],
                        description=result["description"],
                        relevance_score=relevance,
                        reason=f"Recommended for {analysis_model.project_type} projects using {', '.join(analysis_model.languages[:2])}",
                        install_command=result["install_command"]
                    ).dict())
            
            # Sort by relevance score
            recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return {
                "status": "success",
                "project_summary": {
                    "type": analysis_model.project_type,
                    "languages": analysis_model.languages,
                    "frameworks": analysis_model.frameworks
                },
                "recommendations": recommendations[:10],  # Top 10 recommendations
                "total_found": len(recommendations)
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to generate recommendations: {str(e)}"
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

async def install_mcp(qualified_names: List[str]) -> Dict[str, Any]:
    """
    Install multiple MCPs in batch.
    
    Args:
        qualified_names: List of MCP qualified names to install
    
    Returns:
        Dictionary with installation results for each MCP
    """
    results = []
    
    for name in qualified_names:
        # Find the MCP first to get install command
        find_result = await find_mcp(name)
        
        if "error" in find_result:
            results.append({
                "qualifiedName": name,
                "status": "error",
                "message": find_result["error"]
            })
            continue
        
        # Install it
        install_result = await find_and_install_mcp(name)
        results.append({
            "qualifiedName": name,
            "status": install_result.get("status"),
            "message": install_result.get("message", "")
        })
    
    return {
        "status": "complete",
        "installed": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "error"),
        "results": results
    }

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

async def update_claude_config(mcps_to_add: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Update Claude Code configuration with new MCPs.
    
    Args:
        mcps_to_add: List of MCP configurations to add
                    Each should have: name, command, args
    
    Returns:
        Dictionary with update status
    """
    config_path = Path.home() / ".config" / "claude" / "claude_config.json"
    
    try:
        # Read existing config
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {"mcpServers": {}}
        
        # Add new MCPs
        for mcp in mcps_to_add:
            name = mcp.get("name")
            if name and name not in config.get("mcpServers", {}):
                config.setdefault("mcpServers", {})[name] = {
                    "command": mcp.get("command", "npx"),
                    "args": mcp.get("args", ["-y", name])
                }
        
        # Write updated config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            "status": "success",
            "message": f"Added {len(mcps_to_add)} MCPs to configuration",
            "config_path": str(config_path),
            "added_mcps": [mcp.get("name") for mcp in mcps_to_add]
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update configuration: {str(e)}",
            "config_path": str(config_path)
        }

if __name__ == "__main__":
    # Start the FastMCP server
    mcp.run()