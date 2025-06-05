#!/bin/bash
set -e

echo "Initializing Terraform for EKS deployment..."

cd terraform

# Initialize Terraform
echo "Running terraform init..."
terraform init

# Validate configuration
echo "Validating Terraform configuration..."
terraform validate

# Plan deployment
echo "Creating Terraform plan..."
terraform plan -out=tfplan

echo "Terraform initialization completed!"
echo "To apply the plan, run: terraform apply tfplan"