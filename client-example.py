#!/usr/bin/env python3
"""
Example MCP client to interact with the EKS MCP server.
This demonstrates how to connect to and use the MCP server.
"""
import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client


async def run_mcp_client():
    """Connect to MCP server and demonstrate usage."""
    
    # Start the MCP server process
    server_process = subprocess.Popen(
        [sys.executable, "server-enhanced.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Connect to the server
        async with stdio_client(server_process) as (read, write):
            async with ClientSession(read, write) as session:
                
                # Initialize the session
                await session.initialize()
                
                print("🚀 Connected to MCP EKS Server!")
                print("=" * 50)
                
                # List available resources
                print("\n📋 Available Resources:")
                resources = await session.list_resources()
                for resource in resources.resources:
                    print(f"  • {resource.name}: {resource.description}")
                
                # Read cluster info resource
                print("\n🏗️  Reading cluster information...")
                cluster_info = await session.read_resource("resource://cluster-info")
                print(f"  {cluster_info.contents[0].text}")
                
                # Read health resource
                print("\n💚 Checking server health...")
                health = await session.read_resource("resource://health")
                print(f"  {health.contents[0].text}")
                
                # List available tools
                print("\n🔧 Available Tools:")
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"  • {tool.name}: {tool.description}")
                
                # Call get_cluster_status tool
                print("\n📊 Getting cluster status...")
                result = await session.call_tool(
                    "get_cluster_status",
                    {"cluster_name": "mcp-eks-cluster"}
                )
                print(f"  {result.content[0].text}")
                
                # Call list_pods tool
                print("\n🐳 Listing pods in default namespace...")
                result = await session.call_tool(
                    "list_pods",
                    {"namespace": "default"}
                )
                print(f"  {result.content[0].text}")
                
                # Call list_pods tool for mcp-server namespace
                print("\n🐳 Listing pods in mcp-server namespace...")
                result = await session.call_tool(
                    "list_pods",
                    {"namespace": "mcp-server"}
                )
                print(f"  {result.content[0].text}")
                
                print("\n✅ MCP Client demo completed successfully!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        if server_process:
            server_process.terminate()
            server_process.wait()


if __name__ == "__main__":
    asyncio.run(run_mcp_client())