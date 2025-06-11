# MCP Server on EKS

This project deploys a Model Context Protocol (MCP) server on Amazon EKS using Terraform for infrastructure management.

## Architecture

- **MCP Server**: Python-based server implementing MCP protocol
- **Container**: Docker container for the MCP server
- **Kubernetes**: EKS cluster for container orchestration
- **Karpenter**: Kubernetes-native node autoscaler for efficient scaling
- **Infrastructure**: Terraform for AWS resource management

## Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed
- Terraform >= 1.0
- kubectl installed
- An AWS account with ECR repository created

## Quick Start

1. **Set environment variables**:
```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=your-account-id
export CLUSTER_NAME=mcp-eks-cluster
```

2. **Deploy with Karpenter (Recommended)**:
```bash
# Option 1: Deploy everything at once
./scripts/deploy.sh all

# Option 2: Phase-by-phase deployment
./scripts/deploy.sh infrastructure  # Deploy EKS cluster
./scripts/deploy.sh karpenter       # Deploy Karpenter autoscaler
./scripts/deploy.sh app             # Deploy MCP server
```

3. **Legacy deployment (without Karpenter)**:
```bash
make init
make plan
make apply
make deploy
```

## Project Structure

```
├── server-enhanced.py           # MCP server with real Kubernetes API integration
├── client-example.py            # Example MCP client for testing
├── Dockerfile                   # Container definition
├── requirements.txt             # Python dependencies
├── terraform/                   # Infrastructure as code
│   ├── main.tf                 # Main Terraform configuration with integrated Karpenter
│   ├── variables.tf            # Variable definitions
│   ├── outputs.tf              # Output definitions
│   └── userdata.sh             # EC2 user data script for Karpenter nodes
├── k8s/                        # Kubernetes manifests
│   ├── namespace.yaml          # Namespace definition
│   ├── deployment.yaml         # Application deployment
│   ├── service.yaml            # Service definition
│   └── configmap.yaml          # Configuration map
├── scripts/                    # Deployment scripts
│   ├── deploy.sh               # Main deployment script
│   ├── terraform-init.sh       # Terraform initialization
│   └── test-deployment.sh      # Complete deployment test
├── claude-desktop-config.json  # Claude Desktop MCP configuration
├── integrate-with-claude.md     # Claude Desktop integration guide
└── Makefile                    # Build automation
```

## MCP Server Features

### Server (`server-simple.py`) 
- **Real Kubernetes API Integration**: Connects to actual EKS cluster with proper RBAC
- **HTTP REST API**: Simple HTTP endpoints for easy testing and integration
- **Endpoints**: 
  - `GET /health` - Health check with Kubernetes API connectivity status
  - `GET /cluster-info` - Live cluster information with namespace counts
  - `GET /nodes` - Real-time node status and information
  - `GET /pods?namespace=<ns>` - Live pod information from any namespace
  - `GET /deployments?namespace=<ns>` - Deployment status and replica counts
- **Security**: Proper RBAC with minimal required permissions
- **Error Handling**: Graceful API error handling and detailed error responses
- **Load Balancer**: External access via AWS Application Load Balancer

### What is MCP (Model Context Protocol)?

**MCP** enables AI assistants like Claude to connect to external data sources and tools. Instead of running kubectl commands, you can ask natural language questions about your cluster!

**The Magic:** Your EKS Cluster ↔️ MCP Server ↔️ Claude Desktop ↔️ Natural Language

### Natural Language Examples

Instead of commands like `kubectl get nodes`, you can ask Claude:

- *"How is my cluster doing?"* → Gets health, nodes, and status
- *"Are my MCP server pods running?"* → Checks pod health and restarts  
- *"What Karpenter nodes do I have?"* → Shows auto-scaled nodes
- *"Show me all my namespaces"* → Lists cluster namespaces
- *"Is my cluster having any issues?"* → Comprehensive health check

### Demo the Natural Language Interface
```bash
# See what natural language queries would look like
python3 demo-natural-language.py
```

### Client Integration Options
1. **HTTP REST API**: Direct HTTP access for testing and integration
2. **Claude Desktop**: Natural language interface via MCP bridge (see claude-desktop-config.json)
3. **Load Balancer**: External access via AWS ELB for production use

## Deployment Commands

### Karpenter-based Deployment (Recommended)
```bash
# Deploy everything with Karpenter
./scripts/deploy.sh all

# Or deploy in phases for more control
./scripts/deploy.sh infrastructure  # Phase 1: EKS cluster with minimal nodes
./scripts/deploy.sh karpenter       # Phase 2: Karpenter installation
./scripts/deploy.sh app             # Phase 3: MCP server application

# Test deployment
./scripts/test-deployment.sh
```

### Legacy Infrastructure Deployment
```bash
# Initialize and deploy infrastructure (without Karpenter)
make init plan apply

# Build and deploy application
make deploy

# Complete deployment (infrastructure + app)
make full-deploy
```

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test server locally (requires kubectl access to EKS)
python server-enhanced.py

# Run client example
python client-example.py
```

### Claude Desktop Integration
```bash
# Follow the integration guide
cat integrate-with-claude.md

# Copy configuration (macOS example)
cp claude-desktop-config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

## Configuration

Environment variables:
- `AWS_REGION`: AWS region (default: us-east-1)
- `CLUSTER_NAME`: EKS cluster name (default: mcp-eks-cluster)
- `IMAGE_TAG`: Docker image tag (default: latest)
- `AWS_ACCOUNT_ID`: Your AWS account ID

### Karpenter Configuration

The Karpenter setup follows AWS EKS Blueprints pattern and includes:
- **EKS Module Integration**: Uses terraform-aws-modules/eks with built-in Karpenter support
- **Managed Node Group**: 2 t3.medium nodes with karpenter.sh/controller taint for system pods
- **Pod Identity**: Uses EKS Pod Identity for secure AWS API access
- **NodePool**: Configures instance types (t3.medium/large/xlarge) and capacity types (spot/on-demand)
- **EC2NodeClass**: Defines AMI family (AL2023), security groups, and subnets using discovery tags
- **Auto-scaling**: Nodes scale based on pod scheduling requirements with 30s consolidation
- **Cost optimization**: Prefers spot instances and consolidates underutilized nodes

### Current Status ✅
- **Karpenter**: Successfully deployed and provisioning nodes (AL2023 AMI)
- **MCP Server**: HTTP REST API running on Karpenter-managed nodes
- **Load Balancer**: External access configured and working
- **RBAC**: Proper permissions for Kubernetes API access

## Monitoring

Access your MCP server:
```bash
kubectl get service mcp-server-service -n mcp-server
```

View logs:
```bash
kubectl logs -f deployment/mcp-server -n mcp-server
```

## Usage Examples

### HTTP REST API
Access the server directly via HTTP endpoints:
```bash
# Get LoadBalancer URL
LB_URL=$(kubectl get service mcp-server-service -n mcp-server -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Health check
curl http://$LB_URL/health

# Cluster information
curl http://$LB_URL/cluster-info

# Node information
curl http://$LB_URL/nodes

# Pod information
curl http://$LB_URL/pods?namespace=mcp-server

# Deployment information
curl http://$LB_URL/deployments?namespace=default
```

### Local Testing
```bash
# Port forward for local access
kubectl port-forward -n mcp-server service/mcp-server-service 8080:80

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/cluster-info
```

## Testing

### Quick Test
Run the comprehensive test suite:
```bash
./test-all.sh
```

### Manual Testing
```bash
# Get LoadBalancer URL
LB_URL=$(kubectl get service mcp-server-service -n mcp-server -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test all endpoints
curl http://$LB_URL/health
curl http://$LB_URL/cluster-info  
curl http://$LB_URL/nodes
curl http://$LB_URL/pods?namespace=mcp-server
curl http://$LB_URL/deployments?namespace=default
```

### Test Karpenter Auto-scaling
```bash
# Apply test workload to trigger node provisioning
kubectl apply -f test-karpenter.yaml

# Watch Karpenter create new nodes
kubectl get nodeclaim -w

# Scale up to test more provisioning
kubectl scale deployment test-workload --replicas=8

# Check new nodes
kubectl get nodes -l karpenter.sh/nodepool

# Clean up
kubectl delete -f test-karpenter.yaml
```

### Monitor Karpenter
```bash
# Check Karpenter status
kubectl get nodepool,ec2nodeclass -o wide

# Watch Karpenter logs
kubectl logs -f -n karpenter -l app.kubernetes.io/name=karpenter

# Check node provisioning
kubectl get nodeclaim
```

## Troubleshooting

### Common Issues
1. **Import errors**: Install dependencies with `pip install -r requirements.txt`
2. **Kubernetes API access**: Ensure `kubectl` is configured and working
3. **ECR permissions**: Verify AWS credentials have ECR access
4. **Claude Desktop connection**: Check configuration file path and format

### Logs and Debugging
```bash
# Check pod logs
kubectl logs -f deployment/mcp-server -n mcp-server

# Test Kubernetes connectivity
kubectl get nodes

# Verify ECR repository
aws ecr describe-repositories --repository-names mcp-server
```

## Cleanup

### Karpenter Deployment Cleanup
```bash
# Remove in reverse order
kubectl delete -f k8s/
cd terraform && terraform destroy -auto-approve
```

### Legacy Deployment Cleanup
```bash
make destroy
```
