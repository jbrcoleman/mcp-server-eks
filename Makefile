.PHONY: init plan apply deploy clean destroy

# Variables
REGION ?= us-west-2
CLUSTER_NAME ?= mcp-eks-cluster
IMAGE_TAG ?= latest

# Initialize Terraform
init:
	@echo "Initializing Terraform..."
	cd terraform && terraform init

# Plan Terraform deployment
plan:
	@echo "Planning Terraform deployment..."
	cd terraform && terraform plan -out=tfplan

# Apply Terraform deployment
apply:
	@echo "Applying Terraform deployment..."
	cd terraform && terraform apply tfplan

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t mcp-server:$(IMAGE_TAG) .

# Deploy to Kubernetes
deploy: build
	@echo "Deploying to EKS..."
	./scripts/deploy.sh

# Clean up local resources
clean:
	@echo "Cleaning up..."
	docker system prune -f

# Destroy infrastructure
destroy:
	@echo "Destroying Terraform infrastructure..."
	cd terraform && terraform destroy -auto-approve

# Full deployment (infrastructure + application)
full-deploy: init plan apply deploy

# Help
help:
	@echo "Available targets:"
	@echo "  init        - Initialize Terraform"
	@echo "  plan        - Plan Terraform deployment"
	@echo "  apply       - Apply Terraform deployment"
	@echo "  build       - Build Docker image"
	@echo "  deploy      - Deploy application to EKS"
	@echo "  clean       - Clean up local resources"
	@echo "  destroy     - Destroy infrastructure"
	@echo "  full-deploy - Complete deployment (infrastructure + app)"
	@echo "  help        - Show this help"