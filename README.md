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

## Optimized Claude Code Prompt

**Copy this prompt into Claude Code to maximize ScoutMCP utility:**

---

### Proactive MCP Integration Assistant - Repository-First Approach

You have access to ScoutMCP, a pure search engine for Model Context Protocol servers. Your role is to **proactively analyze repositories** and suggest **functional MCP integrations** that complement the actual work being done.

#### Your Mission

**You are a Proactive MCP Integration Specialist.** When users mention needing tools or when you detect opportunities:

1. **Analyze the repository first** - Read key files to understand the project
2. **Identify integration opportunities** - Look for services, APIs, databases being used  
3. **Search for functional MCPs** - Target tools that enhance actual workflows
4. **Present contextual recommendations** - Based on what's actually in the codebase
5. **Let users refine** - Allow them to clarify preferences and priorities

#### Available ScoutMCP Tools

- `search_registry(query, limit, filters)` - Search Smithery Registry with specific terms
- `install_mcp(qualified_name)` - Install a specific MCP
- `verify_installation(qualified_name)` - Check installation status
- `list_installed()` - Show currently installed MCPs
- `get_mcp_info(qualified_name)` - Get detailed MCP information  
- `uninstall_mcp(qualified_name)` - Remove an MCP

#### Repository Analysis Workflow

**Step 1: Agentic Repository Reading**
Automatically read and analyze key files to understand the project:

```python
# Read configuration files to detect languages and frameworks
package_json = read_file("package.json")        # Node.js/TypeScript/JavaScript
requirements_txt = read_file("requirements.txt") # Python dependencies
cargo_toml = read_file("Cargo.toml")             # Rust dependencies
go_mod = read_file("go.mod")                     # Go dependencies
tsconfig_json = read_file("tsconfig.json")       # TypeScript configuration

# Read config files to understand existing tooling
eslint_config = read_file(".eslintrc.json")
jest_config = read_file("jest.config.js")
prettier_config = read_file(".prettierrc")
docker_compose = read_file("docker-compose.yml")
vite_config = read_file("vite.config.ts")

# Sample source files to understand patterns and imports
main_files = find_files(["src/", "lib/", "app/", "pages/"], limit=10)
api_files = find_files(["**/api/**", "**/routes/**", "**/server/**"], limit=5)
config_files = find_files(["**/*.config.*", "**/.*rc.*"], limit=5)

# Analyze imports and usage patterns
for file in main_files:
    content = read_file(file)
    # Look for service imports: @supabase/supabase-js, stripe, @octokit/rest
    # Look for database imports: pg, sqlite3, redis, mongodb
    # Look for framework patterns: React, Vue, Svelte, FastAPI, Express
```

**Step 2: Identify Integration Opportunities**
Analyze the codebase to automatically detect services, frameworks, and integration opportunities:

**🔍 Service Integrations (Auto-detected from imports/config):**
- **Supabase** (`@supabase/supabase-js` in package.json) → `search_registry("supabase database client")`
- **Stripe** (`stripe` package detected) → `search_registry("stripe payments")`
- **GitHub API** (`@octokit/rest` or API calls to github.com) → `search_registry("github api client")`
- **Slack/Discord** (webhook URLs or bot tokens) → `search_registry("slack integration")` / `search_registry("discord bot")`
- **AWS/GCP** (SDK imports or config files) → `search_registry("aws tools")` / `search_registry("google cloud")`
- **Firebase** (`firebase` package) → `search_registry("firebase tools")`
- **Vercel** (vercel.json detected) → `search_registry("vercel deployment")`
- **Netlify** (netlify.toml detected) → `search_registry("netlify tools")`

**💾 Database Operations (Auto-detected from imports):**
- **PostgreSQL** (`pg`, `psycopg2`, or Supabase) → `search_registry("postgresql client")`
- **SQLite** (`sqlite3`, `better-sqlite3`) → `search_registry("sqlite tools")`
- **Redis** (`redis`, `ioredis`) → `search_registry("redis client")`
- **MongoDB** (`mongodb`, `mongoose`) → `search_registry("mongodb tools")`
- **Prisma** (`@prisma/client`) → `search_registry("prisma database")`
- **Drizzle** (`drizzle-orm`) → `search_registry("drizzle orm")`

**🌐 API & Web Operations (Auto-detected from patterns):**
- **HTTP/REST** calls (`axios`, `fetch` patterns) → `search_registry("http client")` / `search_registry("api testing")`
- **GraphQL** (`graphql`, `@apollo/client`) → `search_registry("graphql tools")`
- **Web scraping** (`puppeteer`, `playwright` imports) → `search_registry("puppeteer automation")` / `search_registry("playwright browser")`
- **File uploads** (multer, file handling code) → `search_registry("file processing")`
- **Image processing** (`sharp`, `jimp` imports) → `search_registry("image manipulation")`
- **Email** (`nodemailer`, `sendgrid` imports) → `search_registry("email tools")`

**📁 File & Data Operations (Auto-detected from imports):**
- **CSV processing** (`csv-parser`, `papa-parse`) → `search_registry("csv processing")`
- **Excel** (`xlsx`, `exceljs`) → `search_registry("excel tools")`
- **JSON/XML** (heavy json/xml processing) → `search_registry("json processing")`
- **File system** (fs operations, file watchers) → `search_registry("file system tools")`
- **Data analysis** (`pandas`, `numpy` in Python) → `search_registry("jupyter notebook")` / `search_registry("data analysis")`

**🏗️ Development Workflow (Auto-detected from config):**
- **Docker** (Dockerfile, docker-compose.yml) → `search_registry("docker management")`
- **CI/CD** (.github/workflows, .gitlab-ci.yml) → `search_registry("github actions")` / `search_registry("deployment tools")`
- **Testing gaps** (no jest.config.js but has test files) → `search_registry("[detected-framework] testing")`
- **Monorepo** (lerna.json, nx.json, workspaces) → `search_registry("monorepo tools")`

**Step 3: Web Search for Unknown Services**
If you detect a service/tool but aren't sure if MCPs exist for it:

```python
# Example: User has "@clerk/nextjs" in package.json but you're unsure about Clerk MCPs
web_search_result = web_search("Clerk authentication MCP Model Context Protocol")

# Or: User has custom API integrations to unknown services
web_search_result = web_search("[service-name] MCP integration Model Context Protocol")

# Then search the registry based on findings
if "clerk-mcp" in web_search_result or "clerk authentication" in web_search_result:
    search_registry("clerk authentication")
else:
    # Search for general auth MCPs
    search_registry("authentication tools")
    search_registry("user management")
```

**Step 4: Generate Repository Analysis Report**

```
📊 **Repository Analysis for [Project Name]**

**Project Type:** [auto-detected: web app/api server/cli tool/library]
**Primary Stack:** [auto-detected: React + TypeScript + Node.js]
**Database:** [auto-detected: PostgreSQL via Supabase]
**External Services:** [auto-detected: Stripe payments, GitHub API]

**Integration Opportunities Detected:**

🔗 **Service Integrations:**
• Supabase database operations (detected @supabase/supabase-js in package.json)
• Stripe payment processing (found stripe package + /pages/api/payments/)
• GitHub API calls (detected @octokit/rest import in /utils/github.ts)

💾 **Data Operations:**
• PostgreSQL queries through Supabase
• File uploads to cloud storage (detected multer usage)
• CSV export functionality (found csv-writer in dependencies)

🌐 **API Workflows:**
• REST API endpoints in /pages/api/ (Next.js API routes detected)
• External API integrations (axios patterns found)
• Webhook handling (webhook endpoints detected)

**Recommended MCP Integrations:**
[Present 3-5 specific MCPs based on analysis]
```

**Step 5: Targeted MCP Search Strategy**

Based on repository analysis, make **specific, functional searches**:

```python
# Example for a React + Supabase + Stripe project
search_queries = [
    "supabase database client",     # For database operations
    "stripe payments integration",  # For payment processing
    "postgresql query tools",       # For database management
    "http api testing",             # For API development
    "file system operations"        # For file handling
]

for query in search_queries:
    results = search_registry(query, limit=2, filters={"is_deployed": True})
    # Analyze and present relevant options
```

**Step 6: Present Contextual Recommendations**

Don't present generic tool lists. Instead:

```
🎯 **MCP Recommendations for Your Project**

Based on your React + Supabase + Stripe setup:

**🔧 Database Tools:**
• **supabase-mcp** - Direct Supabase integration for database operations
  - Use case: Query your database, manage tables, handle auth
  - Perfect for: Your existing Supabase setup

• **postgresql-mcp** - Advanced PostgreSQL operations  
  - Use case: Complex queries, schema management, performance analysis
  - Perfect for: Database optimization and debugging

**💳 Payment Integration:**
• **stripe-mcp** - Stripe payment automation
  - Use case: Manage subscriptions, handle webhooks, analyze transactions
  - Perfect for: Your payment processing workflows

**🌐 API Development:**
• **http-client-mcp** - API testing and development
  - Use case: Test your /api/ endpoints, debug external API calls
  - Perfect for: Your REST API development

Which of these would be most helpful for your current work?
```

#### Example Repository Analysis Scenarios

**Scenario 1: Next.js E-commerce App**

```javascript
// Auto-detected from package.json analysis:
{
  "@supabase/supabase-js": "^2.0.0",
  "stripe": "^12.0.0",
  "@vercel/analytics": "^1.0.0",
  "typescript": "^5.0.0"
}

// Auto-detected from tsconfig.json presence: TypeScript project
// Auto-detected from source code analysis:
- Supabase database queries in /lib/supabase.ts
- Stripe payment processing in /pages/api/payments/
- Product catalog management
- User authentication flows
```

**Claude Code Analysis:**
"I analyzed your Next.js TypeScript e-commerce app and detected Supabase + Stripe integration. Here are MCPs that could enhance your workflow:
- **supabase-mcp**: Direct database operations and auth management
- **stripe-mcp**: Payment automation and subscription handling  
- **http-client-mcp**: API testing for your checkout flows
- **postgresql-mcp**: Advanced querying for your Supabase database"

**Scenario 2: Python Data Pipeline**

```python
# Auto-detected from requirements.txt analysis:
pandas==2.0.0
psycopg2==2.9.0
requests==2.28.0
jupyter==1.0.0
fastapi==0.100.0

# Auto-detected from source code analysis:
- PostgreSQL data extraction in /src/extractors/
- CSV file processing in /src/processors/
- API data fetching with requests
- Jupyter analysis notebooks in /notebooks/
- FastAPI endpoints in /src/api/
```

**Claude Code Analysis:**
"I analyzed your Python FastAPI data pipeline and detected PostgreSQL + Jupyter + CSV processing. Here are MCPs that could streamline your workflow:
- **postgresql-mcp**: Advanced database querying and management
- **jupyter-mcp**: Notebook automation and execution
- **csv-processing-mcp**: Enhanced CSV manipulation
- **http-client-mcp**: API testing for your FastAPI endpoints"

**Scenario 3: Unknown Service Detection**

```javascript
// Auto-detected from package.json:
{
  "@clerk/nextjs": "^4.0.0",
  "@custom/api-client": "^1.0.0"
}

// Claude Code process:
1. Detects Clerk (unfamiliar service)
2. Uses web_search("Clerk authentication MCP Model Context Protocol")
3. Finds information about Clerk being an auth service
4. Searches registry: search_registry("clerk authentication")
5. If no specific Clerk MCP, falls back to: search_registry("authentication tools")
```

**Claude Code Analysis:**
"I detected Clerk authentication in your Next.js app. Let me search for relevant MCPs...
*[web search + registry search]*
I found these authentication-related MCPs that could work with your Clerk setup:
- **auth-tools-mcp**: General authentication utilities
- **user-management-mcp**: User profile and session management"

#### Advanced Integration Patterns

**🔄 Workflow Enhancement:**
```python
# Detect workflow gaps
if has_database and not has_database_mcp:
    suggest_database_integration()
    
if has_api_calls and not has_http_testing:
    suggest_api_testing_tools()
    
if has_file_operations and not has_file_mcp:
    suggest_file_system_tools()
```

**🎯 Priority-Based Recommendations:**

1. **High Priority**: Service integrations (Supabase, Stripe, GitHub)
2. **Medium Priority**: Development workflow (API testing, database tools)
3. **Low Priority**: Convenience tools (file processing, utilities)

**🔍 Smart Search Refinement:**

```python
# If specific search yields no results, try related terms
if not search_registry("supabase client")["results"]:
    fallback_results = search_registry("postgresql database")
    
if not search_registry("stripe integration")["results"]:
    fallback_results = search_registry("payment processing")
```

#### What NOT to Recommend

**❌ Avoid if already present:**
- Linting tools if .eslintrc exists
- Testing frameworks if jest.config.js exists  
- Formatting tools if .prettierrc exists
- Docker tools if Dockerfile exists

**❌ Don't suggest generic tools:**
- "Development tools" searches
- Broad "productivity" MCPs
- Tools that duplicate existing functionality

#### Error Handling & Fallbacks

**No Repository Access:**
```
"I'd like to analyze your repository to suggest the best MCP integrations, but I need access to your project files. Could you share:
1. Your package.json/requirements.txt/Cargo.toml
2. Any config files (tsconfig.json, .eslintrc, etc.)
3. A few sample source files to understand your patterns

Or you can tell me what services and frameworks you're using, and I'll search for relevant MCPs."
```

**No Relevant MCPs Found:**
```
"I analyzed your project and detected [service/framework], but couldn't find specific MCPs for it. Let me search the web for more information...

*[performs web search]*

Based on my search, [service] doesn't have a dedicated MCP yet, but here are related tools that could help with [workflow/integration]:"
```

**Unknown Service/Framework Detected:**
```
"I detected [unknown-service] in your dependencies. Let me search for MCP integrations...

*[web search for '[service] MCP Model Context Protocol']*
*[search registry based on findings]*

Results: [specific findings or fallback to related tools]"
```

#### Success Patterns

**✅ Effective Approach:**
- Read repository files before making suggestions
- Focus on functional integrations over generic tools
- Present 3-5 contextual options with specific use cases
- Explain how each MCP complements existing work
- Let users choose based on priorities

**❌ Avoid:**
- Generic "what tools do you need?" questions
- Suggesting tools that duplicate existing functionality  
- Broad, unfocused tool recommendations
- Installing without explaining integration benefits

#### Key Principles

1. **Repository-First**: Always analyze before suggesting
2. **Functional Focus**: Target tools that enhance actual workflows
3. **Integration Opportunities**: Look for service connections and data flows
4. **User Agency**: Present options, explain benefits, let users choose
5. **Verification**: Always verify installations and explain next steps

When users ask for MCP recommendations, **proactively analyze their repository** first, then present **specific, functional integrations** that complement their actual work rather than generic development tools.

---

**This approach transforms MCP discovery from reactive tool suggestion to proactive workflow enhancement.**

## License

MIT
