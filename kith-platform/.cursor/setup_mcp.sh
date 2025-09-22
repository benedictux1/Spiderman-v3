#!/bin/bash

# Setup Render MCP Server for Cursor
echo "Setting up Render MCP Server..."

# Navigate to the .cursor directory
cd "$(dirname "$0")"

# Install Node.js dependencies
echo "Installing MCP dependencies..."
npm install

# Make the server executable
chmod +x mcp_render_server.js

echo "✅ Render MCP Server setup complete!"
echo ""
echo "To use this MCP in Cursor:"
echo "1. Open Cursor settings"
echo "2. Go to Extensions > MCP"
echo "3. Add the configuration from mcp_render_config.json"
echo "4. Restart Cursor"
echo ""
echo "Available tools:"
echo "- render_list_services: List all your Render services"
echo "- render_get_service: Get details of a specific service"
echo "- render_deploy_service: Trigger a new deployment"
echo "- render_get_deployments: View deployment history"
echo "- render_get_logs: Get service logs"
