#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
EMAIL="your-email@example.com"  # Replace with your email for Let's Encrypt notifications
DOMAIN="brainyquiz.today"

echo -e "${YELLOW}Setting up cert-manager for automatic TLS certificates...${NC}"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}You can install helm with: curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash${NC}"
    exit 1
fi

# Add the Jetstack Helm repository
echo -e "${GREEN}Adding Jetstack Helm repository...${NC}"
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager using Helm
echo -e "${GREEN}Installing cert-manager...${NC}"
kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --version v1.13.1 \
  --set installCRDs=true

# Wait for cert-manager to be ready
echo -e "${GREEN}Waiting for cert-manager to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s

# Create ClusterIssuer for Let's Encrypt
echo -e "${GREEN}Creating Let's Encrypt ClusterIssuer...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ${EMAIL}
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update the Ingress to use cert-manager for automatic TLS certificates
echo -e "${GREEN}Updating Ingress to use cert-manager...${NC}"
cat <<EOF > k8s/base/ingress-cert-manager.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: exam-app-ingress
  namespace: exam-app
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - ${DOMAIN}
    secretName: exam-app-tls-cert-manager
  rules:
  - host: ${DOMAIN}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
      - path: /flower
        pathType: Prefix
        backend:
          service:
            name: flower
            port:
              number: 5555
EOF

# Apply the updated Ingress
kubectl apply -f k8s/base/ingress-cert-manager.yaml

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}cert-manager setup complete!${NC}"
echo -e "${YELLOW}The certificate will be automatically provisioned once the domain ${DOMAIN} is pointed to your cluster's external IP.${NC}"
echo -e "${GREEN}==================================================${NC}"
