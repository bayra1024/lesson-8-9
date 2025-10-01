#!/usr/bin/env python3
"""
MLflow Experiment Tracking with Prometheus PushGateway Integration

This script trains multiple ML models with different hyperparameters,
tracks experiments in MLflow, and pushes metrics to Prometheus PushGateway.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss
import mlflow
import mlflow.sklearn
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import pickle
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
PUSHGATEWAY_URL = os.getenv('PUSHGATEWAY_URL', 'http://localhost:9091')
EXPERIMENT_NAME = 'iris_classification'
BEST_MODEL_DIR = '../best_model'

# Hyperparameter search space
HYPERPARAMETERS = [
    {'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 2},
    {'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2},
    {'n_estimators': 150, 'max_depth': 7, 'min_samples_split': 2},
    {'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 5},
    {'n_estimators': 200, 'max_depth': 10, 'min_samples_split': 2},
    {'n_estimators': 100, 'max_depth': 3, 'min_samples_split': 10},
]

def load_data():
    """Load and prepare the Iris dataset."""
    logger.info("Loading Iris dataset...")
    iris = load_iris()
    X, y = iris.data, iris.target
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Dataset loaded: {X_train.shape[0]} train samples, {X_test.shape[0]} test samples")
    return X_train, X_test, y_train, y_test

def train_model(X_train, X_test, y_train, y_test, params, run_id):
    """Train a RandomForest model with given parameters."""
    logger.info(f"Training model with parameters: {params}")
    
    # Create and train the model
    model = RandomForestClassifier(
        n_estimators=params['n_estimators'],
        max_depth=params['max_depth'],
        min_samples_split=params['min_samples_split'],
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    loss = log_loss(y_test, y_pred_proba)
    
    logger.info(f"Model trained - Accuracy: {accuracy:.4f}, Loss: {loss:.4f}")
    
    return model, accuracy, loss

def push_metrics_to_prometheus(accuracy, loss, run_id):
    """Push metrics to Prometheus PushGateway."""
    try:
        registry = CollectorRegistry()
        
        # Create metrics
        accuracy_gauge = Gauge('mlflow_accuracy', 'Model accuracy from MLflow', 
                              ['run_id', 'experiment'], registry=registry)
        loss_gauge = Gauge('mlflow_loss', 'Model loss from MLflow', 
                          ['run_id', 'experiment'], registry=registry)
        
        # Set metric values
        accuracy_gauge.labels(run_id=run_id, experiment=EXPERIMENT_NAME).set(accuracy)
        loss_gauge.labels(run_id=run_id, experiment=EXPERIMENT_NAME).set(loss)
        
        # Push to gateway
        push_to_gateway(PUSHGATEWAY_URL, job='mlflow_experiments', registry=registry)
        logger.info(f"Metrics pushed to Prometheus PushGateway for run {run_id}")
        
    except Exception as e:
        logger.error(f"Failed to push metrics to Prometheus: {e}")

def save_best_model(best_model, best_run_id):
    """Save the best model to local directory."""
    os.makedirs(BEST_MODEL_DIR, exist_ok=True)
    
    model_path = os.path.join(BEST_MODEL_DIR, f'best_model_{best_run_id}.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    
    logger.info(f"Best model saved to {model_path}")

def main():
    """Main training and tracking function."""
    logger.info("Starting MLflow experiment tracking...")
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Create or get experiment
    try:
        experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
        logger.info(f"Created new experiment: {EXPERIMENT_NAME}")
    except mlflow.exceptions.MlflowException:
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        experiment_id = experiment.experiment_id
        logger.info(f"Using existing experiment: {EXPERIMENT_NAME}")
    
    # Load data
    X_train, X_test, y_train, y_test = load_data()
    
    # Track best model
    best_accuracy = 0
    best_model = None
    best_run_id = None
    
    # Train models with different hyperparameters
    for i, params in enumerate(HYPERPARAMETERS):
        with mlflow.start_run(experiment_id=experiment_id) as run:
            run_id = run.info.run_id
            logger.info(f"Starting run {i+1}/{len(HYPERPARAMETERS)}: {run_id}")
            
            # Log parameters
            mlflow.log_params(params)
            mlflow.log_param('run_number', i+1)
            mlflow.log_param('timestamp', datetime.now().isoformat())
            
            # Train model
            model, accuracy, loss = train_model(X_train, X_test, y_train, y_test, params, run_id)
            
            # Log metrics
            mlflow.log_metric('accuracy', accuracy)
            mlflow.log_metric('loss', loss)
            
            # Log model
            mlflow.sklearn.log_model(model, "model")
            
            # Log additional metadata
            mlflow.log_param('dataset', 'iris')
            mlflow.log_param('test_size', 0.2)
            mlflow.log_param('random_state', 42)
            
            # Push metrics to Prometheus
            push_metrics_to_prometheus(accuracy, loss, run_id)
            
            # Track best model
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model = model
                best_run_id = run_id
                logger.info(f"New best model found! Accuracy: {accuracy:.4f}")
    
    # Save best model
    if best_model is not None:
        save_best_model(best_model, best_run_id)
        logger.info(f"Experiment completed! Best accuracy: {best_accuracy:.4f} (Run: {best_run_id})")
    else:
        logger.error("No model was trained successfully!")
        sys.exit(1)

if __name__ == "__main__":
    main()
