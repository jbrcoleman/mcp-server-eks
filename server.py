#!/usr/bin/env python3
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from pydantic import AnyUrl


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("eks-mcp-server")


@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri=AnyUrl("resource://cluster-info"),
            name="EKS Cluster Information",
            description="Information about the EKS cluster",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("resource://health"),
            name="Health Check",
            description="Server health status",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource."""
    if str(uri) == "resource://cluster-info":
        return json.dumps({
            "cluster_name": "mcp-eks-cluster",
            "region": "us-west-2",
            "status": "active",
            "version": "1.28"
        })
    elif str(uri) == "resource://health":
        return json.dumps({
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        })
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_cluster_status",
            description="Get the current status of the EKS cluster",
            inputSchema={
                "type": "object",
                "properties": {
                    "cluster_name": {
                        "type": "string",
                        "description": "Name of the EKS cluster",
                    }
                },
                "required": ["cluster_name"],
            },
        ),
        Tool(
            name="list_pods",
            description="List pods in a specific namespace",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace",
                        "default": "default",
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    if name == "get_cluster_status":
        cluster_name = arguments.get("cluster_name", "mcp-eks-cluster")
        result = {
            "cluster_name": cluster_name,
            "status": "active",
            "node_count": 3,
            "version": "1.28"
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "list_pods":
        namespace = arguments.get("namespace", "default")
        result = {
            "namespace": namespace,
            "pods": [
                {"name": "mcp-server-pod-1", "status": "Running"},
                {"name": "mcp-server-pod-2", "status": "Running"},
            ]
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the server."""
    logger.info("Starting MCP EKS Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="eks-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())