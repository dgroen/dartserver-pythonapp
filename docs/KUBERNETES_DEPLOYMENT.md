# Kubernetes Deployment Guide for Darts Application

This guide provides step-by-step instructions for deploying the Darts application to an AWS EKS (Elastic Kubernetes Service) cluster with automated deployment, monitoring, and logging.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Application Deployment](#application-deployment)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Scaling Configuration](#scaling-configuration)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **AWS CLI** (v2.x): [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- **kubectl** (v1.28+): [Installation Guide](https://kubernetes.io/docs/tasks/tools/)
- **Helm** (v3.13+): [Installation Guide](https://helm.sh/docs/intro/install/)
- **Terraform** (v1.5+): [Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
- **Docker**: [Installation Guide](https://docs.docker.com/get-docker/)

### AWS Requirements

- AWS account with appropriate permissions
- AWS credentials configured (`aws configure`)
- ECR repositories created for container images
- IAM role for GitHub Actions (for CI/CD)

### Recommended Knowledge

- Kubernetes concepts (Pods, Deployments, Services, ConfigMaps, Secrets)
- Helm chart basics
- Terraform fundamentals
- AWS EKS architecture
- Docker containerization

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud (EKS)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐       ┌──────────────┐                       │
│  │  ALB Ingress │───────│  Nginx       │                       │
│  │  Controller  │       │  (optional)  │                       │
│  └──────────────┘       └──────────────┘                       │
│         │                      │                                │
│         ├──────────────────────┼────────────────────┐           │
│         │                      │                    │           │
│   ┌─────▼──────┐        ┌─────▼──────┐      ┌─────▼──────┐    │
│   │  Darts App │        │API Gateway │      │  WSO2 IS   │    │
│   │  (2-10)    │        │  (2-8)     │      │    (1)     │    │
│   └─────┬──────┘        └─────┬──────┘      └─────┬──────┘    │
│         │                     │                    │           │
│         ├─────────────────────┴────────────────────┤           │
│         │                                           │           │
│   ┌─────▼──────┐       ┌──────────┐       ┌───────▼──────┐    │
│   │ PostgreSQL │       │ RabbitMQ │       │ Monitoring   │    │
│   │     (1)    │       │    (1)   │       │ (Prometheus) │    │
│   └────────────┘       └──────────┘       └──────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 EKS Managed Node Group                   │  │
│  │              (Auto-scaling: 2-10 nodes)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

- **Darts App**: Main Flask + Socket.IO application (2-10 replicas)
- **API Gateway**: REST API gateway with authentication (2-8 replicas)
- **PostgreSQL**: Database for persistent storage (StatefulSet)
- **RabbitMQ**: Message broker for event-driven communication (StatefulSet)
- **WSO2 Identity Server**: OAuth2/OIDC authentication provider
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Fluent Bit**: Log collection and forwarding to CloudWatch

## Infrastructure Setup

### Step 1: Create EKS Cluster with Terraform

1. **Navigate to Terraform directory:**
   ```bash
   cd terraform
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Review the configuration:**
   ```bash
   terraform plan
   ```

4. **Apply the configuration:**
   ```bash
   terraform apply
   ```
   
   This will create:
   - VPC with public and private subnets
   - EKS cluster with managed node groups
   - IAM roles and policies
   - Security groups
   - VPC endpoints for ECR and S3

5. **Update kubeconfig:**
   ```bash
   aws eks update-kubeconfig --region us-east-1 --name darts-eks-cluster
   ```

6. **Verify cluster access:**
   ```bash
   kubectl get nodes
   ```

### Step 2: Install Required Add-ons

1. **Install AWS Load Balancer Controller:**
   ```bash
   helm repo add eks https://aws.github.io/eks-charts
   helm repo update
   
   helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
     -n kube-system \
     --set clusterName=darts-eks-cluster \
     --set serviceAccount.create=true \
     --set serviceAccount.name=aws-load-balancer-controller
   ```

2. **Install EBS CSI Driver:**
   ```bash
   helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
   helm repo update
   
   helm install aws-ebs-csi-driver aws-ebs-csi-driver/aws-ebs-csi-driver \
     -n kube-system \
     --set enableVolumeScheduling=true \
     --set enableVolumeResizing=true \
     --set enableVolumeSnapshot=true
   ```

3. **Install Cluster Autoscaler:**
   ```bash
   helm repo add autoscaler https://kubernetes.github.io/autoscaler
   helm repo update
   
   helm install cluster-autoscaler autoscaler/cluster-autoscaler \
     -n kube-system \
     --set autoDiscovery.clusterName=darts-eks-cluster \
     --set awsRegion=us-east-1
   ```

### Step 3: Create ECR Repositories

```bash
aws ecr create-repository --repository-name darts-app --region us-east-1
aws ecr create-repository --repository-name api-gateway --region us-east-1
```

## Application Deployment

### Option 1: Deploy with Helm (Recommended)

1. **Build and push Docker images:**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and push Darts app
   docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/darts-app:v1.0.0 -f Dockerfile .
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/darts-app:v1.0.0
   
   # Build and push API Gateway
   docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/api-gateway:v1.0.0 -f Dockerfile.gateway .
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/api-gateway:v1.0.0
   ```

2. **Update Helm values:**
   Edit `helm/darts-app/values-production.yaml` with your specific configuration (secrets, domain names, etc.)

3. **Install the Helm chart:**
   ```bash
   helm install darts-app ./helm/darts-app \
     --namespace darts-app \
     --create-namespace \
     --values ./helm/darts-app/values-production.yaml
   ```

4. **Verify deployment:**
   ```bash
   kubectl get pods -n darts-app
   kubectl get svc -n darts-app
   kubectl get ingress -n darts-app
   ```

### Option 2: Deploy with kubectl

1. **Apply namespace:**
   ```bash
   kubectl apply -f k8s/base/namespace/
   ```

2. **Create secrets:**
   Update secrets with your actual credentials:
   ```bash
   kubectl apply -f k8s/base/secrets/
   ```

3. **Apply ConfigMaps:**
   ```bash
   kubectl apply -f k8s/base/configmaps/
   ```

4. **Deploy StatefulSets:**
   ```bash
   kubectl apply -f k8s/base/statefulsets/
   ```

5. **Deploy applications:**
   ```bash
   kubectl apply -f k8s/base/deployments/
   ```

6. **Create services:**
   ```bash
   kubectl apply -f k8s/base/services/
   ```

7. **Apply ingress:**
   ```bash
   kubectl apply -f k8s/ingress/
   ```

8. **Apply HPA:**
   ```bash
   kubectl apply -f k8s/hpa/
   ```

## Monitoring and Logging

### Deploy Monitoring Stack

1. **Deploy Prometheus:**
   ```bash
   kubectl apply -f k8s/monitoring/prometheus.yaml
   ```

2. **Deploy Grafana:**
   ```bash
   kubectl apply -f k8s/monitoring/grafana.yaml
   ```

3. **Access Grafana:**
   ```bash
   kubectl port-forward svc/grafana-service 3000:3000 -n monitoring
   ```
   
   Open http://localhost:3000 (default credentials: admin/admin)

4. **Import dashboards:**
   - Kubernetes Cluster Monitoring: Dashboard ID 315
   - Node Exporter: Dashboard ID 1860
   - PostgreSQL: Dashboard ID 9628

### Deploy Logging Stack

1. **Deploy Fluent Bit:**
   ```bash
   kubectl apply -f k8s/logging/fluent-bit.yaml
   ```

2. **Verify logs in CloudWatch:**
   ```bash
   aws logs tail /aws/eks/darts-app/application --follow
   ```

## Scaling Configuration

### Horizontal Pod Autoscaling (HPA)

HPA is configured to scale based on CPU and memory utilization:

- **Darts App**: 2-10 replicas
  - Scale up at 70% CPU or 80% memory
  - Scale down after 5 minutes of low usage

- **API Gateway**: 2-8 replicas
  - Scale up at 70% CPU or 80% memory
  - Scale down after 5 minutes of low usage

### Cluster Autoscaling

EKS node group auto-scaling:
- Minimum nodes: 2
- Maximum nodes: 10
- Scales based on pod resource requests

### Manual Scaling

Scale deployments manually if needed:
```bash
kubectl scale deployment darts-app --replicas=5 -n darts-app
kubectl scale deployment api-gateway --replicas=4 -n darts-app
```

## CI/CD Pipeline

### GitHub Actions Workflow

The repository includes two GitHub Actions workflows:

1. **`deploy-eks.yml`**: Build, push, and deploy application
   - Triggered on push to `main` or `develop` branches
   - Builds Docker images
   - Pushes to ECR
   - Deploys to EKS using Helm
   - Runs smoke tests

2. **`terraform-eks.yml`**: Manage infrastructure
   - Validates Terraform code
   - Plans infrastructure changes
   - Applies changes on merge to `main`

### Setup Instructions

1. **Configure GitHub Secrets:**
   ```
   AWS_ROLE_TO_ASSUME: arn:aws:iam::account-id:role/github-actions-role
   ```

2. **Create IAM role for GitHub Actions:**
   - Configure OIDC provider
   - Attach necessary policies (ECR, EKS, CloudWatch)

3. **Enable workflows:**
   Workflows will run automatically on push/PR

### Manual Deployment

Trigger manual deployment:
```bash
gh workflow run deploy-eks.yml -f environment=production
```

## Troubleshooting

### Common Issues

#### Pods not starting

```bash
# Check pod status
kubectl get pods -n darts-app

# View pod logs
kubectl logs <pod-name> -n darts-app

# Describe pod for events
kubectl describe pod <pod-name> -n darts-app
```

#### Service not accessible

```bash
# Check service endpoints
kubectl get endpoints -n darts-app

# Test service internally
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- \
  curl -v http://darts-app-service:5000/health
```

#### Database connection issues

```bash
# Check PostgreSQL pod
kubectl get pods -l app=postgres -n darts-app
kubectl logs <postgres-pod> -n darts-app

# Test connectivity
kubectl run psql-client --image=postgres:16-alpine --rm -i --restart=Never -- \
  psql -h postgres-service.darts-app.svc.cluster.local -U postgres -d dartsdb
```

#### HPA not scaling

```bash
# Check HPA status
kubectl get hpa -n darts-app
kubectl describe hpa darts-app-hpa -n darts-app

# Verify metrics server
kubectl top nodes
kubectl top pods -n darts-app
```

### Useful Commands

```bash
# View all resources
kubectl get all -n darts-app

# Check resource usage
kubectl top pods -n darts-app
kubectl top nodes

# View cluster events
kubectl get events -n darts-app --sort-by='.lastTimestamp'

# Execute commands in pod
kubectl exec -it <pod-name> -n darts-app -- /bin/bash

# View Helm release
helm list -n darts-app
helm status darts-app -n darts-app

# Rollback deployment
helm rollback darts-app -n darts-app
```

## Security Best Practices

1. **Secrets Management**: Use AWS Secrets Manager or HashiCorp Vault
2. **Network Policies**: Enable and configure network policies
3. **RBAC**: Implement role-based access control
4. **Pod Security**: Use Pod Security Standards
5. **Image Scanning**: Scan images for vulnerabilities
6. **TLS/SSL**: Enable TLS for all external traffic
7. **Audit Logging**: Enable EKS control plane logging

## Cost Optimization

1. **Right-sizing**: Monitor and adjust resource requests/limits
2. **Spot Instances**: Use EC2 Spot instances for non-critical workloads
3. **Auto-scaling**: Properly configure HPA and cluster autoscaler
4. **Reserved Instances**: Consider RIs for predictable workloads
5. **Storage**: Use appropriate storage classes (gp2 vs gp3)

## Next Steps

1. Set up custom domain and SSL certificates
2. Configure backup and disaster recovery
3. Implement blue-green or canary deployments
4. Set up monitoring alerts and notifications
5. Document runbooks for common operations
6. Conduct load testing and performance tuning

## Support and Resources

- [EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Project Repository](https://github.com/dgroen/dartserver-pythonapp)
