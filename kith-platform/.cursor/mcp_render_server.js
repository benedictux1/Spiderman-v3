#!/usr/bin/env node

/**
 * Render MCP Server for Cursor
 * Provides Render API integration for deployment management
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');

class RenderMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'render-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.renderApiToken = process.env.RENDER_API_TOKEN;
    this.renderApiBase = 'https://api.render.com/v1';

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'render_list_services',
            description: 'List all Render services',
            inputSchema: {
              type: 'object',
              properties: {
                limit: {
                  type: 'number',
                  description: 'Number of services to return (default: 20)',
                  default: 20
                }
              }
            }
          },
          {
            name: 'render_get_service',
            description: 'Get details of a specific Render service',
            inputSchema: {
              type: 'object',
              properties: {
                serviceId: {
                  type: 'string',
                  description: 'The service ID to get details for'
                }
              },
              required: ['serviceId']
            }
          },
          {
            name: 'render_deploy_service',
            description: 'Trigger a new deployment for a service',
            inputSchema: {
              type: 'object',
              properties: {
                serviceId: {
                  type: 'string',
                  description: 'The service ID to deploy'
                }
              },
              required: ['serviceId']
            }
          },
          {
            name: 'render_get_deployments',
            description: 'Get deployment history for a service',
            inputSchema: {
              type: 'object',
              properties: {
                serviceId: {
                  type: 'string',
                  description: 'The service ID to get deployments for'
                },
                limit: {
                  type: 'number',
                  description: 'Number of deployments to return (default: 10)',
                  default: 10
                }
              },
              required: ['serviceId']
            }
          },
          {
            name: 'render_get_logs',
            description: 'Get logs for a service',
            inputSchema: {
              type: 'object',
              properties: {
                serviceId: {
                  type: 'string',
                  description: 'The service ID to get logs for'
                },
                limit: {
                  type: 'number',
                  description: 'Number of log entries to return (default: 100)',
                  default: 100
                }
              },
              required: ['serviceId']
            }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'render_list_services':
            return await this.listServices(args.limit || 20);
          
          case 'render_get_service':
            return await this.getService(args.serviceId);
          
          case 'render_deploy_service':
            return await this.deployService(args.serviceId);
          
          case 'render_get_deployments':
            return await this.getDeployments(args.serviceId, args.limit || 10);
          
          case 'render_get_logs':
            return await this.getLogs(args.serviceId, args.limit || 100);
          
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`
            }
          ],
          isError: true
        };
      }
    });
  }

  setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  async makeRenderRequest(endpoint, method = 'GET', body = null) {
    const url = `${this.renderApiBase}${endpoint}`;
    const options = {
      method,
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${this.renderApiToken}`,
        'Content-Type': 'application/json'
      }
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`Render API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  async listServices(limit) {
    const data = await this.makeRenderRequest(`/services?limit=${limit}`);
    
    const services = data.map(service => ({
      id: service.id,
      name: service.name,
      type: service.type,
      servicePath: service.servicePath,
      repo: service.repo,
      branch: service.branch,
      region: service.region,
      plan: service.plan,
      healthCheckPath: service.healthCheckPath,
      createdAt: service.createdAt,
      updatedAt: service.updatedAt
    }));

    return {
      content: [
        {
          type: 'text',
          text: `Found ${services.length} Render services:\n\n${services.map(s => 
            `• ${s.name} (${s.id})\n  Type: ${s.type}\n  Branch: ${s.branch}\n  Region: ${s.region}\n  Plan: ${s.plan}`
          ).join('\n\n')}`
        }
      ]
    };
  }

  async getService(serviceId) {
    const service = await this.makeRenderRequest(`/services/${serviceId}`);
    
    return {
      content: [
        {
          type: 'text',
          text: `Service Details: ${service.name}\n\n` +
                `ID: ${service.id}\n` +
                `Type: ${service.type}\n` +
                `Repository: ${service.repo}\n` +
                `Branch: ${service.branch}\n` +
                `Region: ${service.region}\n` +
                `Plan: ${service.plan}\n` +
                `Health Check: ${service.healthCheckPath || 'None'}\n` +
                `Created: ${service.createdAt}\n` +
                `Updated: ${service.updatedAt}`
        }
      ]
    };
  }

  async deployService(serviceId) {
    const deployment = await this.makeRenderRequest(`/services/${serviceId}/deploys`, 'POST');
    
    return {
      content: [
        {
          type: 'text',
          text: `Deployment triggered successfully!\n\n` +
                `Deployment ID: ${deployment.id}\n` +
                `Status: ${deployment.status}\n` +
                `Created: ${deployment.createdAt}`
        }
      ]
    };
  }

  async getDeployments(serviceId, limit) {
    const data = await this.makeRenderRequest(`/services/${serviceId}/deploys?limit=${limit}`);
    
    const deployments = data.map(deploy => ({
      id: deploy.id,
      status: deploy.status,
      commit: deploy.commit?.id || 'N/A',
      message: deploy.commit?.message || 'N/A',
      createdAt: deploy.createdAt
    }));

    return {
      content: [
        {
          type: 'text',
          text: `Deployment History (${deployments.length} deployments):\n\n${deployments.map(d => 
            `• ${d.id} - ${d.status}\n  Commit: ${d.commit}\n  Message: ${d.message}\n  Created: ${d.createdAt}`
          ).join('\n\n')}`
        }
      ]
    };
  }

  async getLogs(serviceId, limit) {
    const data = await this.makeRenderRequest(`/services/${serviceId}/logs?limit=${limit}`);
    
    return {
      content: [
        {
          type: 'text',
          text: `Service Logs (${data.length} entries):\n\n${data.map(log => 
            `${log.timestamp} - ${log.level}: ${log.message}`
          ).join('\n')}`
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Render MCP server running on stdio');
  }
}

const server = new RenderMCPServer();
server.run().catch(console.error);
