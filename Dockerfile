FROM python:3.11-slim

WORKDIR /app

# Cài đặt các gói cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Sao chép requirements files
COPY requirements.txt requirements-dev.txt ./

# Tạo phiên bản requirements_linux.txt không có pywin32 và giải quyết xung đột protobuf
RUN grep -v "pywin32" requirements.txt | grep -v "^protobuf==" > requirements_linux.txt && \
    echo "protobuf>=5.26.1,<6.0dev" >> requirements_linux.txt

# Cài đặt dependencies dựa trên môi trường
ARG ENV=production
RUN if [ "$ENV" = "development" ]; then \
    pip install --no-cache-dir -r requirements_linux.txt -r requirements-dev.txt; \
    else \
    pip install --no-cache-dir -r requirements_linux.txt; \
    fi

# Tạo thư mục logs và static
RUN mkdir -p logs static

# Sao chép toàn bộ code của ứng dụng (ngoại trừ những gì trong .dockerignore)
COPY . .

# Tạo file .env và babycare_connection.json từ biến môi trường nếu chúng không tồn tại
ARG ENV_FILE_CONTENT=""
ARG BABYCARE_CONNECTION_JSON=""

RUN if [ ! -f .env ] && [ ! -z "$ENV_FILE_CONTENT" ]; then \
    echo "$ENV_FILE_CONTENT" > .env; \
    fi

RUN if [ ! -f babycare_connection.json ] && [ ! -z "$BABYCARE_CONNECTION_JSON" ]; then \
    echo "$BABYCARE_CONNECTION_JSON" > babycare_connection.json; \
    fi

# Mở cổng mà ứng dụng sẽ chạy
EXPOSE 8080

# Thêm health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Khởi chạy ứng dụng với Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--ws-ping-interval", "30", "--ws-ping-timeout", "120", "--log-level", "info"] 