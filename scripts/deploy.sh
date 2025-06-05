#!/bin/bash
set -e

echo "Starting MCP Server deployment to EKS..."

# Variables
REGION=${AWS_REGION:-us-west-2}
CLUSTER_NAME=${CLUSTER_NAME:-mcp-eks-cluster}
IMAGE_TAG=${IMAGE_TAG:-latest}
ECR_REPO=${ECR_REPO:-mcp-server}

# Build and push Docker image
echo "Building Docker image..."
docker build -t $ECR_REPO:$IMAGE_TAG .

# Get ECR login token and login
echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Tag and push image
echo "Pushing image to ECR..."
docker tag $ECR_REPO:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

# Update kubeconfig
echo "Updating kubeconfig..."
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

# Apply Kubernetes manifests
echo "Deploying to Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Wait for deployment
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/mcp-server -n mcp-server

# Get service endpoint
echo "Getting service endpoint..."
kubectl get service mcp-server-service -n mcp-server

echo "Deployment completed successfully!"