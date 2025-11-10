# IAM Roles and Policies for EKS and Applications

# EBS CSI Driver IAM Role
module "ebs_csi_driver_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name = "${var.cluster_name}-ebs-csi-driver"

  attach_ebs_csi_policy = true

  oidc_providers = {
    main = {
      provider_arn               = aws_iam_openid_connect_provider.eks.arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }

  tags = {
    Name = "${var.cluster_name}-ebs-csi-driver-role"
  }
}

# ALB Ingress Controller IAM Role
module "alb_controller_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name = "${var.cluster_name}-alb-controller"

  attach_load_balancer_controller_policy = true

  oidc_providers = {
    main = {
      provider_arn               = aws_iam_openid_connect_provider.eks.arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }

  tags = {
    Name = "${var.cluster_name}-alb-controller-role"
  }
}

# Fluent Bit CloudWatch IAM Role
resource "aws_iam_role" "fluent_bit" {
  name = "${var.cluster_name}-fluent-bit"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Condition = {
        StringEquals = {
          "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:sub" = "system:serviceaccount:logging:fluent-bit"
          "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = {
    Name = "${var.cluster_name}-fluent-bit-role"
  }
}

resource "aws_iam_role_policy_attachment" "fluent_bit_cloudwatch" {
  role       = aws_iam_role.fluent_bit.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_policy" "fluent_bit_additional" {
  name        = "${var.cluster_name}-fluent-bit-additional"
  description = "Additional permissions for Fluent Bit"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/eks/${var.cluster_name}/*"]
      }
    ]
  })

  tags = {
    Name = "${var.cluster_name}-fluent-bit-additional-policy"
  }
}

resource "aws_iam_role_policy_attachment" "fluent_bit_additional" {
  role       = aws_iam_role.fluent_bit.name
  policy_arn = aws_iam_policy.fluent_bit_additional.arn
}

# ECR Access Policy for Nodes
resource "aws_iam_policy" "ecr_access" {
  name        = "${var.cluster_name}-ecr-access"
  description = "Allow EKS nodes to pull images from ECR"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "${var.cluster_name}-ecr-access-policy"
  }
}

# Cluster Autoscaler IAM Role
module "cluster_autoscaler_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name = "${var.cluster_name}-cluster-autoscaler"

  attach_cluster_autoscaler_policy = true
  cluster_autoscaler_cluster_names = [var.cluster_name]

  oidc_providers = {
    main = {
      provider_arn               = aws_iam_openid_connect_provider.eks.arn
      namespace_service_accounts = ["kube-system:cluster-autoscaler"]
    }
  }

  tags = {
    Name = "${var.cluster_name}-cluster-autoscaler-role"
  }
}

# Output IAM role ARNs
output "ebs_csi_driver_role_arn" {
  description = "IAM role ARN for EBS CSI driver"
  value       = module.ebs_csi_driver_irsa.iam_role_arn
}

output "alb_controller_role_arn" {
  description = "IAM role ARN for ALB controller"
  value       = module.alb_controller_irsa.iam_role_arn
}

output "fluent_bit_role_arn" {
  description = "IAM role ARN for Fluent Bit"
  value       = aws_iam_role.fluent_bit.arn
}

output "cluster_autoscaler_role_arn" {
  description = "IAM role ARN for Cluster Autoscaler"
  value       = module.cluster_autoscaler_irsa.iam_role_arn
}
