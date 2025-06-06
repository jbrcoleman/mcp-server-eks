variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "mcp-eks-cluster"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}