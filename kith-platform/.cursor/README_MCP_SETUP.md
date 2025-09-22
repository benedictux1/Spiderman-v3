# Render MCP Setup for Cursor

This setup provides Render API integration directly in Cursor, allowing you to manage your deployments without leaving the IDE.

## 🚀 Quick Setup

1. **Install dependencies:**
   ```bash
   cd .cursor
   ./setup_mcp.sh
   ```

2. **Configure Cursor:**
   - Open Cursor Settings (Cmd/Ctrl + ,)
   - Go to "Extensions" → "MCP"
   - Click "Add MCP Server"
   - Use the configuration from `mcp_render_config.json`

3. **Restart Cursor**

## 🛠️ Available Tools

### `render_list_services`
List all your Render services
```json
{
  "limit": 20
}
```

### `render_get_service`
Get detailed information about a specific service
```json
{
  "serviceId": "srv-abc123"
}
```

### `render_deploy_service`
Trigger a new deployment for a service
```json
{
  "serviceId": "srv-abc123"
}
```

### `render_get_deployments`
View deployment history for a service
```json
{
  "serviceId": "srv-abc123",
  "limit": 10
}
```

### `render_get_logs`
Get recent logs for a service
```json
{
  "serviceId": "srv-abc123",
  "limit": 100
}
```

## 🔧 Configuration

The MCP server uses your Render API token: `rnd_gsEOjPqytT1uD3OGpwec0W3kSgdY`

## 📋 Usage Examples

### List Your Services
Ask Cursor: "Show me all my Render services"

### Deploy Your Kith Platform
Ask Cursor: "Deploy my Kith Platform service"

### Check Deployment Status
Ask Cursor: "Show me the deployment history for my Kith Platform"

### View Logs
Ask Cursor: "Show me the recent logs for my Kith Platform service"

## 🔍 Troubleshooting

### If MCP doesn't work:
1. Check that Node.js is installed (`node --version`)
2. Verify dependencies are installed (`cd .cursor && npm list`)
3. Check Cursor's MCP settings
4. Restart Cursor completely

### If API calls fail:
1. Verify your Render API token is correct
2. Check that you have the necessary permissions
3. Ensure your service IDs are valid

## 🎯 Benefits for Your Kith Platform

With this MCP setup, you can:
- ✅ Deploy your UX improvements directly from Cursor
- ✅ Monitor deployment status in real-time
- ✅ View logs to debug issues
- ✅ Manage multiple services from one place
- ✅ Trigger deployments after code changes

## 🔐 Security

Your Render API token is stored in the environment variable and is only used for Render API calls. The token is not logged or transmitted elsewhere.
