# Kubernetes Architecture for Darts Application

## Overview

This document describes the Kubernetes architecture for the Darts Game application deployed on AWS EKS with high availability, auto-scaling, monitoring, and logging capabilities.

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                               Internet / Users                                │
└─────────────────────────────────┬─────────────────────────────────────────────┘
                                  │
                                  │ HTTPS
                                  │
┌─────────────────────────────────▼─────────────────────────────────────────────┐
│                          AWS Route 53 (DNS)                                   │
└─────────────────────────────────┬─────────────────────────────────────────────┘
                                  │
                                  │
┌─────────────────────────────────▼─────────────────────────────────────────────┐
│                    Application Load Balancer (ALB)                            │
│                     SSL Termination, Health Checks                            │
└───┬────────────────────────────────────────────────────────────────────────┬──┘
    │                                                                          │
    │                                                                          │
┌───▼──────────────────────────────────────────────────────────────────────────▼──┐
│                          AWS EKS Cluster (Kubernetes)                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         Namespace: darts-app                            │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                         │   │
│  │  ┌──────────────────┐              ┌──────────────────┐                │   │
│  │  │   Ingress        │              │  Nginx Service   │                │   │
│  │  │  (ALB Controller)│──────────────│   (Optional)     │                │   │
│  │  └────────┬─────────┘              └────────┬─────────┘                │   │
│  │           │                                  │                          │   │
│  │           ├──────────────────────────────────┼──────────────┐           │   │
│  │           │                                  │              │           │   │
│  │  ┌────────▼─────────┐            ┌──────────▼──────┐  ┌───▼───────┐   │   │
│  │  │  Darts App Svc   │            │ API Gateway Svc │  │ WSO2 Svc  │   │   │
│  │  │  (ClusterIP)     │            │   (ClusterIP)   │  │(ClusterIP)│   │   │
│  │  └────────┬─────────┘            └──────────┬──────┘  └───┬───────┘   │   │
│  │           │                                  │             │           │   │
│  │  ┌────────▼─────────────────┐    ┌──────────▼──────────────────┐      │   │
│  │  │   Darts App Deployment   │    │  API Gateway Deployment     │      │   │
│  │  │  ┌─────┐  ┌─────┐        │    │  ┌─────┐  ┌─────┐          │      │   │
│  │  │  │Pod1 │  │Pod2 │ ... 10 │    │  │Pod1 │  │Pod2 │ ... 8    │      │   │
│  │  │  └─────┘  └─────┘        │    │  └─────┘  └─────┘          │      │   │
│  │  │   HPA: 2-10 replicas     │    │   HPA: 2-8 replicas        │      │   │
│  │  └──────┬───────────────────┘    └──────────┬─────────────────┘      │   │
│  │         │                                    │                        │   │
│  │         ├────────────────────────────────────┼────────────────┐       │   │
│  │         │                                    │                │       │   │
│  │  ┌──────▼───────┐  ┌──────────────┐  ┌──────▼──────┐  ┌──────▼────┐  │   │
│  │  │  PostgreSQL  │  │   RabbitMQ   │  │  WSO2 IS    │  │ ConfigMap │  │   │
│  │  │ StatefulSet  │  │ StatefulSet  │  │ Deployment  │  │  Secrets  │  │   │
│  │  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐ │  └───────────┘  │   │
│  │  │  │ Pod-0  │  │  │  │ Pod-0  │  │  │  │ Pod-0  │ │                 │   │
│  │  │  └───┬────┘  │  │  └───┬────┘  │  │  └────────┘ │                 │   │
│  │  │      │       │  │      │       │  └─────────────┘                 │   │
│  │  │  ┌───▼────┐  │  │  ┌───▼────┐  │                                  │   │
│  │  │  │  PVC   │  │  │  │  PVC   │  │                                  │   │
│  │  │  │ 20Gi   │  │  │  │ 10Gi   │  │                                  │   │
│  │  │  └────────┘  │  │  └────────┘  │                                  │   │
│  │  └──────────────┘  └──────────────┘                                  │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                      Namespace: monitoring                            │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  ┌──────────────┐              ┌──────────────┐                      │   │
│  │  │  Prometheus  │──────────────│   Grafana    │                      │   │
│  │  │  Deployment  │  Scrapes     │  Deployment  │                      │   │
│  │  │              │◄─────────────│              │                      │   │
│  │  └──────┬───────┘              └──────────────┘                      │   │
│  │         │                                                            │   │
│  │         └─────────► Scrapes metrics from all pods                   │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                       Namespace: logging                              │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  ┌──────────────────────────────────────────────────────┐            │   │
│  │  │         Fluent Bit DaemonSet                         │            │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │            │   │
│  │  │  │  Pod-1  │  │  Pod-2  │  │  Pod-3  │              │            │   │
│  │  │  │ (Node1) │  │ (Node2) │  │ (Node3) │              │            │   │
│  │  │  └────┬────┘  └────┬────┘  └────┬────┘              │            │   │
│  │  │       │            │            │                    │            │   │
│  │  │       └────────────┴────────────┴──────► CloudWatch │            │   │
│  │  │                                          Logs        │            │   │
│  │  └──────────────────────────────────────────────────────┘            │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                    EKS Managed Node Group                             │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐        ┌──────────┐   │   │
│  │  │  Node 1  │    │  Node 2  │    │  Node 3  │  ....  │  Node N  │   │   │
│  │  │ t3.medium│    │ t3.medium│    │ t3.medium│        │ t3.large │   │   │
│  │  └──────────┘    └──────────┘    └──────────┘        └──────────┘   │   │
│  │                                                                       │   │
│  │  Auto-scaling: 2 - 10 nodes based on resource requests               │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  │
┌─────────────────────────────────▼─────────────────────────────────────────────┐
│                         AWS Supporting Services                               │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   ECR    │  │   EBS    │  │   IAM    │  │   KMS    │  │CloudWatch│      │
│  │Container │  │ Volumes  │  │  Roles   │  │Encryption│  │   Logs   │      │
│  │ Registry │  │  (gp3)   │  │          │  │          │  │  Metrics │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Application Layer

#### Darts App
- **Type**: Deployment
- **Replicas**: 2-10 (auto-scaling)
- **Resources**:
  - Requests: 256Mi memory, 100m CPU
  - Limits: 1Gi memory, 1000m CPU
- **Health Checks**: HTTP on port 5000
- **Features**:
  - Flask + Socket.IO for real-time communication
  - Connects to PostgreSQL, RabbitMQ, WSO2
  - Prometheus metrics exposed

#### API Gateway
- **Type**: Deployment
- **Replicas**: 2-8 (auto-scaling)
- **Resources**:
  - Requests: 128Mi memory, 50m CPU
  - Limits: 512Mi memory, 500m CPU
- **Health Checks**: HTTP on port 8080
- **Features**:
  - REST API with OAuth2 authentication
  - Rate limiting and request validation
  - Forwards events to RabbitMQ

### Data Layer

#### PostgreSQL
- **Type**: StatefulSet
- **Replicas**: 1 (can be scaled for read replicas)
- **Storage**: 20Gi persistent volume (gp3)
- **Resources**:
  - Requests: 512Mi memory, 250m CPU
  - Limits: 2Gi memory, 1000m CPU
- **Features**:
  - Persistent storage for game data
  - Automated backups (via AWS Backup)
  - Health checks with pg_isready

#### RabbitMQ
- **Type**: StatefulSet
- **Replicas**: 1 (can be clustered for HA)
- **Storage**: 10Gi persistent volume (gp3)
- **Resources**:
  - Requests: 512Mi memory, 250m CPU
  - Limits: 2Gi memory, 1000m CPU
- **Features**:
  - Message broker for event-driven architecture
  - Management UI on port 15672
  - Persistent message storage

### Authentication Layer

#### WSO2 Identity Server
- **Type**: Deployment
- **Replicas**: 1 (can be scaled)
- **Resources**:
  - Requests: 1Gi memory, 500m CPU
  - Limits: 2Gi memory, 1500m CPU
- **Features**:
  - OAuth2/OIDC provider
  - User management and authentication
  - Token introspection

### Networking

#### Ingress
- **Controller**: AWS ALB Ingress Controller
- **Type**: Application Load Balancer
- **Features**:
  - SSL/TLS termination
  - Path-based routing
  - Health checks
  - WAF integration (optional)

#### Services
- **ClusterIP**: Internal service discovery
- **LoadBalancer**: External access (Grafana)
- **Headless**: StatefulSet discovery

#### Network Policies
- Pod-to-pod communication rules
- Namespace isolation
- Deny-by-default security

### Observability

#### Monitoring (Prometheus + Grafana)
- **Prometheus**:
  - Scrapes metrics from all pods
  - Stores 30 days of metrics
  - Alert rules configured
  
- **Grafana**:
  - Visualization dashboards
  - Multi-datasource support
  - Alert notifications

#### Logging (Fluent Bit + CloudWatch)
- **Fluent Bit DaemonSet**:
  - Runs on every node
  - Collects container logs
  - Parses and enriches logs
  - Forwards to CloudWatch Logs

- **CloudWatch Logs**:
  - Centralized log storage
  - Log insights queries
  - Retention policies

### Auto-scaling

#### Horizontal Pod Autoscaler (HPA)
- Scales pods based on:
  - CPU utilization (70% threshold)
  - Memory utilization (80% threshold)
  - Custom metrics (optional)
- Scale-up: Fast (within 1 minute)
- Scale-down: Gradual (5-minute stabilization)

#### Cluster Autoscaler
- Scales nodes based on:
  - Pending pods (scale up)
  - Underutilized nodes (scale down)
- Min nodes: 2
- Max nodes: 10
- Scale decision delay: 10 seconds

### Security

#### Network Security
- VPC with public and private subnets
- Security groups for cluster and nodes
- Network policies for pod-to-pod communication
- Private API endpoint option

#### Identity and Access
- IAM roles for service accounts (IRSA)
- RBAC for Kubernetes resources
- Pod security policies
- KMS encryption for secrets

#### Data Security
- Encrypted EBS volumes
- TLS for all external traffic
- Secrets stored in Kubernetes Secrets
- Certificate management with ACM

## Resource Requirements

### Minimum Resources
- **Nodes**: 2 t3.medium instances
- **Total CPU**: 4 vCPUs
- **Total Memory**: 8 GiB
- **Storage**: 50 GiB per node + PVCs

### Production Resources
- **Nodes**: 3-10 t3.medium/large instances
- **Total CPU**: 8-20 vCPUs
- **Total Memory**: 16-40 GiB
- **Storage**: 50 GiB per node + 30+ GiB PVCs

### Storage Breakdown
- PostgreSQL: 20 GiB (expandable to 100 GiB)
- RabbitMQ: 10 GiB (expandable to 50 GiB)
- Logs: Variable (CloudWatch)
- Monitoring: ~5 GiB (Prometheus)

## High Availability Features

1. **Multi-AZ Deployment**: Nodes across 3 availability zones
2. **Pod Anti-Affinity**: Replicas on different nodes
3. **Health Checks**: Liveness and readiness probes
4. **Rolling Updates**: Zero-downtime deployments
5. **Auto-healing**: Automatic pod restart on failure
6. **Data Persistence**: PersistentVolumes with backups
7. **Load Balancing**: ALB with health checks

## Disaster Recovery

1. **Backup Strategy**:
   - Database backups (daily)
   - Volume snapshots (hourly)
   - Configuration in Git

2. **Recovery Time Objective (RTO)**: < 1 hour
3. **Recovery Point Objective (RPO)**: < 15 minutes

4. **Recovery Procedures**:
   - Restore from EBS snapshots
   - Redeploy from Git
   - Restore database from backup

## Performance Optimization

1. **Caching**: Redis for session storage (future enhancement)
2. **Connection Pooling**: Database connection management
3. **Resource Limits**: Prevent resource contention
4. **Horizontal Scaling**: Multiple replicas for load distribution
5. **CDN**: CloudFront for static assets (future enhancement)

## Cost Estimation

### Monthly Costs (Production)
- EKS Cluster: ~$73
- EC2 Instances (3 t3.medium): ~$100
- EBS Volumes: ~$20
- Load Balancer: ~$25
- Data Transfer: ~$20
- CloudWatch: ~$10
- **Total**: ~$250/month (approximate)

### Cost Optimization Tips
1. Use Spot Instances for non-critical workloads
2. Right-size instances based on metrics
3. Use Savings Plans or Reserved Instances
4. Monitor and optimize data transfer
5. Use gp3 instead of gp2 for EBS volumes

## Future Enhancements

1. **Multi-Region Deployment**: Global availability
2. **Service Mesh**: Istio for advanced traffic management
3. **GitOps**: ArgoCD for deployment automation
4. **Advanced Monitoring**: Custom metrics and SLOs
5. **Chaos Engineering**: Automated resilience testing
6. **Blue-Green Deployments**: Advanced deployment strategies
7. **Database Replication**: Read replicas for scaling
8. **Message Queue Clustering**: RabbitMQ HA cluster
