#!/bin/bash
set -e

echo "🧪 MCP EKS Comprehensive Test Suite"
echo "=================================="

# Get LoadBalancer URL
LB_URL=$(kubectl get service mcp-server-service -n mcp-server -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
if [ -z "$LB_URL" ]; then
    echo "❌ LoadBalancer not ready yet"
    exit 1
fi

echo "🌐 LoadBalancer URL: http://$LB_URL"
echo ""

# Test 1: Application Health
echo "1️⃣  Testing Application Health..."
HEALTH=$(curl -s "http://$LB_URL/health" | jq -r '.status')
if [ "$HEALTH" = "healthy" ]; then
    echo "✅ Application is healthy"
else
    echo "❌ Application health check failed"
    exit 1
fi

# Test 2: Kubernetes API Access
echo ""
echo "2️⃣  Testing Kubernetes API Access..."
NAMESPACES=$(curl -s "http://$LB_URL/cluster-info" | jq -r '.namespace_count')
if [ "$NAMESPACES" -gt 0 ]; then
    echo "✅ Kubernetes API accessible ($NAMESPACES namespaces found)"
else
    echo "❌ Kubernetes API access failed"
    exit 1
fi

# Test 3: Node Information
echo ""
echo "3️⃣  Testing Node Information..."
NODE_COUNT=$(curl -s "http://$LB_URL/nodes" | jq -r '.node_count')
KARPENTER_NODES=$(curl -s "http://$LB_URL/nodes" | jq -r '.nodes[] | select(.instance_type != "t3.medium") | .name' | wc -l)
echo "✅ Found $NODE_COUNT total nodes, $KARPENTER_NODES Karpenter-managed nodes"

# Test 4: Pod Information
echo ""
echo "4️⃣  Testing Pod Information..."
MCP_PODS=$(curl -s "http://$LB_URL/pods?namespace=mcp-server" | jq -r '.pod_count')
if [ "$MCP_PODS" -ge 1 ]; then
    echo "✅ MCP Server pods running ($MCP_PODS pods)"
else
    echo "❌ No MCP Server pods found"
    exit 1
fi

# Test 5: Karpenter Status
echo ""
echo "5️⃣  Testing Karpenter Status..."
NODEPOOL_STATUS=$(kubectl get nodepool default -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
NODECLASS_STATUS=$(kubectl get ec2nodeclass default -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')

if [ "$NODEPOOL_STATUS" = "True" ] && [ "$NODECLASS_STATUS" = "True" ]; then
    echo "✅ Karpenter is ready (NodePool: $NODEPOOL_STATUS, EC2NodeClass: $NODECLASS_STATUS)"
else
    echo "❌ Karpenter not ready (NodePool: $NODEPOOL_STATUS, EC2NodeClass: $NODECLASS_STATUS)"
    exit 1
fi

# Test 6: Load Test (Optional)
echo ""
echo "6️⃣  Load Testing (10 requests)..."
for i in {1..10}; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$LB_URL/health")
    if [ "$STATUS" != "200" ]; then
        echo "❌ Request $i failed with status $STATUS"
        exit 1
    fi
    echo -n "."
done
echo ""
echo "✅ Load test passed (10/10 requests successful)"

echo ""
echo "🎉 All tests passed! Deployment is working correctly."
echo ""
echo "📊 Quick Access URLs:"
echo "   Health:      http://$LB_URL/health"
echo "   Cluster:     http://$LB_URL/cluster-info"
echo "   Nodes:       http://$LB_URL/nodes"
echo "   Pods:        http://$LB_URL/pods?namespace=mcp-server"
echo "   Deployments: http://$LB_URL/deployments?namespace=default"