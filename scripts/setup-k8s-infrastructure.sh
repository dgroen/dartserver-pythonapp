#!/bin/bash
# Quick setup script for Kubernetes infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="${CLUSTER_NAME:-darts-eks-cluster}"
NAMESPACE="${NAMESPACE:-darts-app}"
ENVIRONMENT="${ENVIRONMENT:-development}"

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    check_command "aws"
    print_success "AWS CLI is installed"
    
    check_command "kubectl"
    print_success "kubectl is installed"
    
    check_command "helm"
    print_success "Helm is installed"
    
    check_command "terraform"
    print_success "Terraform is installed"
    
    check_command "docker"
    print_success "Docker is installed"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure'"
        exit 1
    fi
    print_success "AWS credentials are configured"
}

# Create ECR repositories
create_ecr_repos() {
    print_header "Creating ECR Repositories"
    
    for repo in darts-app api-gateway; do
        if aws ecr describe-repositories --repository-names $repo --region $AWS_REGION &> /dev/null; then
            print_info "ECR repository '$repo' already exists"
        else
            aws ecr create-repository --repository-name $repo --region $AWS_REGION > /dev/null
            print_success "Created ECR repository '$repo'"
        fi
    done
}

# Initialize Terraform
init_terraform() {
    print_header "Initializing Terraform"
    
    cd terraform
    terraform init
    print_success "Terraform initialized"
    cd ..
}

# Create EKS cluster
create_eks_cluster() {
    print_header "Creating EKS Cluster"
    print_warning "This will take 15-20 minutes..."
    
    cd terraform
    terraform plan -out=tfplan
    terraform apply tfplan
    print_success "EKS cluster created"
    cd ..
}

# Configure kubectl
configure_kubectl() {
    print_header "Configuring kubectl"
    
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
    print_success "kubectl configured"
    
    kubectl get nodes
}

# Install cluster add-ons
install_addons() {
    print_header "Installing Cluster Add-ons"
    
    # Add Helm repos
    helm repo add eks https://aws.github.io/eks-charts
    helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
    helm repo add autoscaler https://kubernetes.github.io/autoscaler
    helm repo update
    print_success "Helm repositories added"
    
    # Install AWS Load Balancer Controller
    print_info "Installing AWS Load Balancer Controller..."
    helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName=$CLUSTER_NAME \
        --set serviceAccount.create=true \
        --set serviceAccount.name=aws-load-balancer-controller \
        --wait
    print_success "AWS Load Balancer Controller installed"
    
    # Install EBS CSI Driver
    print_info "Installing EBS CSI Driver..."
    helm upgrade --install aws-ebs-csi-driver aws-ebs-csi-driver/aws-ebs-csi-driver \
        -n kube-system \
        --set enableVolumeScheduling=true \
        --set enableVolumeResizing=true \
        --set enableVolumeSnapshot=true \
        --wait
    print_success "EBS CSI Driver installed"
    
    # Install Cluster Autoscaler
    print_info "Installing Cluster Autoscaler..."
    helm upgrade --install cluster-autoscaler autoscaler/cluster-autoscaler \
        -n kube-system \
        --set autoDiscovery.clusterName=$CLUSTER_NAME \
        --set awsRegion=$AWS_REGION \
        --wait
    print_success "Cluster Autoscaler installed"
}

# Build and push Docker images
build_and_push_images() {
    print_header "Building and Pushing Docker Images"
    
    # Get ECR registry URL
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    # Login to ECR
    print_info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $ECR_REGISTRY
    print_success "Logged in to ECR"
    
    # Build images
    print_info "Building Docker images..."
    docker build -t ${ECR_REGISTRY}/darts-app:latest -f Dockerfile .
    docker build -t ${ECR_REGISTRY}/api-gateway:latest -f Dockerfile.gateway .
    print_success "Docker images built"
    
    # Push images
    print_info "Pushing Docker images to ECR..."
    docker push ${ECR_REGISTRY}/darts-app:latest
    docker push ${ECR_REGISTRY}/api-gateway:latest
    print_success "Docker images pushed to ECR"
}

# Deploy application
deploy_application() {
    print_header "Deploying Application with Helm"
    
    # Select values file based on environment
    VALUES_FILE="values-${ENVIRONMENT}.yaml"
    
    print_info "Deploying to $ENVIRONMENT environment..."
    helm upgrade --install darts-app ./helm/darts-app \
        --namespace $NAMESPACE \
        --create-namespace \
        --values ./helm/darts-app/$VALUES_FILE \
        --wait \
        --timeout 10m
    print_success "Application deployed"
}

# Install monitoring
install_monitoring() {
    print_header "Installing Monitoring Stack"
    
    kubectl apply -f k8s/monitoring/prometheus.yaml
    kubectl apply -f k8s/monitoring/grafana.yaml
    print_success "Monitoring stack installed"
    
    print_info "Waiting for monitoring pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=300s
    kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s
    print_success "Monitoring stack is ready"
}

# Install logging
install_logging() {
    print_header "Installing Logging Stack"
    
    kubectl apply -f k8s/logging/fluent-bit.yaml
    print_success "Logging stack installed"
    
    print_info "Waiting for Fluent Bit pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=fluent-bit -n logging --timeout=300s
    print_success "Logging stack is ready"
}

# Verify deployment
verify_deployment() {
    print_header "Verifying Deployment"
    
    print_info "Checking pod status..."
    kubectl get pods -n $NAMESPACE
    
    print_info "Checking service status..."
    kubectl get svc -n $NAMESPACE
    
    print_info "Checking HPA status..."
    kubectl get hpa -n $NAMESPACE
    
    print_info "Running smoke tests..."
    if ./scripts/smoke-tests.sh; then
        print_success "All smoke tests passed"
    else
        print_warning "Some smoke tests failed. Check the output above."
    fi
}

# Print summary
print_summary() {
    print_header "Setup Complete!"
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    echo -e "${GREEN}🎉 Kubernetes infrastructure is ready!${NC}"
    echo ""
    echo "Cluster Information:"
    echo "  Region: $AWS_REGION"
    echo "  Cluster: $CLUSTER_NAME"
    echo "  Namespace: $NAMESPACE"
    echo "  Environment: $ENVIRONMENT"
    echo ""
    echo "ECR Repositories:"
    echo "  Darts App: ${ECR_REGISTRY}/darts-app:latest"
    echo "  API Gateway: ${ECR_REGISTRY}/api-gateway:latest"
    echo ""
    echo "Access URLs:"
    echo "  Application: Check ingress with 'kubectl get ingress -n $NAMESPACE'"
    echo "  Prometheus: kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring"
    echo "  Grafana: kubectl port-forward svc/grafana-service 3000:3000 -n monitoring"
    echo ""
    echo "Useful Commands:"
    echo "  make -f Makefile.k8s status      # Show cluster status"
    echo "  make -f Makefile.k8s logs-app    # View application logs"
    echo "  make -f Makefile.k8s top         # Show resource usage"
    echo ""
    echo "Documentation:"
    echo "  K8S_README.md                    # Quick reference"
    echo "  docs/KUBERNETES_DEPLOYMENT.md    # Detailed deployment guide"
    echo "  docs/KUBERNETES_ARCHITECTURE.md  # Architecture documentation"
    echo ""
}

# Main execution
main() {
    clear
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   Darts Application - Kubernetes Infrastructure Setup        ║
║                                                               ║
║   This script will set up a complete Kubernetes              ║
║   infrastructure on AWS EKS with monitoring and logging      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    print_warning "This script will create AWS resources that incur costs."
    print_warning "Estimated cost: ~$250/month for production setup"
    echo ""
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Setup cancelled"
        exit 0
    fi
    
    # Run setup steps
    check_prerequisites
    create_ecr_repos
    init_terraform
    create_eks_cluster
    configure_kubectl
    install_addons
    build_and_push_images
    deploy_application
    install_monitoring
    install_logging
    verify_deployment
    print_summary
}

# Run main function
main "$@"
