terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  zango_task_definition = templatefile("${path.module}/zango-ecs-task.json", {
    TASK_ROLE_ARN      = var.task_role_arn
    ZANGO_IMAGE_URI    = var.zango_image_uri
    NGINX_IMAGE_URI    = var.nginx_image_uri
    LOG_GROUP_NAME     = var.log_group_name
    AWS_REGION         = var.aws_region
    AWS_SECRET_NAME    = var.aws_secret_name
  })
}

resource "aws_ecs_cluster" "zango" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = var.tags
}

resource "aws_ecs_task_definition" "zango" {
  family                   = var.task_family
  requires_compatibilities = ["EC2"]
  network_mode            = "bridge"
  task_role_arn           = var.task_role_arn
  
  container_definitions = local.zango_task_definition
  
  volume {
    name = "app_volume"
    docker_volume_configuration {
      scope          = "shared"
      autoprovision  = true
      driver         = "local"
    }
  }
  
  volume {
    name = "static_volume"
    docker_volume_configuration {
      scope          = "shared"
      autoprovision  = true
      driver         = "local"
    }
  }
  
  volume {
    name = "media_volume"
    docker_volume_configuration {
      scope          = "shared"
      autoprovision  = true
      driver         = "local"
    }
  }
  
  volume {
    name = "logs_volume"
    docker_volume_configuration {
      scope          = "shared"
      autoprovision  = true
      driver         = "local"
    }
  }
  
  dynamic "placement_constraints" {
    for_each = var.placement_constraint_expression != "" ? [1] : []
    content {
      type       = "memberOf"
      expression = var.placement_constraint_expression
    }
  }
  
  tags = var.tags
}

resource "aws_ecs_service" "zango" {
  count           = var.create_service ? 1 : 0
  name            = var.service_name
  cluster         = aws_ecs_cluster.zango.id
  task_definition = aws_ecs_task_definition.zango.arn
  desired_count   = var.desired_count
  
  dynamic "placement_constraints" {
    for_each = var.placement_constraint_expression != "" ? [1] : []
    content {
      type       = "memberOf"
      expression = var.placement_constraint_expression
    }
  }
  
  tags = var.tags
}

resource "aws_cloudwatch_log_group" "zango" {
  count             = var.create_log_group ? 1 : 0
  name              = var.log_group_name
  retention_in_days = var.log_retention_days
  
  tags = var.tags
}
