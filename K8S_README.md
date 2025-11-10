# Kubernetes Infrastructure for Darts Application

This directory contains Kubernetes manifests, Helm charts, Terraform configurations, and CI/CD pipelines for deploying the Darts application to AWS EKS with high availability, auto-scaling, monitoring, and logging.

## 📁 Directory Structure

```
.
├── k8s/                          # Kubernetes manifests
│   ├── base/                     # Base configurations
│   │   ├── namespace/            # Namespace definition
│   │   ├── configmaps/           # Application configurations
│   │   ├── secrets/              # Secrets (template only)
│   │   ├── deployments/          # Application deployments
│   │   ├── services/             # Service definitions
│   │   ├── statefulsets/         # StatefulSets (DB, RabbitMQ)
│   │   └── pvcs/                 # PersistentVolumeClaims
│   ├── hpa/                      # Horizontal Pod Autoscalers
│   ├── ingress/                  # Ingress configurations
│   ├── monitoring/               # Prometheus & Grafana
│   ├── logging/                  # Fluent Bit for log collection
│   └── network-policies/         # Network security policies
│
├── helm/                         # Helm charts
│   └── darts-app/               # Main Helm chart
│       ├── Chart.yaml           # Chart metadata
│       ├── values.yaml          # Default values
│       ├── values-production.yaml   # Production overrides
│       ├── values-development.yaml  # Development overrides
│       └── templates/           # Helm templates (future)
│
├── terraform/                    # Infrastructure as Code
│   ├── main.tf                  # Main Terraform config
│   ├── vpc/                     # VPC configuration
│   ├── eks/                     # EKS cluster setup
│   └── iam/                     # IAM roles and policies
│
├── .github/workflows/           # CI/CD pipelines
│   ├── deploy-eks.yml           # Application deployment
│   └── terraform-eks.yml        # Infrastructure management
│
└── docs/                        # Documentation
    ├── KUBERNETES_DEPLOYMENT.md    # Deployment guide
    └── KUBERNETES_ARCHITECTURE.md  # Architecture details
```

## 🚀 Quick Start

### Prerequisites

Ensure you have the following tools installed:
- [AWS CLI](https://aws.amazon.com/cli/) (v2.x)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (v1.28+)
- [Helm](https://helm.sh/docs/intro/install/) (v3.13+)
- [Terraform](https://www.terraform.io/downloads) (v1.5+)
- [Docker](https://docs.docker.com/get-docker/)

### 1. Deploy Infrastructure with Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This creates:
- VPC with public/private subnets
- EKS cluster with managed node groups
- IAM roles and policies
- Security groups
- VPC endpoints

### 2. Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name darts-eks-cluster
kubectl get nodes
```

### 3. Deploy Application with Helm

```bash
# Build and push Docker images to ECR
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/darts-app:v1.0.0 .
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/darts-app:v1.0.0

# Deploy with Helm
helm install darts-app ./helm/darts-app \
  --namespace darts-app \
  --create-namespace \
  --values ./helm/darts-app/values-production.yaml
```

### 4. Verify Deployment

```bash
kubectl get pods -n darts-app
kubectl get svc -n darts-app
kubectl get ingress -n darts-app
```

## 📊 Architecture Overview

```
Internet → ALB → Darts App (2-10 pods) → PostgreSQL (StatefulSet)
              ↓                        ↓
         API Gateway (2-8 pods)    RabbitMQ (StatefulSet)
              ↓                        ↓
         WSO2 Identity Server      Monitoring (Prometheus/Grafana)
                                      ↓
                                   Logging (Fluent Bit → CloudWatch)
```

### Key Components

- **Darts App**: Flask + Socket.IO application with auto-scaling (2-10 replicas)
- **API Gateway**: REST API with OAuth2 authentication (2-8 replicas)
- **PostgreSQL**: Database with persistent storage (20Gi)
- **RabbitMQ**: Message broker with persistent storage (10Gi)
- **WSO2 IS**: Identity and access management
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Fluent Bit**: Log collection and forwarding to CloudWatch

## 🔧 Configuration

### Secrets Management

**⚠️ IMPORTANT**: The secrets in `k8s/base/secrets/` are templates only. In production:

1. **Option 1**: Use AWS Secrets Manager
   ```bash
   kubectl create secret generic darts-app-secrets \
     --from-literal=SECRET_KEY="your-secret-key" \
     --from-literal=DATABASE_PASSWORD="your-db-password" \
     -n darts-app
   ```

2. **Option 2**: Use Sealed Secrets
   ```bash
   kubeseal --format yaml < secrets.yaml > sealed-secrets.yaml
   kubectl apply -f sealed-secrets.yaml
   ```

3. **Option 3**: Use External Secrets Operator
   - Install ESO
   - Configure AWS Secrets Manager backend
   - Create ExternalSecret resources

### Environment-Specific Values

#### Development
```bash
helm install darts-app ./helm/darts-app \
  --values ./helm/darts-app/values-development.yaml
```

#### Production
```bash
helm install darts-app ./helm/darts-app \
  --values ./helm/darts-app/values-production.yaml
```

## 📈 Monitoring & Logging

### Access Prometheus

```bash
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring
# Open http://localhost:9090
```

### Access Grafana

```bash
kubectl port-forward svc/grafana-service 3000:3000 -n monitoring
# Open http://localhost:3000
# Default credentials: admin/admin
```

### View Logs in CloudWatch

```bash
aws logs tail /aws/eks/darts-app/application --follow
```

### Import Grafana Dashboards

1. Kubernetes Cluster Monitoring: Dashboard ID 315
2. Node Exporter Full: Dashboard ID 1860
3. PostgreSQL Database: Dashboard ID 9628

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

#### Application Deployment (`deploy-eks.yml`)
- Triggers on push to `main` or `develop`
- Builds Docker images
- Pushes to Amazon ECR
- Deploys to EKS with Helm
- Runs smoke tests
- Automatic rollback on failure

#### Infrastructure Management (`terraform-eks.yml`)
- Validates Terraform code
- Plans infrastructure changes
- Applies on merge to `main`
- Supports manual destroy

### Setup GitHub Actions

1. Configure AWS credentials:
   ```bash
   # Create OIDC provider for GitHub Actions
   # Add IAM role ARN to GitHub secrets: AWS_ROLE_TO_ASSUME
   ```

2. Workflows run automatically on push/PR

3. Manual deployment:
   ```bash
   gh workflow run deploy-eks.yml -f environment=production
   ```

## ⚡ Scaling

### Horizontal Pod Autoscaling (HPA)

Configured to scale based on CPU and memory:

```bash
# View HPA status
kubectl get hpa -n darts-app

# Manually scale (overrides HPA)
kubectl scale deployment darts-app --replicas=5 -n darts-app
```

### Cluster Autoscaling

EKS node group auto-scales from 2 to 10 nodes based on resource requests.

## 🔒 Security

### Network Policies

Network policies are defined in `k8s/network-policies/` to:
- Restrict pod-to-pod communication
- Isolate namespaces
- Control ingress/egress traffic

Apply with:
```bash
kubectl apply -f k8s/network-policies/
```

### Pod Security

Implement Pod Security Standards:
```bash
kubectl label namespace darts-app pod-security.kubernetes.io/enforce=restricted
```

### Secrets Best Practices

1. Never commit actual secrets to Git
2. Use AWS Secrets Manager or Sealed Secrets
3. Enable encryption at rest with KMS
4. Rotate secrets regularly
5. Use least-privilege IAM roles

## 🛠️ Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n darts-app
kubectl logs <pod-name> -n darts-app
kubectl describe pod <pod-name> -n darts-app
```

### Test Service Connectivity

```bash
kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- \
  curl -v http://darts-app-service:5000/health
```

### View Cluster Events

```bash
kubectl get events -n darts-app --sort-by='.lastTimestamp'
```

### Database Connection Test

```bash
kubectl run psql-client --image=postgres:16-alpine --rm -i --restart=Never -- \
  psql -h postgres-service.darts-app.svc.cluster.local -U postgres -d dartsdb
```

### Helm Debug

```bash
helm list -n darts-app
helm status darts-app -n darts-app
helm rollback darts-app -n darts-app
```

## 💰 Cost Optimization

### Estimated Monthly Costs (Production)
- EKS Cluster: ~$73
- EC2 Instances (3 t3.medium): ~$100
- EBS Volumes: ~$20
- Load Balancer: ~$25
- Data Transfer: ~$20
- CloudWatch: ~$10
- **Total**: ~$250/month

### Optimization Tips
1. Use Spot Instances for dev/test
2. Right-size based on metrics
3. Use Savings Plans or Reserved Instances
4. Configure auto-scaling properly
5. Use gp3 instead of gp2 volumes

## 📚 Documentation

- [Deployment Guide](docs/KUBERNETES_DEPLOYMENT.md) - Step-by-step deployment instructions
- [Architecture Guide](docs/KUBERNETES_ARCHITECTURE.md) - Detailed architecture documentation
- [Main README](../README.md) - Application overview

## 🔄 Updates and Maintenance

### Update Application

```bash
# Build new image
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/darts-app:v1.1.0 .
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/darts-app:v1.1.0

# Update deployment
helm upgrade darts-app ./helm/darts-app \
  --set image.dartsApp.tag=v1.1.0 \
  -n darts-app
```

### Update Infrastructure

```bash
cd terraform
terraform plan
terraform apply
```

### Backup and Restore

#### Backup
```bash
# Create EBS snapshot
aws ec2 create-snapshot --volume-id <volume-id> --description "darts-db-backup"

# Export Kubernetes resources
kubectl get all -n darts-app -o yaml > backup.yaml
```

#### Restore
```bash
# Restore from snapshot
# Create volume from snapshot
# Update PVC to use new volume

# Restore resources
kubectl apply -f backup.yaml
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the [troubleshooting guide](docs/KUBERNETES_DEPLOYMENT.md#troubleshooting)
- Review the [architecture documentation](docs/KUBERNETES_ARCHITECTURE.md)

## 📝 License

See [LICENSE](../LICENSE) file in the root directory.

---

**Note**: This is a production-ready setup, but always review and customize configurations for your specific requirements and security policies.
