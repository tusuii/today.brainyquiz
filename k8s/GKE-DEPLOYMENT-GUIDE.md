# Deploying Exam App to Google Kubernetes Engine (GKE)

This guide provides step-by-step instructions for deploying the Exam App to a GKE cluster with HTTPS enabled using the `brainyquiz.today` domain.

## Prerequisites

Before you begin, make sure you have the following:

1. A Google Cloud Platform (GCP) account with billing enabled
2. The `gcloud` CLI installed and configured
3. `kubectl` installed
4. `docker` installed
5. `helm` installed (for cert-manager)
6. Ownership of the `brainyquiz.today` domain or access to its DNS settings

## Step 1: Prepare Your Environment

1. Clone this repository (if you haven't already)
2. Navigate to the project directory
3. Make the deployment scripts executable:

```bash
chmod +x k8s/deploy-gke.sh k8s/setup-cert-manager.sh
```

4. Edit the `k8s/deploy-gke.sh` script to set your GCP project ID:

```bash
PROJECT_ID="YOUR_GCP_PROJECT_ID"  # Replace with your actual GCP project ID
```

5. Edit the `k8s/setup-cert-manager.sh` script to set your email address:

```bash
EMAIL="your-email@example.com"  # Replace with your actual email
```

## Step 2: Deploy the Application to GKE

Run the GKE deployment script:

```bash
./k8s/deploy-gke.sh
```

This script will:
- Create a GKE cluster if it doesn't exist
- Build and push the Docker image to Google Container Registry (GCR)
- Deploy all Kubernetes resources (PostgreSQL, RabbitMQ, web app, Celery worker, Flower)
- Set up the Ingress with a temporary TLS certificate

After the script completes, it will display the external IP address assigned to your Ingress.

## Step 3: Configure DNS for Your Domain

1. Go to your domain registrar's website or DNS provider
2. Add an A record for `brainyquiz.today` pointing to the external IP address displayed by the deployment script
3. (Optional) Add a CNAME record for `www.brainyquiz.today` pointing to `brainyquiz.today`
4. Wait for DNS propagation (this can take up to 24-48 hours, but often happens within minutes)

You can check DNS propagation using:

```bash
dig brainyquiz.today
```

## Step 4: Set Up Automatic TLS Certificates with Let's Encrypt

Once your DNS is properly configured and propagated, run the cert-manager setup script:

```bash
./k8s/setup-cert-manager.sh
```

This script will:
- Install cert-manager in your cluster
- Configure a Let's Encrypt ClusterIssuer
- Update your Ingress to use cert-manager for automatic certificate provisioning

The certificate will be automatically provisioned once Let's Encrypt can verify that you control the domain.

## Step 5: Verify the Deployment

1. Open a web browser and navigate to `https://brainyquiz.today`
2. You should see your Exam App running with a valid HTTPS certificate
3. The Flower UI should be accessible at `https://brainyquiz.today/flower`

## Troubleshooting

### Certificate Issues

If the certificate isn't being issued:

1. Check certificate status:
```bash
kubectl get certificate -n exam-app
```

2. Check certificate request status:
```bash
kubectl get certificaterequest -n exam-app
```

3. Check challenges:
```bash
kubectl get challenge -n exam-app
```

### Ingress Issues

If you can't access your application:

1. Check the Ingress status:
```bash
kubectl describe ingress exam-app-ingress -n exam-app
```

2. Check Ingress controller logs:
```bash
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### Application Issues

If the application pods aren't starting:

1. Check pod status:
```bash
kubectl get pods -n exam-app
```

2. Check pod logs:
```bash
kubectl logs -n exam-app deploy/web
kubectl logs -n exam-app deploy/celery-worker
kubectl logs -n exam-app deploy/flower
```

## Maintenance and Updates

To update your application:

1. Make changes to your code
2. Build and push a new Docker image with a new tag
3. Update the deployment files with the new image tag
4. Apply the updated deployment files:
```bash
kubectl apply -f k8s/base/web-deployment.yaml
kubectl apply -f k8s/base/celery-worker-deployment.yaml
kubectl apply -f k8s/base/flower-deployment.yaml
```

## Cleanup

To delete the entire deployment:

```bash
kubectl delete namespace exam-app
```

To delete just the GKE cluster:

```bash
gcloud container clusters delete exam-app-cluster --zone us-central1-a
```

## Additional Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
