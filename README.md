# MCP Server on EKS

This project deploys a Model Context Protocol (MCP) server on Amazon EKS using Terraform for infrastructure management.

## Architecture

- **MCP Server**: Python-based server implementing MCP protocol
- **Container**: Docker container for the MCP server
- **Kubernetes**: EKS cluster for container orchestration
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
export AWS_REGION=us-west-2
export AWS_ACCOUNT_ID=your-account-id
export CLUSTER_NAME=mcp-eks-cluster
```

2. **Deploy infrastructure**:
```bash
make init
make plan
make apply
```

3. **Deploy application**:
```bash
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
│   └── outputs.tf              # Output definitions
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

### Infrastructure Deployment
```bash
# Initialize and deploy infrastructure
make init plan apply

# Build and deploy application
make deploy

# Complete deployment (infrastructure + app)
make full-deploy

# Test complete deployment
./scripts/test-deployment.sh
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
- `AWS_REGION`: AWS region (default: us-west-2)
- `CLUSTER_NAME`: EKS cluster name (default: mcp-eks-cluster)
- `IMAGE_TAG`: Docker image tag (default: latest)
- `AWS_ACCOUNT_ID`: Your AWS account ID

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

To destroy all resources:
```bash
make destroy
```
