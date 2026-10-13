output "aws_region" {
  description = "AWS region used by this project."
  value       = var.aws_region
}

output "cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "ecr_repository_name" {
  description = "ECR repository name."
  value       = aws_ecr_repository.app.name
}

output "ecr_repository_url" {
  description = "Full ECR repository URL."
  value       = aws_ecr_repository.app.repository_url
}

output "github_actions_role_arn" {
  description = "Add this value to the GitHub secret AWS_GITHUB_ACTIONS_ROLE_ARN."
  value       = aws_iam_role.github_actions.arn
}

output "cluster_endpoint" {
  description = "EKS Kubernetes API endpoint."
  value       = module.eks.cluster_endpoint
}
