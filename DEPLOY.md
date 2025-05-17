# Hướng dẫn triển khai Baby Posture Analysis

Hướng dẫn này giúp bạn thiết lập CI/CD pipline để triển khai ứng dụng Baby Posture Analysis lên VPS sử dụng Docker và GitHub Actions.

## Yêu cầu

1. **VPS** đã cài đặt:
   - Docker
   - Docker Compose
   - Lsof (để kiểm tra cổng)

2. **GitHub repository** cho mã nguồn của bạn.

3. **Docker Hub account** để lưu trữ Docker image.

## Quy trình tổng quan

1. Code được push lên GitHub -> Kích hoạt GitHub Actions
2. GitHub Actions build Docker image và đẩy lên Docker Hub
3. GitHub Actions triển khai lên VPS qua SSH
4. VPS pull image từ Docker Hub và chạy container

## Thiết lập trên VPS

### 1. Cài đặt Docker và Docker Compose

```bash
# Cài đặt Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Cài đặt Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Cài đặt lsof để kiểm tra cổng
sudo apt-get update
sudo apt-get install -y lsof
```

### 2. Tạo thư mục dự án và các file nhạy cảm

```bash
mkdir -p ~/baby_posture_analysis/logs
mkdir -p ~/baby_posture_analysis/static
```

### 3. Thiết lập các file nhạy cảm

Tạo file `.env`:

```bash
cat > ~/baby_posture_analysis/.env << EOF
# Thông tin API
API_HOST=0.0.0.0
API_PORT=8080
API_TITLE=Baby Posture Analysis
API_DESCRIPTION=API for analyzing baby posture from images and videos
API_VERSION=1.0.0

# Thêm các biến môi trường khác nếu cần
# ...
EOF
```

Tạo file `babycare_connection.json` (thay thế bằng thông tin thực tế):

```bash
cat > ~/baby_posture_analysis/babycare_connection.json << EOF
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "your-private-key",
  "client_email": "your-client-email",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "your-cert-url"
}
EOF
```

## Thiết lập GitHub Secrets

Trong repository GitHub của bạn, đi tới Settings > Secrets and variables > Actions và thêm các secret sau:

1. `DOCKER_USERNAME` - Tên người dùng Docker Hub
2. `DOCKER_PASSWORD` - Mật khẩu Docker Hub
3. `VPS_IP` - Địa chỉ IP của VPS
4. `VPS_USERNAME` - Tên người dùng SSH trên VPS
5. `VPS_PASSWORD` - Mật khẩu SSH của VPS
6. `PORT` - Cổng để chạy ứng dụng (mặc định: 8080)
7. `ENV_FILE_CONTENT` - Nội dung của file .env
8. `BABYCARE_CONNECTION_JSON` - Nội dung của file babycare_connection.json

Để lấy nội dung của các file nhạy cảm trên VPS để đưa vào GitHub Secrets:

```bash
# Lấy nội dung file .env
cat ~/baby_posture_analysis/.env

# Lấy nội dung file babycare_connection.json
cat ~/baby_posture_analysis/babycare_connection.json
```

## Cấu trúc dự án

```
baby_posture_analysis/
├── .github/
│   └── workflows/
│       └── deploy.yml      # GitHub Actions workflow
├── app/                    # Mã nguồn ứng dụng
├── .dockerignore           # Loại bỏ file không cần thiết khi build Docker
├── Dockerfile              # Định nghĩa Docker image
├── docker-compose.yml      # Cấu hình Docker Compose
├── requirements.txt        # Dependencies Python
└── setup-secrets.sh        # Script thiết lập các file nhạy cảm
```

## Quy trình CI/CD

### 1. Push code lên GitHub

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

### 2. GitHub Actions tự động:

1. Build Docker image
2. Push image lên Docker Hub
3. Triển khai lên VPS

### 3. Kiểm tra logs trên VPS

```bash
cd ~/baby_posture_analysis
docker-compose logs -f
```

## Khắc phục sự cố

### 1. Kiểm tra trạng thái container

```bash
docker ps -a
```

### 2. Xem logs của container

```bash
docker logs baby_posture_analysis
```

### 3. Khởi động lại dịch vụ

```bash
cd ~/baby_posture_analysis
docker-compose down
docker-compose up -d
```

### 4. Kiểm tra cổng đang sử dụng

```bash
lsof -i :8080
```

## Kiểm tra hoạt động ứng dụng

Truy cập vào địa chỉ: `http://[VPS_IP]:[PORT]`

## Bảo mật

- Các file nhạy cảm được lưu trữ an toàn trong GitHub Secrets
- Sử dụng biến môi trường để cấu hình
- Không đưa các thông tin nhạy cảm vào mã nguồn

## Các cải tiến có thể thực hiện

1. Thiết lập Nginx làm reverse proxy
2. Thêm SSL/TLS với Let's Encrypt
3. Thiết lập monitoring với Prometheus/Grafana
4. Thêm backup tự động cho dữ liệu 