variable "task_family" {
  description = "Name of the ECS task definition family"
  type        = string
  default     = "zango"
}

variable "task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "zango_image_uri" {
  description = "URI of the Zango Docker image"
  type        = string
}

variable "nginx_image_uri" {
  description = "URI of the Nginx Docker image"
  type        = string
}

variable "log_group_name" {
  description = "Name of the CloudWatch log group"
  type        = string
  default     = "/ecs/zango"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "placement_constraint_expression" {
  description = "ECS placement constraint expression"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Environment = "production"
    Application = "zango"
  }
}

variable "create_service" {
  description = "Whether to create an ECS service"
  type        = bool
  default     = true
}

variable "service_name" {
  description = "Name of the ECS service"
  type        = string
  default     = "zango-service"
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "zango-ecs-cluster"
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

variable "max_percent" {
  description = "Maximum percentage of tasks during deployment"
  type        = number
  default     = 200
}

variable "min_healthy_percent" {
  description = "Minimum healthy percentage during deployment"
  type        = number
  default     = 50
}

variable "create_log_group" {
  description = "Whether to create CloudWatch log group"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "aws_secret_name" {
    description = "AWS secret name"
    type = string
}
