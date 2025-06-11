#!/usr/bin/env python3
"""
MCP Server bridge that connects Claude Desktop to the HTTP API.
This enables natural language queries about your EKS cluster.
"""
import asyncio
import json
import logging
import os
import requests
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, 
    ServerCapabilities, ResourcesCapability, ToolsCapability
)
from pydantic import AnyUrl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("eks-mcp-bridge")

# MCP Server HTTP API endpoint
MCP_API_BASE = os.getenv("MCP_API_BASE", "http://a51a58f78b8f84a278b1fe7ddc9aadde-1713856781.us-east-1.elb.amazonaws.com")

def call_mcp_api(endpoint: str) -> Dict[str, Any]:
    """Call the MCP HTTP API."""
    try:
        url = f"{MCP_API_BASE}{endpoint}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error calling MCP API {endpoint}: {e}")
        return {"error": str(e)}

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri=AnyUrl("resource://cluster-status"),
            name="EKS Cluster Status",
            description="Real-time status of your EKS cluster including nodes and health",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("resource://pod-status"),
            name="Pod Status",
            description="Status of all pods across namespaces",
            mimeType="application/json",
        ),
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource."""
    if str(uri) == "resource://cluster-status":
        cluster_info = call_mcp_api("/cluster-info")
        nodes = call_mcp_api("/nodes")
        health = call_mcp_api("/health")
        
        status = {
            "cluster": cluster_info,
            "nodes": nodes,
            "health": health
        }
        return json.dumps(status, indent=2)
    
    elif str(uri) == "resource://pod-status":
        mcp_pods = call_mcp_api("/pods?namespace=mcp-server")
        default_pods = call_mcp_api("/pods?namespace=default")
        karpenter_pods = call_mcp_api("/pods?namespace=karpenter")
        
        status = {
            "mcp_server": mcp_pods,
            "default": default_pods,
            "karpenter": karpenter_pods
        }
        return json.dumps(status, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="check_cluster_health",
            description="Check the overall health of your EKS cluster",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_node_info",
            description="Get detailed information about cluster nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_karpenter_only": {
                        "type": "boolean",
                        "description": "Show only Karpenter-managed nodes",
                        "default": False
                    }
                },
            },
        ),
        Tool(
            name="check_pods",
            description="Check the status of pods in a specific namespace",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace to check",
                        "default": "mcp-server",
                    }
                },
            },
        ),
        Tool(
            name="get_deployments",
            description="Get deployment status and replica information",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace to check",
                        "default": "default",
                    }
                },
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls with natural language responses."""
    
    if name == "check_cluster_health":
        health = call_mcp_api("/health")
        cluster_info = call_mcp_api("/cluster-info")
        nodes = call_mcp_api("/nodes")
        
        if health.get("status") == "healthy":
            response = f"""✅ Your EKS cluster '{cluster_info.get('cluster_name', 'unknown')}' is healthy!

🏗️ Cluster: {cluster_info.get('cluster_name')} in {cluster_info.get('region')}
📊 Namespaces: {cluster_info.get('namespace_count', 0)}
🖥️ Nodes: {nodes.get('node_count', 0)} total
   • Ready nodes: {len([n for n in nodes.get('nodes', []) if n.get('status') == 'Ready'])}
   • Karpenter nodes: {len([n for n in nodes.get('nodes', []) if n.get('instance_type') != 't3.medium'])}

🔗 Kubernetes API: {health.get('kubernetes_api', 'unknown')}"""
        else:
            response = f"❌ Cluster health check failed: {health.get('error', 'Unknown error')}"
        
        return [TextContent(type="text", text=response)]
    
    elif name == "get_node_info":
        include_karpenter_only = arguments.get("include_karpenter_only", False)
        nodes = call_mcp_api("/nodes")
        
        if "error" in nodes:
            return [TextContent(type="text", text=f"❌ Error getting node info: {nodes['error']}")]
        
        node_list = nodes.get("nodes", [])
        if include_karpenter_only:
            # Filter for non-t3.medium instances (Karpenter managed)
            node_list = [n for n in node_list if n.get('instance_type') != 't3.medium']
        
        response = f"🖥️ Your cluster has {len(node_list)} {'Karpenter-managed ' if include_karpenter_only else ''}nodes:\n\n"
        
        for node in node_list:
            status_emoji = "✅" if node.get('status') == 'Ready' else "❌"
            response += f"{status_emoji} {node.get('name', 'unknown')}\n"
            response += f"   • Type: {node.get('instance_type', 'unknown')}\n"
            response += f"   • Zone: {node.get('zone', 'unknown')}\n"
            response += f"   • Status: {node.get('status', 'unknown')}\n\n"
        
        return [TextContent(type="text", text=response)]
    
    elif name == "check_pods":
        namespace = arguments.get("namespace", "mcp-server")
        pods = call_mcp_api(f"/pods?namespace={namespace}")
        
        if "error" in pods:
            return [TextContent(type="text", text=f"❌ Error checking pods in {namespace}: {pods['error']}")]
        
        pod_count = pods.get("pod_count", 0)
        pod_list = pods.get("pods", [])
        
        response = f"🐳 Pods in '{namespace}' namespace: {pod_count} total\n\n"
        
        if pod_count == 0:
            response += "No pods found in this namespace."
        else:
            for pod in pod_list:
                status_emoji = "✅" if pod.get('phase') == 'Running' and pod.get('ready') > 0 else "❌"
                response += f"{status_emoji} {pod.get('name', 'unknown')}\n"
                response += f"   • Phase: {pod.get('phase', 'unknown')}\n"
                response += f"   • Ready: {pod.get('ready', 0)}/1\n"
                response += f"   • Restarts: {pod.get('restart_count', 0)}\n\n"
        
        return [TextContent(type="text", text=response)]
    
    elif name == "get_deployments":
        namespace = arguments.get("namespace", "default")
        deployments = call_mcp_api(f"/deployments?namespace={namespace}")
        
        if "error" in deployments:
            return [TextContent(type="text", text=f"❌ Error getting deployments in {namespace}: {deployments['error']}")]
        
        deployment_count = deployments.get("deployment_count", 0)
        deployment_list = deployments.get("deployments", [])
        
        response = f"🚀 Deployments in '{namespace}' namespace: {deployment_count} total\n\n"
        
        if deployment_count == 0:
            response += "No deployments found in this namespace."
        else:
            for deployment in deployment_list:
                replicas = deployment.get('replicas', 0)
                ready = deployment.get('ready_replicas', 0)
                available = deployment.get('available_replicas', 0)
                
                status_emoji = "✅" if ready == replicas and available == replicas else "⚠️"
                response += f"{status_emoji} {deployment.get('name', 'unknown')}\n"
                response += f"   • Desired: {replicas}\n"
                response += f"   • Ready: {ready}\n"
                response += f"   • Available: {available}\n\n"
        
        return [TextContent(type="text", text=response)]
    
    else:
        return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]

async def main():
    """Main entry point for the server."""
    logger.info("Starting MCP-Claude Bridge Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="eks-mcp-bridge",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    resources=ResourcesCapability(subscribe=False, listChanged=False),
                    tools=ToolsCapability(),
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())