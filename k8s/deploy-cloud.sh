#!/bin/bash

# Exit on any error
set -e

# Default values
CLOUD_PROVIDER="gke"  # Options: gke, eks
IMAGE_REGISTRY=""
IMAGE_TAG="latest"
NAMESPACE="exam-app"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --provider)
      CLOUD_PROVIDER="$2"
      shift 2
      ;;
    --registry)
      IMAGE_REGISTRY="$2"
      shift 2
      ;;
    --tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$IMAGE_REGISTRY" ]]; then
  echo "Error: Image registry is required. Use --registry to specify."
  echo "Example: ./deploy-cloud.sh --provider gke --registry gcr.io/your-project"
  exit 1
fi

echo "Starting $CLOUD_PROVIDER deployment for Exam App..."
echo "Using image registry: $IMAGE_REGISTRY"
echo "Image tag: $IMAGE_TAG"

# Build and push Docker image
IMAGE_NAME="$IMAGE_REGISTRY/exam-app:$IMAGE_TAG"
echo "Building and pushing Docker image: $IMAGE_NAME"
docker build -t $IMAGE_NAME .

case $CLOUD_PROVIDER in
  gke)
    echo "Pushing to Google Container Registry..."
    docker push $IMAGE_NAME
    ;;
  eks)
    echo "Pushing to Amazon ECR..."
    # For ECR, you might need to login first
    # aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin $IMAGE_REGISTRY
    docker push $IMAGE_NAME
    ;;
  *)
    echo "Unsupported cloud provider: $CLOUD_PROVIDER"
    exit 1
    ;;
esac

# Create a temporary directory for customized manifests
TEMP_DIR=$(mktemp -d)
cp -r k8s/base/* $TEMP_DIR/

# Update the image in the deployments
for file in $TEMP_DIR/*deployment.yaml; do
  sed -i "s|image: exam-app:latest|image: $IMAGE_NAME|g" $file
  sed -i "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Always|g" $file
done

# Create namespace and apply Kubernetes resources
echo "Applying Kubernetes manifests..."
kubectl apply -f $TEMP_DIR/namespace.yaml
kubectl apply -f $TEMP_DIR/

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --namespace $NAMESPACE --for=condition=available --timeout=300s deployment/web
kubectl wait --namespace $NAMESPACE --for=condition=available --timeout=300s deployment/postgres
kubectl wait --namespace $NAMESPACE --for=condition=available --timeout=300s deployment/rabbitmq
kubectl wait --namespace $NAMESPACE --for=condition=available --timeout=300s deployment/celery-worker
kubectl wait --namespace $NAMESPACE --for=condition=available --timeout=300s deployment/flower

# Clean up temporary directory
rm -rf $TEMP_DIR

echo "Deployment completed successfully!"
echo "You can access the application through the load balancer or ingress."
echo "Run 'kubectl get ingress -n $NAMESPACE' to see the external IP."
