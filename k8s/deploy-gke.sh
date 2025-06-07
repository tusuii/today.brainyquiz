#!/bin/bash
set -e

# Configuration
PROJECT_ID="YOUR_GCP_PROJECT_ID"  # Replace with your GCP project ID
CLUSTER_NAME="exam-app-cluster"
CLUSTER_ZONE="us-central1-a"
CLUSTER_VERSION="1.27"  # Specify the Kubernetes version
MACHINE_TYPE="e2-standard-2"
NUM_NODES=2
REGISTRY="gcr.io/${PROJECT_ID}"
IMAGE_NAME="exam-app"
IMAGE_TAG="latest"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Deploying Exam App to Google Kubernetes Engine...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Configure gcloud
echo -e "${GREEN}Configuring gcloud...${NC}"
gcloud config set project ${PROJECT_ID}

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${YELLOW}Please login to Google Cloud:${NC}"
    gcloud auth login
fi

# Enable required APIs
echo -e "${GREEN}Enabling required GCP APIs...${NC}"
gcloud services enable container.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com

# Check if cluster exists, create if it doesn't
echo -e "${GREEN}Checking for existing GKE cluster...${NC}"
if ! gcloud container clusters list --filter="name=${CLUSTER_NAME}" --format="value(name)" | grep -q "${CLUSTER_NAME}"; then
    echo -e "${GREEN}Creating GKE cluster ${CLUSTER_NAME}...${NC}"
    gcloud container clusters create ${CLUSTER_NAME} \
        --zone ${CLUSTER_ZONE} \
        --cluster-version ${CLUSTER_VERSION} \
        --machine-type ${MACHINE_TYPE} \
        --num-nodes ${NUM_NODES} \
        --enable-ip-alias \
        --enable-autoscaling \
        --min-nodes 1 \
        --max-nodes 3
else
    echo -e "${GREEN}Cluster ${CLUSTER_NAME} already exists.${NC}"
fi

# Get credentials for the cluster
echo -e "${GREEN}Getting credentials for cluster...${NC}"
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${CLUSTER_ZONE}

# Build and push Docker image
echo -e "${GREEN}Building and pushing Docker image...${NC}"
docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

# Update image in deployment files
echo -e "${GREEN}Updating deployment files with GCR image...${NC}"
sed -i "s|image: exam-app:latest|image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/base/web-deployment.yaml
sed -i "s|image: exam-app:latest|image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/base/celery-worker-deployment.yaml
sed -i "s|image: exam-app:latest|image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/base/flower-deployment.yaml

# Create exam-app namespace if it doesn't exist
echo -e "${GREEN}Creating namespace...${NC}"
kubectl create namespace exam-app --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
echo -e "${GREEN}Applying Kubernetes manifests...${NC}"
kubectl apply -f k8s/base/secrets.yaml
kubectl apply -f k8s/base/postgres-pvc.yaml
kubectl apply -f k8s/base/rabbitmq-pvc.yaml
kubectl apply -f k8s/base/postgres-deployment.yaml
kubectl apply -f k8s/base/postgres-service.yaml
kubectl apply -f k8s/base/rabbitmq-deployment.yaml
kubectl apply -f k8s/base/rabbitmq-service.yaml

echo -e "${GREEN}Waiting for database and message broker to be ready...${NC}"
kubectl rollout status deployment/postgres -n exam-app --timeout=180s
kubectl rollout status deployment/rabbitmq -n exam-app --timeout=180s

echo -e "${GREEN}Deploying application components...${NC}"
kubectl apply -f k8s/base/web-deployment.yaml
kubectl apply -f k8s/base/web-service.yaml
kubectl apply -f k8s/base/celery-worker-deployment.yaml
kubectl apply -f k8s/base/flower-deployment.yaml
kubectl apply -f k8s/base/flower-service.yaml

echo -e "${GREEN}Waiting for application components to be ready...${NC}"
kubectl rollout status deployment/web -n exam-app --timeout=180s
kubectl rollout status deployment/celery-worker -n exam-app --timeout=180s
kubectl rollout status deployment/flower -n exam-app --timeout=180s

echo -e "${GREEN}Setting up Ingress with TLS...${NC}"
kubectl apply -f k8s/base/ingress.yaml

# Get the external IP of the Ingress
echo -e "${GREEN}Waiting for Ingress to get an external IP...${NC}"
external_ip=""
while [ -z $external_ip ]; do
  echo "Waiting for external IP..."
  external_ip=$(kubectl get ingress exam-app-ingress -n exam-app --template="{{range .status.loadBalancer.ingress}}{{.ip}}{{end}}")
  [ -z "$external_ip" ] && sleep 10
done

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}External IP: ${external_ip}${NC}"
echo -e "${YELLOW}To access your application, configure your DNS provider to point brainyquiz.today to ${external_ip}${NC}"
echo -e "${GREEN}==================================================${NC}"
