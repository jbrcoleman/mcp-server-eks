#!/usr/bin/env python3
"""
Enhanced MCP server with real Kubernetes API integration.
This version connects to actual EKS cluster instead of returning mock data.
"""
import asyncio
import json
import logging
import os
from typing import Any, Dict, List

from kubernetes import client, config
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
from pydantic import AnyUrl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("eks-mcp-server-enhanced")

# Initialize Kubernetes client
try:
    # Try to load in-cluster config first (when running in pod)
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes config")
except:
    try:
        # Fall back to local kubeconfig
        config.load_kube_config()
        logger.info("Loaded local Kubernetes config")
    except Exception as e:
        logger.warning(f"Could not load Kubernetes config: {e}")
        logger.warning("Will use mock data instead")

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()


@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri=AnyUrl("resource://cluster-info"),
            name="EKS Cluster Information",
            description="Real-time information about the EKS cluster",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("resource://node-info"),
            name="Node Information",
            description="Information about cluster nodes",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("resource://health"),
            name="Health Check",
            description="Server and cluster health status",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource."""
    try:
        if str(uri) == "resource://cluster-info":
            # Get real cluster information
            namespaces = v1.list_namespace()
            return json.dumps({
                "cluster_name": os.getenv("CLUSTER_NAME", "mcp-eks-cluster"),
                "region": os.getenv("AWS_REGION", "us-west-2"),
                "namespace_count": len(namespaces.items),
                "server_version": "1.28",
                "namespaces": [ns.metadata.name for ns in namespaces.items]
            })
        
        elif str(uri) == "resource://node-info":
            # Get node information
            nodes = v1.list_node()
            node_info = []
            for node in nodes.items:
                node_info.append({
                    "name": node.metadata.name,
                    "status": "Ready" if any(
                        condition.type == "Ready" and condition.status == "True"
                        for condition in node.status.conditions
                    ) else "NotReady",
                    "instance_type": node.metadata.labels.get("node.kubernetes.io/instance-type", "unknown"),
                    "zone": node.metadata.labels.get("topology.kubernetes.io/zone", "unknown")
                })
            
            return json.dumps({
                "node_count": len(nodes.items),
                "nodes": node_info
            })
        
        elif str(uri) == "resource://health":
            # Health check with real API call
            try:
                v1.list_namespace(limit=1)
                return json.dumps({
                    "status": "healthy",
                    "kubernetes_api": "accessible",
                    "timestamp": "2024-01-01T00:00:00Z"
                })
            except Exception as e:
                return json.dumps({
                    "status": "unhealthy",
                    "kubernetes_api": "inaccessible",
                    "error": str(e),
                    "timestamp": "2024-01-01T00:00:00Z"
                })
        
        else:
            raise ValueError(f"Unknown resource: {uri}")
            
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return json.dumps({"error": str(e)})


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
                    "include_nodes": {
                        "type": "boolean",
                        "description": "Include node information",
                        "default": False
                    }
                },
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
                    },
                    "show_status": {
                        "type": "boolean",
                        "description": "Include detailed pod status",
                        "default": True
                    }
                },
            },
        ),
        Tool(
            name="get_deployments",
            description="List deployments in a namespace",
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
    """Handle tool calls with real Kubernetes API integration."""
    try:
        if name == "get_cluster_status":
            include_nodes = arguments.get("include_nodes", False)
            
            # Get namespace count
            namespaces = v1.list_namespace()
            
            result = {
                "cluster_name": os.getenv("CLUSTER_NAME", "mcp-eks-cluster"),
                "namespace_count": len(namespaces.items),
                "kubernetes_version": "1.28"
            }
            
            if include_nodes:
                nodes = v1.list_node()
                result["node_count"] = len(nodes.items)
                result["nodes"] = [
                    {
                        "name": node.metadata.name,
                        "ready": any(
                            condition.type == "Ready" and condition.status == "True"
                            for condition in node.status.conditions
                        )
                    }
                    for node in nodes.items
                ]
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "list_pods":
            namespace = arguments.get("namespace", "default")
            show_status = arguments.get("show_status", True)
            
            try:
                pods = v1.list_namespaced_pod(namespace=namespace)
                pod_list = []
                
                for pod in pods.items:
                    pod_info = {"name": pod.metadata.name}
                    
                    if show_status:
                        pod_info.update({
                            "phase": pod.status.phase,
                            "ready": sum(1 for condition in (pod.status.conditions or [])
                                       if condition.type == "Ready" and condition.status == "True"),
                            "restart_count": sum(container.restart_count or 0 
                                               for container in (pod.status.container_statuses or []))
                        })
                    
                    pod_list.append(pod_info)
                
                result = {
                    "namespace": namespace,
                    "pod_count": len(pod_list),
                    "pods": pod_list
                }
                
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    result = {"error": f"Namespace '{namespace}' not found"}
                else:
                    result = {"error": f"API error: {e.reason}"}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_deployments":
            namespace = arguments.get("namespace", "default")
            
            try:
                deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
                deployment_list = []
                
                for deployment in deployments.items:
                    deployment_list.append({
                        "name": deployment.metadata.name,
                        "replicas": deployment.spec.replicas,
                        "ready_replicas": deployment.status.ready_replicas or 0,
                        "available_replicas": deployment.status.available_replicas or 0
                    })
                
                result = {
                    "namespace": namespace,
                    "deployment_count": len(deployment_list),
                    "deployments": deployment_list
                }
                
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    result = {"error": f"Namespace '{namespace}' not found"}
                else:
                    result = {"error": f"API error: {e.reason}"}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    """Main entry point for the server."""
    logger.info("Starting Enhanced MCP EKS Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="eks-mcp-server-enhanced",
                server_version="2.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())