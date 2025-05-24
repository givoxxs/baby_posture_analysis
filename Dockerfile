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
COPY requirements_linux.txt .

# Cài đặt dependencies
RUN pip install --no-cache-dir -r requirements_linux.txt

# Tạo thư mục logs và static
RUN mkdir -p logs static

# Sao chép toàn bộ code của ứng dụng
COPY . .

# Tạo file .env từ biến môi trường nếu chúng không tồn tại
ARG ENV_FILE_CONTENT=""

RUN if [ ! -f .env ] && [ ! -z "$ENV_FILE_CONTENT" ]; then \
    echo "$ENV_FILE_CONTENT" > .env; \
    fi

# Mở cổng mà ứng dụng sẽ chạy
EXPOSE 8080

# Thêm health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Khởi chạy ứng dụng với Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--ws-ping-interval", "30", "--ws-ping-timeout", "120", "--log-level", "info"] 