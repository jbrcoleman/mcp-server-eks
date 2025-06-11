#!/usr/bin/env python3
"""
Demonstration of natural language queries that would be possible with Claude Desktop + MCP
"""
import requests
import json

def simulate_natural_language_query():
    print("=== Natural Language Query Demo ===")
    print()
    
    base_url = 'http://a51a58f78b8f84a278b1fe7ddc9aadde-1713856781.us-east-1.elb.amazonaws.com'
    
    # Query 1: "How is my cluster doing?"
    print('👤 You: "How is my cluster doing?"')
    print('🤖 Claude (via MCP): ')
    
    health = requests.get(f'{base_url}/health').json()
    cluster = requests.get(f'{base_url}/cluster-info').json()
    nodes = requests.get(f'{base_url}/nodes').json()
    
    if health.get('status') == 'healthy':
        node_list = nodes.get('nodes', [])
        karpenter_count = sum(1 for n in node_list if n.get('instance_type') != 't3.medium')
        
        print(f'   ✅ Your cluster "{cluster.get("cluster_name")}" is running perfectly!')
        print(f'   📊 {cluster.get("namespace_count")} namespaces are active')
        print(f'   🖥️  {nodes.get("node_count")} nodes are ready and healthy')
        print(f'   ⚡ {karpenter_count} Karpenter-managed nodes providing auto-scaling')
        print(f'   🌐 Located in {cluster.get("region")}')
    else:
        print('   ❌ Your cluster has some issues that need attention')
    
    print()
    
    # Query 2: "Are my MCP server pods running?"
    print('👤 You: "Are my MCP server pods running?"')
    print('🤖 Claude (via MCP): ')
    
    pods = requests.get(f'{base_url}/pods?namespace=mcp-server').json()
    pod_list = pods.get('pods', [])
    healthy_pods = [p for p in pod_list if p.get('phase') == 'Running' and p.get('ready') > 0]
    
    print(f'   🐳 You have {len(pod_list)} MCP server pods')
    if len(healthy_pods) == len(pod_list) and len(pod_list) > 0:
        print(f'   ✅ All {len(healthy_pods)} pods are running and ready!')
        for pod in healthy_pods:
            print(f'      • {pod.get("name")} - {pod.get("restart_count")} restarts')
    else:
        print(f'   ⚠️  Only {len(healthy_pods)}/{len(pod_list)} pods are healthy')
    
    print()
    
    # Query 3: "What Karpenter nodes do I have?"
    print('👤 You: "What Karpenter nodes do I have?"')
    print('🤖 Claude (via MCP): ')
    
    karpenter_nodes = [n for n in node_list if n.get('instance_type') != 't3.medium']
    
    if karpenter_nodes:
        print(f'   🚀 Karpenter has provisioned {len(karpenter_nodes)} nodes for you:')
        for node in karpenter_nodes:
            print(f'      • {node.get("name")} - {node.get("instance_type")} in {node.get("zone")}')
        print(f'   💰 This is saving costs by using spot instances and auto-scaling!')
    else:
        print('   📋 No Karpenter-managed nodes found (only static managed node group)')
    
    print()
    
    # Query 4: "Show me all my cluster namespaces"
    print('👤 You: "Show me all my cluster namespaces"')
    print('🤖 Claude (via MCP): ')
    
    namespaces = cluster.get('namespaces', [])
    print(f'   📂 Your cluster has {len(namespaces)} namespaces:')
    for ns in namespaces:
        emoji = '🔧' if 'kube' in ns else '📦' if ns == 'mcp-server' else '⚡' if ns == 'karpenter' else '📋'
        print(f'      {emoji} {ns}')

if __name__ == "__main__":
    simulate_natural_language_query()