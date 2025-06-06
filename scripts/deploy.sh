#!/bin/bash
set -e

echo "Starting MCP Server deployment to EKS with Karpenter..."

# Variables
REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME=${CLUSTER_NAME:-mcp-eks-cluster}
IMAGE_TAG=${IMAGE_TAG:-latest}
ECR_REPO=${ECR_REPO:-mcp-server}
PHASE=${1:-all}

# Function to deploy infrastructure
deploy_infrastructure() {
    echo "Phase 1: Deploying EKS infrastructure..."
    cd terraform
    terraform init
    terraform plan
    terraform apply -auto-approve
    cd ..
    
    echo "Waiting for cluster to be ready..."
    aws eks wait cluster-active --name $CLUSTER_NAME --region $REGION
    
    echo "Updating kubeconfig..."
    aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME
}

# Function to deploy Karpenter
deploy_karpenter() {
    echo "Phase 2: Deploying Karpenter..."
    cd terraform/karpenter
    terraform init
    terraform plan
    terraform apply -auto-approve
    cd ../..
    
    echo "Waiting for Karpenter to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=karpenter -n karpenter --timeout=300s
}

# Function to deploy application
deploy_application() {
    echo "Phase 3: Deploying MCP Server application..."
    
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
}

# Main deployment logic
case $PHASE in
    "infrastructure")
        deploy_infrastructure
        ;;
    "karpenter")
        deploy_karpenter
        ;;
    "app")
        deploy_application
        ;;
    "all")
        deploy_infrastructure
        deploy_karpenter
        deploy_application
        ;;
    *)
        echo "Usage: $0 [infrastructure|karpenter|app|all]"
        echo "  infrastructure: Deploy only EKS cluster and VPC"
        echo "  karpenter: Deploy only Karpenter (requires infrastructure)"
        echo "  app: Deploy only the MCP server application"
        echo "  all: Deploy everything (default)"
        exit 1
        ;;
esac

echo "Deployment completed successfully!"