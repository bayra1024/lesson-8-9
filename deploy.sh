#!/bin/bash

# MLOps Infrastructure Deployment Script
# This script deploys all ArgoCD applications for the MLOps stack

set -e

echo "🚀 Deploying MLOps Infrastructure..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if ArgoCD is running
if ! kubectl get pods -n argocd &> /dev/null; then
    echo "❌ ArgoCD is not running. Please install ArgoCD first."
    echo "   Follow: https://argo-cd.readthedocs.io/en/stable/getting_started/"
    exit 1
fi

echo "✅ ArgoCD is running"

# Apply all ArgoCD applications
echo "📦 Deploying ArgoCD applications..."

echo "   Deploying MinIO..."
kubectl apply -f argocd/applications/minio.yaml

echo "   Deploying PostgreSQL..."
kubectl apply -f argocd/applications/postgres.yaml

echo "   Deploying MLflow Secrets..."
kubectl apply -f argocd/applications/mlflow-secrets.yaml

echo "   Deploying MLflow..."
kubectl apply -f argocd/applications/mlflow.yaml

echo "   Deploying Prometheus PushGateway..."
kubectl apply -f argocd/applications/pushgateway.yaml

echo "✅ All applications deployed!"

# Wait for applications to be ready
echo "⏳ Waiting for applications to be ready..."

echo "   Waiting for MinIO..."
kubectl wait --for=condition=available --timeout=300s deployment/minio -n mlflow

echo "   Waiting for PostgreSQL..."
kubectl wait --for=condition=available --timeout=300s deployment/postgres-postgresql -n mlflow

echo "   Waiting for MLflow..."
kubectl wait --for=condition=available --timeout=300s deployment/mlflow -n mlflow

echo "   Waiting for PushGateway..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus-pushgateway -n monitoring

echo "✅ All applications are ready!"

# Show status
echo ""
echo "📊 Application Status:"
echo "====================="
kubectl get applications -n argocd

echo ""
echo "🔍 Pod Status:"
echo "============="
kubectl get pods -n mlflow
kubectl get pods -n monitoring

echo ""
echo "🌐 Services:"
echo "==========="
kubectl get svc -n mlflow
kubectl get svc -n monitoring

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Run experiments: cd experiments && ./run_experiment.sh"
echo "   2. Access MLflow UI: kubectl port-forward -n mlflow svc/mlflow 5000:5000"
echo "   3. Access PushGateway: kubectl port-forward -n monitoring svc/prometheus-pushgateway 9091:9091"
echo ""
echo "🔗 URLs (after port-forwarding):"
echo "   MLflow UI: http://localhost:5000"
echo "   PushGateway: http://localhost:9091"
echo "   MinIO: http://localhost:9000 (admin/minioadmin123)"
