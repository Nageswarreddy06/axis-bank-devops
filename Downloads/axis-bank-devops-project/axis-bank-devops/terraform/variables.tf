variable "aws_region" {
  description = "AWS region for all project resources."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Short name used for resource tags."
  type        = string
  default     = "axis-bank-demo"
}

variable "cluster_name" {
  description = "Name of the EKS cluster."
  type        = string
  default     = "axis-bank-demo-eks"
}

variable "cluster_version" {
  description = "Kubernetes version supported by EKS in your selected region."
  type        = string
  default     = "1.34"
}

variable "vpc_cidr" {
  description = "CIDR range for the learning VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "github_repository" {
  description = "GitHub repository in OWNER/REPO format, e.g. username/axis-bank-devops."
  type        = string
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "Restrict EKS public API access to your public IP in CIDR format, e.g. [\"198.51.100.10/32\"]. Do not leave a wide-open range."
  type        = list(string)
}
