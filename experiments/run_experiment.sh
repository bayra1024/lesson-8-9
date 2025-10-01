#!/bin/bash

# MLOps Experiment Runner Script
# This script sets up the environment and runs the MLflow experiment

set -e

echo "🚀 Starting MLOps Experiment..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Set environment variables
export MLFLOW_TRACKING_URI="http://localhost:5000"
export PUSHGATEWAY_URL="http://localhost:9091"

echo "📋 Environment variables set:"
echo "   MLFLOW_TRACKING_URI: $MLFLOW_TRACKING_URI"
echo "   PUSHGATEWAY_URL: $PUSHGATEWAY_URL"

# Check if services are running
echo "🔍 Checking if services are running..."

# Check MLflow
if ! kubectl get svc -n mlflow mlflow &> /dev/null; then
    echo "❌ MLflow service not found. Please deploy the ArgoCD applications first."
    echo "   Run: kubectl apply -f ../argocd/applications/"
    exit 1
fi

# Check PushGateway
if ! kubectl get svc -n monitoring prometheus-pushgateway &> /dev/null; then
    echo "❌ Prometheus PushGateway service not found. Please deploy the ArgoCD applications first."
    echo "   Run: kubectl apply -f ../argocd/applications/"
    exit 1
fi

echo "✅ Services found. Setting up port forwarding..."

# Start port forwarding in background
echo "🌐 Starting port forwarding..."
kubectl port-forward -n mlflow svc/mlflow 5000:5000 &
MLFLOW_PID=$!

kubectl port-forward -n monitoring svc/prometheus-pushgateway 9091:9091 &
PUSHGATEWAY_PID=$!

# Wait for port forwarding to be ready
echo "⏳ Waiting for port forwarding to be ready..."
sleep 5

# Check if ports are accessible
if ! curl -s http://localhost:5000 > /dev/null; then
    echo "❌ MLflow is not accessible on localhost:5000"
    kill $MLFLOW_PID $PUSHGATEWAY_PID 2>/dev/null || true
    exit 1
fi

if ! curl -s http://localhost:9091 > /dev/null; then
    echo "❌ PushGateway is not accessible on localhost:9091"
    kill $MLFLOW_PID $PUSHGATEWAY_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Port forwarding is ready!"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create best_model directory
mkdir -p ../best_model

# Run the experiment
echo "🧪 Running MLflow experiment..."
python3 train_and_push.py

# Cleanup
echo "🧹 Cleaning up port forwarding..."
kill $MLFLOW_PID $PUSHGATEWAY_PID 2>/dev/null || true

echo "✅ Experiment completed!"
echo ""
echo "📊 Next steps:"
echo "   1. Open MLflow UI: http://localhost:5000"
echo "   2. Check metrics in Grafana"
echo "   3. View best model in: ../best_model/"
echo ""
echo "To access MLflow UI manually, run:"
echo "   kubectl port-forward -n mlflow svc/mlflow 5000:5000"
