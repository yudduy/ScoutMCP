#!/bin/bash

echo "🚀 MCP Scout Quick Test & Setup Guide"
echo "======================================"
echo ""

# Test 1: Check if server runs
echo "1️⃣  Testing if MCP Scout server starts..."
export SMITHERY_API_KEY="655e59f7-df1e-4598-814c-6fa08f7a501c"
timeout 2 python server.py 2>/dev/null
if [ $? -eq 124 ]; then
    echo "   ✅ Server starts successfully"
else
    echo "   ❌ Server failed to start"
fi

echo ""
echo "2️⃣  Checking Claude Code configuration..."
CONFIG_PATH="$HOME/.config/claude/claude_config.json"
if [ -f "$CONFIG_PATH" ]; then
    echo "   ✅ Claude config exists at: $CONFIG_PATH"
else
    echo "   ℹ️  Claude config not found. Creating example..."
    mkdir -p "$HOME/.config/claude"
    cat > "$HOME/.config/claude/claude_config_example.json" << 'EOF'
{
  "mcpServers": {
    "mcp-scout": {
      "command": "python",
      "args": ["/Users/duy/Documents/build/mcp-mount/server.py"],
      "env": {
        "SMITHERY_API_KEY": "655e59f7-df1e-4598-814c-6fa08f7a501c"
      }
    }
  }
}
EOF
    echo "   📄 Example config created at: $HOME/.config/claude/claude_config_example.json"
fi

echo ""
echo "3️⃣  To integrate with Claude Code:"
echo ""
echo "   Add this to your ~/.config/claude/claude_config.json:"
echo ""
echo '   {
     "mcpServers": {
       "mcp-scout": {
         "command": "python",
         "args": ["'$(pwd)/server.py'"],
         "env": {
           "SMITHERY_API_KEY": "your-api-key-here"
         }
       }
     }
   }'

echo ""
echo "4️⃣  Available MCP Scout tools:"
echo "   • find_mcp - Search for MCPs by query"
echo "   • find_and_install_mcp - Find and install MCPs"
echo "   • analyze_and_recommend_mcps - Get recommendations from codebase analysis"
echo "   • batch_install_mcps - Install multiple MCPs at once"
echo "   • get_installed_mcps - Check what's already installed"
echo "   • update_claude_config - Update Claude configuration"

echo ""
echo "5️⃣  Example usage in Claude Code:"
echo '   "Find an MCP for web search"'
echo '   "Analyze this project and recommend MCPs"'
echo '   "Install database tools for this project"'

echo ""
echo "✅ Setup guide complete!"