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
│   ├── main.tf                 # Main Terraform configuration
│   ├── variables.tf            # Variable definitions
│   ├── outputs.tf              # Output definitions
│   └── karpenter/              # Karpenter deployment
│       ├── main.tf             # Karpenter Helm chart and providers
│       └── nodepool.tf         # NodePool and EC2NodeClass
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

### Server (`server-enhanced.py`) 
- **Real Kubernetes API Integration**: Connects to actual EKS cluster
- **Resources**: 
  - Live cluster information with namespace counts
  - Real-time node status and information
  - Health checks with API connectivity status
- **Tools**: 
  - `get_cluster_status` - Real cluster metrics with optional node details
  - `list_pods` - Live pod information from any namespace with status
  - `get_deployments` - Deployment status and replica counts
- **Error Handling**: Graceful API error handling and fallbacks
- **Automatic Config**: Supports both in-cluster and local kubectl configurations

### Client Integration
- **Claude Desktop**: Natural language interface to your EKS cluster
- **Programmatic Access**: Python client example for automation
- **Health Monitoring**: Liveness and readiness probes

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

The Karpenter setup includes:
- **Minimal managed node group**: Single t3.medium node for Karpenter installation
- **NodePool**: Configures instance types (t3.medium/large/xlarge) and capacity types (spot/on-demand)
- **EC2NodeClass**: Defines AMI family, security groups, and subnets
- **Auto-scaling**: Nodes scale based on pod scheduling requirements
- **Cost optimization**: Prefers spot instances when available

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

### Using with Claude Desktop
After configuring Claude Desktop:
```
You: "Can you check the status of my EKS cluster?"
Claude: [Uses MCP server to get real cluster information]

You: "List all pods in the mcp-server namespace"
Claude: [Shows live pod status and information]

You: "What deployments are running in default namespace?"
Claude: [Returns deployment status with replica counts]
```

### Programmatic Usage
```python
# Use the client example as a starting point
python client-example.py

# Integrate into your own applications
from mcp.client.session import ClientSession
# ... see client-example.py for full implementation
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
cd terraform/karpenter && terraform destroy -auto-approve
cd ../.. && terraform destroy -auto-approve
```

### Legacy Deployment Cleanup
```bash
make destroy
```
