import multiprocessing
import os

# Số lượng worker processes
# Công thức thông dụng là (2 x số core CPU) + 1
workers_per_core = float(os.getenv("WORKERS_PER_CORE", "2"))
cores = multiprocessing.cpu_count()
default_web_concurrency = max(int(workers_per_core * cores), 2)
web_concurrency = int(os.getenv("WEB_CONCURRENCY", default_web_concurrency))

# Host và port
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8080")

# Timeout
timeout = int(os.getenv("TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "120"))
keepalive = int(os.getenv("KEEPALIVE", "5"))

# Logging
accesslog = os.getenv("ACCESS_LOG", "-")
errorlog = os.getenv("ERROR_LOG", "-")
loglevel = os.getenv("LOG_LEVEL", "info")

# Worker options
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = int(os.getenv("MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("MAX_REQUESTS_JITTER", "50"))

# Reload code khi có thay đổi (chỉ nên dùng trong môi trường phát triển)
reload = os.getenv("RELOAD", "False").lower() in ("true", "1", "t")

# Bind cho socket
bind = f"{host}:{port}"

# SSL configuration (nếu cần)
# certfile = os.getenv("CERTFILE")
# keyfile = os.getenv("KEYFILE")
