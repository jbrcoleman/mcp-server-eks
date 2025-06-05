# Integrating MCP Server with Claude Desktop

## Step 1: Install Claude Desktop
Download and install Claude Desktop from https://claude.ai/download

## Step 2: Configure MCP Server

1. **Copy the configuration**:
   ```bash
   # On macOS
   cp claude-desktop-config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   # On Linux
   cp claude-desktop-config.json ~/.config/Claude/claude_desktop_config.json
   
   # On Windows
   copy claude-desktop-config.json %APPDATA%\Claude\claude_desktop_config.json
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Restart Claude Desktop**

## Step 3: Test the Integration

Once configured, Claude Desktop will automatically connect to your MCP server. You can then:

1. Ask Claude: "What EKS clusters do you have access to?"
2. Ask Claude: "Can you check the health of my EKS cluster?"
3. Ask Claude: "List the pods in the mcp-server namespace"

## Step 4: Verify Connection

In Claude Desktop, you should see:
- A new "eks-cluster" tool available
- Ability to query cluster information
- Access to pod listing functionality

## Troubleshooting

If the connection fails:
1. Check that Python and dependencies are installed
2. Verify the server.py path in the config
3. Check Claude Desktop logs for errors
4. Test the server directly with: `python server.py`