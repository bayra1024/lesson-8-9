#### 🏗️ Архітектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MLflow UI     │    │  PushGateway    │    │    Grafana      │
│   (Port 5000)   │    │  (Port 9091)    │    │   (Port 3000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐              ┌───▼───┐              ┌────▼────┐
    │PostgreSQL│             │Prometheus│           │Prometheus│
    │(Port 5432)│            │         │            │         │
    └─────────┘              └─────────┘            └─────────┘
         │
    ┌────▼────┐
    │  MinIO  │
    │(Port 9000)│
    └─────────┘
```

#### 📁 Структура проекту

```
mlops-experiments/
├── argocd/
│   └── applications/
│       ├── mlflow.yaml          # MLflow Tracking Server
│       ├── minio.yaml           # MinIO для артефактів
│       ├── postgres.yaml        # PostgreSQL для метаданих
│       ├── mlflow-secrets.yaml  # Секрети для підключення
│       └── pushgateway.yaml     # Prometheus PushGateway
├── experiments/
│   ├── train_and_push.py        # Скрипт тренування з трекінгом
│   └── requirements.txt         # Python залежності
├── best_model/                  # Найкраща модель (.pkl)
└── README.md
```

### 🚀 Швидкий старт

#### 1. Розгортання інфраструктури через ArgoCD

```bash
# Застосувати всі ArgoCD додатки
kubectl apply -f argocd/applications/

# Перевірити статус додатків
kubectl get applications -n argocd

# Перевірити поди
kubectl get pods -n mlflow
kubectl get pods -n monitoring
```

#### 2. Налаштування port-forward

```bash
# MLflow UI
kubectl port-forward -n mlflow svc/mlflow 5000:5000

# Prometheus PushGateway
kubectl port-forward -n monitoring svc/prometheus-pushgateway 9091:9091

# MinIO
kubectl port-forward -n mlflow svc/minio 9000:9000

# PostgreSQL
kubectl port-forward -n mlflow svc/postgres-postgresql 5432:5432
```

#### 3. Запуск експериментів

```bash
# Перейти в директорію експериментів
cd experiments

# Встановити залежності
pip install -r requirements.txt

# Запустити тренування
python train_and_push.py
```

### 🔧 Детальні інструкції

#### Перевірка наявності сервісів у кластері

```bash
# Перевірити всі сервіси
kubectl get svc -A | grep -E "(mlflow|minio|postgres|pushgateway)"

# Перевірити поди
kubectl get pods -A | grep -E "(mlflow|minio|postgres|pushgateway)"

# Перевірити логи
kubectl logs -n mlflow deployment/mlflow
kubectl logs -n monitoring deployment/prometheus-pushgateway
```

#### Доступ до MLflow UI

1. Відкрийте браузер на `http://localhost:5000`
2. Перейдіть до експерименту `iris_classification`
3. Перегляньте метрики, параметри та артефакти

#### Перегляд метрик в Grafana

1. Відкрийте Grafana на `http://localhost:3000`
2. Перейдіть до **Explore**
3. Виберіть Prometheus як джерело даних
4. Виконайте запити:
   ```
   mlflow_accuracy
   mlflow_loss
   ```

#### Налаштування змінних середовища

```bash
# Для локального запуску
export MLFLOW_TRACKING_URI="http://localhost:5000"
export PUSHGATEWAY_URL="http://localhost:9091"

# Для запуску в кластері
export MLFLOW_TRACKING_URI="http://mlflow.mlflow.svc.cluster.local:5000"
export PUSHGATEWAY_URL="http://prometheus-pushgateway.monitoring.svc.cluster.local:9091"
```

### 📊 Моніторинг та метрики

#### MLflow метрики
- **accuracy**: Точність моделі на тестовому наборі
- **loss**: Log loss на тестовому наборі

#### Prometheus метрики
- `mlflow_accuracy{run_id, experiment}`: Точність з мітками
- `mlflow_loss{run_id, experiment}`: Втрати з мітками

#### Grafana дашборди

Створіть дашборд з наступними панелями:

1. **Accuracy over time**:
   ```promql
   mlflow_accuracy
   ```

2. **Loss over time**:
   ```promql
   mlflow_loss
   ```

3. **Best model comparison**:
   ```promql
   topk(5, mlflow_accuracy)
   ```

### 🛠️ Troubleshooting

#### Проблеми з підключенням до MLflow

```bash
# Перевірити доступність сервісу
kubectl get svc -n mlflow mlflow

# Перевірити логи
kubectl logs -n mlflow deployment/mlflow

# Перевірити конфігурацію
kubectl describe deployment -n mlflow mlflow
```

#### Проблеми з PushGateway

```bash
# Перевірити статус
kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus-pushgateway

# Перевірити логи
kubectl logs -n monitoring deployment/prometheus-pushgateway

# Тестувати підключення
curl http://localhost:9091/metrics
```

#### Проблеми з базою даних

```bash
# Перевірити підключення до PostgreSQL
kubectl exec -n mlflow -it deployment/postgres-postgresql -- psql -U postgres -d mlflow

# Перевірити таблиці MLflow
kubectl exec -n mlflow -it deployment/postgres-postgresql -- psql -U postgres -d mlflow -c "\dt"
```

### 📈 Результати експериментів

Після запуску скрипта ви отримаєте:

1. **MLflow UI**: Всі експерименти з метриками та артефактами
2. **Grafana**: Графіки метрик у реальному часі
3. **best_model/**: Найкраща модель збережена локально
4. **Prometheus**: Метрики з мітками для аналізу

### 🔐 Безпека

- Всі паролі та ключі зберігаються в Kubernetes Secrets
- MinIO налаштований з базовою аутентифікацією
- PostgreSQL захищений паролем
- MLflow працює в ізольованому namespace

### 📝 Логи та моніторинг

```bash
# Логи MLflow
kubectl logs -f -n mlflow deployment/mlflow

# Логи PushGateway
kubectl logs -f -n monitoring deployment/prometheus-pushgateway

# Логи PostgreSQL
kubectl logs -f -n mlflow deployment/postgres-postgresql

# Логи MinIO
kubectl logs -f -n mlflow deployment/minio
```

### 📊 Grafana Дашборд

Імпортуйте готовий дашборд для моніторингу експериментів:

1. Відкрийте Grafana
2. Перейдіть до **Import Dashboard**
3. Скопіюйте вміст файлу `grafana-dashboard.json`
4. Налаштуйте Prometheus як джерело даних

Дашборд включає:
- Графіки точності та втрат у часі
- Таблицю найкращих моделей
- Розподіл метрик
- Автоматичне оновлення кожні 5 секунд

### 🎯 Наступні кроки

1. Налаштуйте автоматичне розгортання через CI/CD
2. Додайте алерти в Grafana
3. Інтегруйте з Jupyter Notebooks
4. Додайте A/B тестування моделей
5. Налаштуйте автоматичне перетренування

### 📞 Підтримка

При виникненні проблем перевірте:
1. Статус всіх подів: `kubectl get pods -A`
2. Логи сервісів: `kubectl logs -n <namespace> <deployment>`
3. Конфігурацію ArgoCD: `kubectl get applications -n argocd`
4. Доступність сервісів: `kubectl get svc -A`