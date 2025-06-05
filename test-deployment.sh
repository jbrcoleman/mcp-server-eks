#!/bin/bash
set -e

echo "Testing MCP Server deployment..."

# Check if required environment variables are set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: AWS_ACCOUNT_ID environment variable is required"
    echo "Set it with: export AWS_ACCOUNT_ID=your-account-id"
    exit 1
fi

# Create ECR repository if it doesn't exist
echo "Creating ECR repository..."
aws ecr describe-repositories --repository-names mcp-server --region ${AWS_REGION:-us-west-2} || \
aws ecr create-repository --repository-name mcp-server --region ${AWS_REGION:-us-west-2}

# Deploy infrastructure
echo "Deploying infrastructure..."
make init plan apply

# Deploy application
echo "Deploying MCP server..."
make deploy

# Test the deployment
echo "Testing deployment..."
kubectl get pods -n mcp-server
kubectl get services -n mcp-server

echo "Deployment test completed!"