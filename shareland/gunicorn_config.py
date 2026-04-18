import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000

# Timeout settings - increased to handle longer requests
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))  # 120 seconds default
keepalive = 5

# Worker lifecycle
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Logging
accesslog = "-"  # Log to stdout for Docker
errorlog = "-"   # Log to stderr for Docker
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Process naming
proc_name = "shareland"

# Graceful timeout for worker shutdown
graceful_timeout = 30






