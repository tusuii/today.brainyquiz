#!/bin/bash

# Exit on any error
set -e

echo "Starting Minikube deployment for Exam App..."

# Check if minikube is running
if ! minikube status &>/dev/null; then
  echo "Starting Minikube..."
  minikube start
else
  echo "Minikube is already running."
fi

# Enable ingress addon
echo "Enabling Ingress addon..."
minikube addons enable ingress

# Set docker env to use minikube's docker daemon
echo "Setting docker environment to use Minikube's docker daemon..."
eval $(minikube docker-env)

# Build the Docker image
echo "Building Docker image..."
docker build -t exam-app:latest .

# Create namespace and apply Kubernetes resources
echo "Applying Kubernetes manifests..."
kubectl apply -k k8s/base

# Wait for deployments to be ready
echo "Waiting for deployments to be ready..."
kubectl wait --namespace exam-app --for=condition=available --timeout=300s deployment/web
kubectl wait --namespace exam-app --for=condition=available --timeout=300s deployment/postgres
kubectl wait --namespace exam-app --for=condition=available --timeout=300s deployment/rabbitmq
kubectl wait --namespace exam-app --for=condition=available --timeout=300s deployment/celery-worker
kubectl wait --namespace exam-app --for=condition=available --timeout=300s deployment/flower

# Get the URL to access the application
echo "Getting application URL..."
minikube service web -n exam-app --url

echo "Deployment completed successfully!"
echo "You can access the application at the URL above."
echo "To access the Flower dashboard, use: minikube service flower -n exam-app --url"
