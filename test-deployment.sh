#!/bin/bash
set -e

echo "Testing MCP Server deployment..."

# Get AWS Account ID automatically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: Unable to get AWS Account ID. Please check your AWS credentials."
    exit 1
fi
echo "Using AWS Account ID: $AWS_ACCOUNT_ID"

# Create ECR repository if it doesn't exist
echo "Creating ECR repository..."
aws ecr describe-repositories --repository-names mcp-server --region ${AWS_REGION:-us-east-1} || \
aws ecr create-repository --repository-name mcp-server --region ${AWS_REGION:-us-east-1}

# Deploy infrastructure with Karpenter
echo "Deploying infrastructure..."
./scripts/deploy.sh infrastructure

# Verify Karpenter is working
echo "Verifying Karpenter..."
./scripts/deploy.sh karpenter

# Deploy application
echo "Deploying MCP server..."
./scripts/deploy.sh app

# Test the deployment
echo "Testing deployment..."
kubectl get pods -n mcp-server
kubectl get services -n mcp-server

# Check Karpenter nodes
echo "Checking Karpenter managed nodes..."
kubectl get nodes -l karpenter.sh/nodepool

# Show Karpenter resources
echo "Karpenter resources:"
kubectl get nodepool,ec2nodeclass -o wide

echo "Deployment test completed!"