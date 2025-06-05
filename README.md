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
├── server.py              # MCP server implementation
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
├── terraform/             # Infrastructure as code
│   ├── main.tf           # Main Terraform configuration
│   ├── variables.tf      # Variable definitions
│   └── outputs.tf        # Output definitions
├── k8s/                  # Kubernetes manifests
│   ├── namespace.yaml    # Namespace definition
│   ├── deployment.yaml   # Application deployment
│   ├── service.yaml      # Service definition
│   └── configmap.yaml    # Configuration map
├── scripts/              # Deployment scripts
│   ├── deploy.sh         # Main deployment script
│   └── terraform-init.sh # Terraform initialization
└── Makefile              # Build automation
```

## MCP Server Features

The server provides:
- **Resources**: Cluster information and health status
- **Tools**: Cluster status and pod listing capabilities
- **Health checks**: Liveness and readiness probes

## Deployment Commands

```bash
# Initialize and deploy infrastructure
make init plan apply

# Build and deploy application
make deploy

# Complete deployment (infrastructure + app)
make full-deploy

# Clean up
make destroy
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

## Cleanup

To destroy all resources:
```bash
make destroy
```
