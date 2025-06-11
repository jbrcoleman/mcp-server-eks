#!/bin/bash
set -e

echo "Starting MCP Server deployment to EKS with Karpenter..."

# Variables
REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME=${CLUSTER_NAME:-mcp-eks-cluster}
IMAGE_TAG=${IMAGE_TAG:-latest}
ECR_REPO=${ECR_REPO:-mcp-server}
PHASE=${1:-all}

# Get AWS Account ID automatically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: Unable to get AWS Account ID. Please check your AWS credentials."
    exit 1
fi
echo "Using AWS Account ID: $AWS_ACCOUNT_ID"

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

# Function to verify Karpenter deployment
verify_karpenter() {
    echo "Phase 2: Verifying Karpenter deployment..."
    
    echo "Waiting for Karpenter to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=karpenter -n karpenter --timeout=300s
    
    echo "Checking Karpenter NodePool and EC2NodeClass..."
    kubectl get nodepool,ec2nodeclass -o wide
}

# Function to deploy application
deploy_application() {
    echo "Phase 3: Deploying MCP Server application..."
    
    # Build and push Docker image
    echo "Building Docker image..."
    docker build -t $ECR_REPO:$IMAGE_TAG .
    
    # Use a unique tag to avoid ECR immutable tag issues
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    UNIQUE_TAG="$IMAGE_TAG-$TIMESTAMP"
    docker tag $ECR_REPO:$IMAGE_TAG $ECR_REPO:$UNIQUE_TAG
    
    # Get ECR login token and login
    echo "Logging into ECR..."
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
    
    # Tag and push image with unique tag
    echo "Pushing image to ECR..."
    docker tag $ECR_REPO:$UNIQUE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$UNIQUE_TAG
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$UNIQUE_TAG
    
    # Update deployment image tag
    echo "Updating deployment image tag..."
    sed -i "s|image: .*mcp-server:.*|image: $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$UNIQUE_TAG|" k8s/deployment.yaml
    
    # Apply Kubernetes manifests
    echo "Deploying to Kubernetes..."
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/rbac.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    
    # Wait for deployment
    echo "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/mcp-server -n mcp-server
    
    # Get service endpoint
    echo "Getting service endpoint..."
    kubectl get service mcp-server-service -n mcp-server
    
    # Display access information
    echo ""
    echo "=== Deployment Complete! ==="
    LB_URL=$(kubectl get service mcp-server-service -n mcp-server -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
    if [ "$LB_URL" != "pending" ]; then
        echo "🌐 External URL: http://$LB_URL"
        echo "📊 Health Check: http://$LB_URL/health"
        echo "🏗️  Cluster Info: http://$LB_URL/cluster-info"
        echo "🖥️  Nodes: http://$LB_URL/nodes"
        echo "🐳 Pods: http://$LB_URL/pods?namespace=mcp-server"
    else
        echo "⏳ LoadBalancer provisioning... check again in a few minutes"
    fi
}

# Main deployment logic
case $PHASE in
    "infrastructure")
        deploy_infrastructure
        ;;
    "karpenter")
        verify_karpenter
        ;;
    "app")
        deploy_application
        ;;
    "all")
        deploy_infrastructure
        verify_karpenter
        deploy_application
        ;;
    *)
        echo "Usage: $0 [infrastructure|karpenter|app|all]"
        echo "  infrastructure: Deploy only EKS cluster and VPC with Karpenter"
        echo "  karpenter: Verify Karpenter deployment (requires infrastructure)"
        echo "  app: Deploy only the MCP server application"
        echo "  all: Deploy everything (default)"
        exit 1
        ;;
esac

echo "Deployment completed successfully!"