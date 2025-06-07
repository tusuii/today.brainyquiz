# Kubernetes Deployment for Exam App

This directory contains Kubernetes manifests and deployment scripts for running the Exam App on Kubernetes. The configuration is designed to work with Minikube for local development and GKE/EKS for cloud deployments.

## Directory Structure

- `base/`: Contains the base Kubernetes manifests
  - `namespace.yaml`: Creates a dedicated namespace for the application
  - `secrets.yaml`: Stores database credentials securely
  - `postgres-*.yaml`: Database components
  - `rabbitmq-*.yaml`: Message broker components
  - `web-*.yaml`: Web application components
  - `celery-worker-deployment.yaml`: Background processing component
  - `flower-*.yaml`: Celery monitoring UI components
  - `ingress.yaml`: Exposes the web app on port 80
  - `kustomization.yaml`: Ties all resources together

- `deploy-minikube.sh`: Script for local deployment with Minikube
- `deploy-cloud.sh`: Script for deploying to GKE or EKS

## Prerequisites

- Docker
- kubectl
- Minikube (for local development)
- Google Cloud SDK (for GKE deployment)
- AWS CLI (for EKS deployment)

## Local Deployment with Minikube

To deploy the application locally with Minikube:

```bash
./deploy-minikube.sh
```

This script will:
1. Start Minikube if it's not running
2. Enable the Ingress addon
3. Build the Docker image using Minikube's Docker daemon
4. Deploy all Kubernetes resources
5. Wait for deployments to be ready
6. Display the URL to access the application

## Cloud Deployment (GKE or EKS)

To deploy the application to GKE:

```bash
./deploy-cloud.sh --provider gke --registry gcr.io/your-project-id
```

To deploy the application to EKS:

```bash
./deploy-cloud.sh --provider eks --registry your-aws-account-id.dkr.ecr.region.amazonaws.com/exam-app
```

Additional options:
- `--tag`: Specify a custom image tag (default: latest)
- `--namespace`: Specify a custom namespace (default: exam-app)

## Accessing the Application

- Web Application: Access through the Ingress IP address or domain
- Flower UI: Access at `<ingress-address>/flower`
- RabbitMQ Management UI: Not exposed by default for security reasons

## Scaling

To scale the web application or Celery workers:

```bash
kubectl scale deployment/web -n exam-app --replicas=3
kubectl scale deployment/celery-worker -n exam-app --replicas=5
```

## Monitoring

- Use Flower UI to monitor Celery tasks
- Use Kubernetes Dashboard or cloud provider's monitoring tools for cluster monitoring

## Troubleshooting

If you encounter issues:

1. Check pod status:
   ```bash
   kubectl get pods -n exam-app
   ```

2. View pod logs:
   ```bash
   kubectl logs <pod-name> -n exam-app
   ```

3. Check service endpoints:
   ```bash
   kubectl get endpoints -n exam-app
   ```

4. Verify ingress configuration:
   ```bash
   kubectl describe ingress exam-app-ingress -n exam-app
   ```
