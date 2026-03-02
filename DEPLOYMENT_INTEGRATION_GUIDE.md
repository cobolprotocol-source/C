# COBOL Protocol v1.5.3 - DEPLOYMENT & INTEGRATION GUIDE

**Date**: March 2, 2026  
**Status**: ✅ Production Ready  
**Audience**: DevOps, Integration Engineers, System Administrators

---

## Quick Start: 5 Minutes to Production

### Step 1: Prerequisites Check (1 min)

```bash
# Verify Python 3.9+
python3 --version

# Verify pip
pip --version

# Verify git (for clone)
git --version
```

### Step 2: Installation (2 min)

```bash
# Clone repository
git clone https://github.com/ecobolprotocol/dev.c.git
cd dev.c

# Create virtual environment
python3 -m venv cobol_env
source cobol_env/bin/activate  # On Windows: cobol_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# Or minimal install:
# pip install cryptography numpy
```

### Step 3: Verification (1 min)

```bash
# Run verification script
python3 -m pytest conftest.py -v

# Or quick manual check
python3 << 'EOF'
from infrastructure_architecture import *
registry = create_performance_model_registry()
print(f"✅ Ready! {len(registry.models)} models available")
EOF
```

### Step 4: First Compression (1 min)

```python
# test_first_compression.py
from dag_compression_pipeline import CompressionDAG, DAGExecutionEngine

dag = CompressionDAG()
engine = DAGExecutionEngine(dag)

test_data = b"Hello, COBOL v1.5.3 Compression!"
context = engine.create_execution_context(test_data)
context = engine.execute_default_path(context)

print(f"Input:  {len(test_data)} bytes")
print(f"Output: {len(context.data)} bytes")
print(f"✅ Compression test successful!")
```

```bash
python3 test_first_compression.py
```

---

## Production Deployment

### Architecture Decision: Standalone vs. Integrated

```
Choose Based On...

├─ Standalone COBOL Service
│  └─ New compression-only microservice
│     • Dedicated compression cluster
│     • REST/gRPC API
│     • Load balancer
│     → Use if: NEW compression pipeline needed
│
└─ Integrated into Existing System
   ├─ Python application import
   ├─ REST API wrapper
   └─ Database plugin
   → Use if: EXISTING system needs compression
```

### Option 1: Standalone Microservice (Recommended for Scale)

#### Architecture

```
┌──────────────────────────────────────────┐
│   Load Balancer (nginx)                  │
│   Rate limiting, SSL termination         │
└──────────────────────────────────────────┘
              ↓↓↓
    ┌─────────────────────┐
    │ Compression Cluster │
    ├─────────────────────┤
    │ Pod 1: App + COBOL  │
    │ Pod 2: App + COBOL  │
    │ Pod 3: App + COBOL  │
    └─────────────────────┘
              ↓
    ┌──────────────────────┐
    │ Shared Cache Layer   │
    │ (Redis)              │
    │ • Model registry     │
    │ • Dictionary cache   │
    └──────────────────────┘
              ↓
    ┌──────────────────────┐
    │ Persistent Storage   │
    │ • Results            │
    │ • Audit logs         │
    │ • Metrics            │
    └──────────────────────┘
```

#### Deployment Steps

```bash
# 1. Create application wrapper
cat > cobol_api_server.py << 'EOF'
from flask import Flask, request, jsonify
from dag_compression_pipeline import CompressionDAG, DAGExecutionEngine
import base64

app = Flask(__name__)
dag = CompressionDAG()
engine = DAGExecutionEngine(dag)

@app.route('/compress', methods=['POST'])
def compress():
    try:
        data = base64.b64decode(request.json['data'])
        context = engine.create_execution_context(data)
        context = engine.execute_default_path(context)
        return jsonify({
            'status': 'success',
            'compressed': base64.b64encode(context.data).decode(),
            'ratio': len(data) / len(context.data)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'version': '1.5.3'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, workers=4)
EOF

# 2. Create requirements.txt
cat > requirements.txt << 'EOF'
Flask==2.3.0
cryptography==41.0.0
numpy==1.24.0
psutil==5.9.0
prometheus-client==0.17.0
EOF

# 3. Create Docker file (optional but recommended)
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY *.py .
ENV FLASK_APP=cobol_api_server.py
EXPOSE 5000
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:5000", "cobol_api_server:app"]
EOF

# 4. Deploy to Kubernetes (example)
cat > k8s-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cobol-compression
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cobol-compression
  template:
    metadata:
      labels:
        app: cobol-compression
    spec:
      containers:
      - name: cobol-app
        image: cobol-compression:1.5.3
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "512Mi"
            cpu: "1"
          limits:
            memory: "2Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: cobol-compression-service
spec:
  selector:
    app: cobol-compression
  ports:
  - protocol: TCP
    port: 5000
    targetPort: 5000
  type: LoadBalancer
EOF
```

### Option 2: Direct Integration into Python Application

#### Method A: Direct Import

```python
# In your existing Python application
from dag_compression_pipeline import CompressionDAG, DAGExecutionEngine
from infrastructure_architecture import create_performance_model_registry

class DataCompressionService:
    def __init__(self):
        self.dag = CompressionDAG()
        self.engine = DAGExecutionEngine(self.dag)
        self.models = create_performance_model_registry()
    
    def compress(self, data: bytes, model_name: str = "DATACENTER_GENERAL") -> bytes:
        model = self.models.get_model(model_name)
        context = self.engine.create_execution_context(data)
        context = self.engine.execute_default_path(context)
        return context.data
    
    def compress_with_encryption(self, data: bytes, key: bytes, 
                                nonce: bytes) -> bytes:
        from security_trust_layer import AES256GCMEncryptor
        
        # Compress first
        compressed = self.compress(data)
        
        # Then encrypt
        encryptor = AES256GCMEncryptor()
        encrypted = encryptor.encrypt(compressed, key, nonce)
        
        return encrypted
```

#### Method B: REST API Adapter

```python
# In your Flask/FastAPI application
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64

app = FastAPI()

class CompressionRequest(BaseModel):
    data: str  # base64-encoded
    model: str = "DATACENTER_GENERAL"
    encrypt: bool = False
    key: str = None  # For encryption, base64-encoded

service = DataCompressionService()

@app.post("/api/v1/compress")
async def compress_endpoint(request: CompressionRequest):
    try:
        data = base64.b64decode(request.data)
        
        if request.encrypt and request.key:
            key = base64.b64decode(request.key)
            nonce = b'\x00' * 12
            result = service.compress_with_encryption(data, key, nonce)
        else:
            result = service.compress(data, request.model)
        
        return {
            "status": "success",
            "compressed": base64.b64encode(result).decode(),
            "ratio": len(data) / len(result),
            "original_size": len(data),
            "compressed_size": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### Method C: Database Plugin (PostgreSQL)

```python
# PostgreSQL extension loader
import psycopg2
from psycopg2.extensions import register_adapter

class CompressionAdapter:
    def __init__(self, data: bytes):
        self.data = data
        self.service = DataCompressionService()
    
    def get_json_data(self, none):
        compressed = self.service.compress(self.data)
        return f"COMPRESSED({len(compressed)} bytes)"

# Usage in queries
def setup_postgres_extension(conn):
    cursor = conn.cursor()
    
    # Create function wrapper
    cursor.execute("""
        CREATE OR REPLACE FUNCTION cobol_compress(bytea) 
        RETURNS bytea AS $$
            import sys
            from dag_compression_pipeline import CompressionDAG, DAGExecutionEngine
            
            dag = CompressionDAG()
            engine = DAGExecutionEngine(dag)
            
            context = engine.create_execution_context($1)
            context = engine.execute_default_path(context)
            return context.data
        $$ LANGUAGE plpython3u IMMUTABLE;
    """)
    
    conn.commit()

# Usage in SQL
# SELECT cobol_compress(large_data_column) AS compressed 
# FROM archive_table
```

---

## Configuration Management

### Environment-Based Configuration

```bash
# .env file for development
COBOL_MODEL=DATACENTER_GENERAL
COBOL_ENERGY_BUDGET=100
COBOL_ENABLE_ENCRYPTION=false
COBOL_ENABLE_DP=false
COBOL_LOG_LEVEL=INFO
COBOL_CACHE_SIZE_MB=512

# .env.production
COBOL_MODEL=DATACENTER_GENERAL
COBOL_ENERGY_BUDGET=100
COBOL_ENABLE_ENCRYPTION=true
COBOL_ENABLE_DP=true
COBOL_LOG_LEVEL=WARN
COBOL_CACHE_SIZE_MB=2048
```

### Configuration Loader

```python
import os
from dataclasses import dataclass

@dataclass
class CobolConfig:
    model: str = os.getenv("COBOL_MODEL", "DATACENTER_GENERAL")
    energy_budget: float = float(os.getenv("COBOL_ENERGY_BUDGET", "100"))
    enable_encryption: bool = os.getenv("COBOL_ENABLE_ENCRYPTION", "false").lower() == "true"
    enable_dp: bool = os.getenv("COBOL_ENABLE_DP", "false").lower() == "true"
    log_level: str = os.getenv("COBOL_LOG_LEVEL", "INFO")
    cache_size_mb: int = int(os.getenv("COBOL_CACHE_SIZE_MB", "512"))
    
    def get_energy_profile(self):
        from energy_aware_execution import EnergyProfile
        return EnergyProfile.default_datacenter()

config = CobolConfig()
```

---

## Monitoring & Observability

### Metrics to Track

```python
# Key metrics for production monitoring
from prometheus_client import Counter, Histogram, Gauge
import time

class CobolMetrics:
    compression_requests = Counter(
        'cobol_compression_requests_total',
        'Total compression requests',
        ['model', 'status']
    )
    
    compression_duration = Histogram(
        'cobol_compression_duration_seconds',
        'Compression duration',
        ['model']
    )
    
    compression_ratio = Gauge(
        'cobol_compression_ratio',
        'Compression ratio (output/input)',
        ['model']
    )
    
    energy_used = Histogram(
        'cobol_energy_used_mj',
        'Energy used per request',
        ['model']
    )
    
    @staticmethod
    def track_compression(model_name: str, start_time: float, 
                         input_size: int, output_size: int, 
                         energy_used: float):
        duration = time.time() - start_time
        CobolMetrics.compression_requests.labels(
            model=model_name, status='success'
        ).inc()
        CobolMetrics.compression_duration.labels(model=model_name).observe(duration)
        CobolMetrics.compression_ratio.labels(model=model_name).set(
            output_size / input_size
        )
        CobolMetrics.energy_used.labels(model=model_name).observe(energy_used)
```

### Logging Strategy

```python
import logging

# Configure structured logging
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/cobol/compression.log',
            'formatter': 'json'
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO'
    }
})

logger = logging.getLogger(__name__)

# Usage
logger.info("compression_started", extra={
    'input_size': len(data),
    'model': model_name,
    'session_id': session_id
})
```

### Health Checks

```bash
# Kubernetes/Docker health check endpoint
curl http://localhost:5000/health
# Response: {"status": "healthy", "version": "1.5.3"}

# Detailed health check
curl http://localhost:5000/health/detailed
# Response includes:
# {
#   "status": "healthy",
#   "version": "1.5.3",
#   "models_loaded": 5,
#   "cache_hit_rate": 0.87,
#   "uptime_seconds": 3600,
#   "requests_handled": 15000,
#   "avg_compression_time_ms": 245
# }
```

---

## Security Hardening

### 1. Network Security

```yaml
# Network policies (Kubernetes)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cobol-network-policy
spec:
  podSelector:
    matchLabels:
      app: cobol-compression
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: application
    ports:
    - protocol: TCP
      port: 5000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: storage
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL for audit logs
```

### 2. Encryption Keys Management

```python
# Using AWS Secrets Manager (recommended for production)
import boto3

class KeyManager:
    def __init__(self):
        self.client = boto3.client('secretsmanager')
    
    def get_encryption_key(self, key_id: str) -> bytes:
        response = self.client.get_secret_value(SecretId=key_id)
        return base64.b64decode(response['SecretString'])
    
    def rotate_key(self, key_id: str):
        """Rotate encryption key every 90 days"""
        self.client.rotate_secret(
            SecretId=key_id,
            RotationLambdaARN='arn:aws:lambda:...',
            RotationRules={'AutomaticallyAfterDays': 90}
        )

# Or using HashiCorp Vault
import hvac

class VaultKeyManager:
    def __init__(self):
        self.client = hvac.Client(url='https://vault.example.com:8200')
    
    def get_encryption_key(self) -> bytes:
        secret = self.client.secrets.kv.read_secret_version(
            path='cobol/keys/encryption'
        )
        return base64.b64decode(secret['data']['data']['key'])
```

### 3. Access Control

```python
# Role-Based Access Control (RBAC)
from functools import wraps
from flask import request

def require_role(required_role: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get role from JWT token
            token = request.headers.get('Authorization')
            role = extract_role_from_token(token)
            
            if role not in required_role.split(','):
                return {'error': 'Insufficient permissions'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.post("/api/v1/compress")
@require_role("compress_user,compress_admin")
def compress_endpoint(request: CompressionRequest):
    # compression logic
    pass
```

### 4. Audit Logging (Non-Repudiation)

```python
from security_trust_layer import SecurityAuditLog

def log_compression_with_audit(data: bytes, model: str, 
                               user_id: str, session_id: str):
    # Create audit log
    audit = SecurityAuditLog(log_id=session_id)
    
    # Log user action
    audit.add_entry('COMPRESSION_INITIATED', {
        'user_id': user_id,
        'model': model,
        'input_size': len(data),
        'timestamp': datetime.now().isoformat()
    })
    
    # Perform compression
    compressed = compress(data, model)
    
    # Log completion
    audit.add_entry('COMPRESSION_COMPLETED', {
        'output_size': len(compressed),
        'ratio': len(data) / len(compressed),
        'timestamp': datetime.now().isoformat()
    })
    
    # Store audit log (immutable)
    store_audit_log(audit)
    
    # Verify integrity
    if not audit.verify_integrity():
        raise SecurityError("Audit log tampering detected!")
    
    return compressed
```

---

## Performance Tuning

### Memory Optimization

```python
# For large data compression, use streaming
def stream_compress_large_file(filepath: str, chunk_size: int = 10 * 1024 * 1024):
    """Compress large file in chunks to save memory"""
    
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            # Compress chunk
            context = engine.create_execution_context(chunk)
            context = engine.execute_default_path(context)
            
            # Yield compressed chunk
            yield context.data
```

### CPU Optimization

```python
# Use threading for parallel requests
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

def compress_async(data: bytes, model: str):
    """Asynchronous compression using thread pool"""
    future = executor.submit(
        compress_service.compress, 
        data, 
        model
    )
    return future

# Usage
future = compress_async(data, "DATACENTER_GENERAL")
result = future.result()  # Wait for result
```

### I/O Optimization

```python
# Use async I/O for storage operations
import aiofiles
import asyncio

async def compress_and_store(data: bytes, output_path: str):
    """Compress and store asynchronously"""
    # Compress
    compressed = compress_service.compress(data)
    
    # Write to file asynchronously
    async with aiofiles.open(output_path, 'wb') as f:
        await f.write(compressed)
```

---

## Backup & Disaster Recovery

### Backup Strategy

```bash
# Daily backup of models and configurations
0 2 * * * python3 /opt/cobol/backup_models.py

# Backup script
#!/usr/bin/env python3
import tarfile
import datetime
import shutil
import os

def backup_models():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"cobol_backup_{timestamp}.tar.gz"
    
    # Include critical files
    files_to_backup = [
        "infrastructure_architecture.py",
        "super_dictionary_system.py",
        "security_trust_layer.py"
    ]
    
    with tarfile.open(backup_name, "w:gz") as tar:
        for file in files_to_backup:
            tar.add(file)
    
    # Upload to S3/GCS
    upload_to_remote_storage(backup_name)
    
    # Keep last 30 days locally
    os.rename(backup_name, f"/backup/{backup_name}")

if __name__ == '__main__':
    backup_models()
```

### Disaster Recovery Plan

```
Event                        Recovery Time  Recovery Point
────────────────────────────────────────────────────────
Single Pod Failure           < 5 seconds     Last request
Multiple Pod Failure         < 30 seconds    Last backup
Data Corruption              < 1 hour        Last daily backup
Model Registry Corruption    < 5 minutes     Immutable copy
Audit Log Corruption         < 1 hour        Blockchain verification
```

---

## Scaling Considerations

### Horizontal Scaling

```yaml
# Kubernetes HPA for auto-scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cobol-compression-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cobol-compression
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 15
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### Vertical Scaling

```bash
# Monitor resource usage
kubectl top nodes
kubectl top pods -n cobol-compression

# Adjust resource requests/limits
kubectl set resources deployment cobol-compression \
  --requests=cpu=2,memory=1Gi \
  --limits=cpu=4,memory=2Gi
```

### Caching Strategy

```python
# Redis cache for frequently compressed patterns
import redis

cache = redis.Redis(host='redis.example.com', port=6379, db=0)

def compress_with_cache(data: bytes, model: str) -> bytes:
    # Create cache key (hash of input + model)
    cache_key = f"cobol:{model}:{hashlib.sha256(data).hexdigest()}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Compress if not in cache
    compressed = compress_service.compress(data, model)
    
    # Store in cache (24-hour TTL)
    cache.setex(cache_key, 86400, compressed)
    
    return compressed
```

---

## Troubleshooting

### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Out of Memory | Process killed, OOM errors | Use streaming compression, increase pod memory |
| Slow Compression | High latency, timeouts | Switch to FAST_PATH, enable caching |
| High CPU | CPU throttling | Add more replicas, enable CPU limits |
| Failed Audit | Integrity check fails | Restore from backup, verify audit chain |
| Encryption Errors | Key format errors | Verify 256-bit (32 bytes) key format |
| Model Not Found | 404 on model lookup | Verify 5 available models listed |

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose compression output
from dag_compression_pipeline import CompressionDAG, DAGExecutionEngine

dag = CompressionDAG()
engine = DAGExecutionEngine(dag)

# Detailed execution trace
context = engine.create_execution_context(data)
context = engine.execute_default_path(context, verbose=True)

# Output: Layer-by-layer compression details
```

---

## Testing Before Production

### Integration Test Checklist

- [ ] Compression correctness (output format valid)
- [ ] Decompression works (round-trip test)  
- [ ] All 5 models accessible
- [ ] Encryption/decryption works
- [ ] Audit logging functional
- [ ] Energy tracking accurate
- [ ] Performance meets SLAs
- [ ] Security audit complete
- [ ] Backup/restore working
- [ ] Monitoring alerts configured

### Load Testing

```python
# Simple load test
import concurrent.futures
import time

def load_test(num_requests: int = 1000, num_workers: int = 10):
    start = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_requests):
            data = b"Test data " * 1000
            future = executor.submit(compress_service.compress, data)
            futures.append(future)
        
        # Wait for all
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    duration = time.time() - start
    throughput = num_requests / duration
    
    print(f"Requests: {num_requests}")
    print(f"Duration: {duration:.2f}s")
    print(f"Throughput: {throughput:.0f} req/s")
    print(f"Avg time per request: {(duration/num_requests)*1000:.2f}ms")
```

---

## Post-Deployment Checklist

- [ ] System up and healthy (`/health` returns 200)
- [ ] Metrics being collected (check Prometheus)
- [ ] Logs flowing to central logging
- [ ] Audit logs stored and verified
- [ ] Backup jobs running successfully
- [ ] Disaster recovery plan tested
- [ ] Team trained on operations
- [ ] Runbooks created for common issues
- [ ] Monitoring alerts tuned (not too noisy)
- [ ] Documentation updated with local specifics

---

**Last Updated**: March 2, 2026  
**Status**: ✅ Production Ready  
**Review**: Every quarter for capacity planning
