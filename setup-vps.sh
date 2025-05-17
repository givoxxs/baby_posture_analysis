#!/bin/bash

# Cập nhật hệ thống
sudo apt-get update
sudo apt-get upgrade -y

# Cài đặt Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Cài đặt Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose 2>/dev/null || true

# Cài đặt lsof để kiểm tra cổng
sudo apt-get install -y lsof

# Thêm người dùng hiện tại vào nhóm docker
sudo usermod -aG docker $USER

# Tạo thư mục dự án
mkdir -p ~/baby_posture_analysis/logs
mkdir -p ~/baby_posture_analysis/static

# Tạo file .env và docker-compose.env
cat > ~/baby_posture_analysis/.env.docker-compose << EOF
DOCKER_USERNAME=givoxxs
PORT=8080
EOF

# Thông báo
echo "================================"
echo "Cài đặt hoàn tất. Vui lòng đăng xuất và đăng nhập lại để áp dụng thay đổi nhóm docker."
echo ""
echo "Sau khi đăng nhập lại, chạy script setup-secrets.sh để thiết lập các file nhạy cảm."
echo ""
echo "Sau đó, thiết lập các GitHub Secrets cần thiết theo hướng dẫn trong DEPLOY.md"
echo "================================" 