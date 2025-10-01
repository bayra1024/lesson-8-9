#!/usr/bin/env python3
"""
Демонстрація збереження найкращої моделі
Цей скрипт показує, як працює логіка вибору та збереження найкращої моделі
"""

import os
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle
from datetime import datetime

# Конфігурація
BEST_MODEL_DIR = '../best_model'

# Тестові параметри
HYPERPARAMETERS = [
    {'n_estimators': 50, 'max_depth': 3, 'min_samples_split': 2},
    {'n_estimators': 100, 'max_depth': 5, 'min_samples_split': 2},
    {'n_estimators': 150, 'max_depth': 7, 'min_samples_split': 2},
]

def train_model(X_train, X_test, y_train, y_test, params):
    """Тренування моделі з заданими параметрами"""
    print(f"Тренування моделі з параметрами: {params}")
    
    model = RandomForestClassifier(
        n_estimators=params['n_estimators'],
        max_depth=params['max_depth'],
        min_samples_split=params['min_samples_split'],
        random_state=42
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Точність моделі: {accuracy:.4f}")
    return model, accuracy

def save_best_model(best_model, best_accuracy, run_id):
    """Збереження найкращої моделі"""
    os.makedirs(BEST_MODEL_DIR, exist_ok=True)
    
    model_path = os.path.join(BEST_MODEL_DIR, f'best_model_{run_id}.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    
    print(f"✅ Найкраща модель збережена в: {model_path}")
    print(f"   Точність: {best_accuracy:.4f}")
    print(f"   Run ID: {run_id}")

def main():
    """Головна функція демонстрації"""
    print("🚀 Демонстрація збереження найкращої моделі")
    print("=" * 50)
    
    # Завантаження даних
    print("📊 Завантаження даних Iris...")
    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Ініціалізація змінних для найкращої моделі
    best_accuracy = 0
    best_model = None
    best_run_id = None
    
    print(f"📈 Тренування {len(HYPERPARAMETERS)} моделей...")
    print()
    
    # Тренування моделей
    for i, params in enumerate(HYPERPARAMETERS):
        run_id = f"demo_run_{i+1}_{datetime.now().strftime('%H%M%S')}"
        print(f"--- Run {i+1}: {run_id} ---")
        
        model, accuracy = train_model(X_train, X_test, y_train, y_test, params)
        
        # Перевірка, чи це найкраща модель
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model = model
            best_run_id = run_id
            print(f"🎯 Нова найкраща модель! Точність: {accuracy:.4f}")
        else:
            print(f"📉 Модель гірша за поточну найкращу ({best_accuracy:.4f})")
        
        print()
    
    # Збереження найкращої моделі
    if best_model is not None:
        save_best_model(best_model, best_accuracy, best_run_id)
        
        # Перевірка збереження
        print("\n🔍 Перевірка збереження:")
        if os.path.exists(BEST_MODEL_DIR):
            files = os.listdir(BEST_MODEL_DIR)
            print(f"   Файли в {BEST_MODEL_DIR}:")
            for file in files:
                print(f"   - {file}")
        else:
            print("   ❌ Директорія не існує")
    else:
        print("❌ Не вдалося натренувати жодної моделі")
    
    print("\n✅ Демонстрація завершена!")

if __name__ == "__main__":
    main()
