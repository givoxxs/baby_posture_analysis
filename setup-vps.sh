#!/bin/bash

# Cập nhật hệ thống
sudo apt-get update
sudo apt-get upgrade -y

# Cài đặt Docker
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce

# Cài đặt Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Thêm người dùng hiện tại vào nhóm docker
sudo usermod -aG docker $USER

# Tạo thư mục dự án
mkdir -p ~/baby_posture_analysis/logs
mkdir -p ~/baby_posture_analysis/static

# Thông báo
echo "Cài đặt hoàn tất. Vui lòng đăng xuất và đăng nhập lại để áp dụng thay đổi nhóm docker."
echo ""
echo "Sau khi đăng nhập lại, bạn có thể tải dự án từ GitHub:"
echo "git clone https://github.com/givoxxs/baby_posture_analysis.git" 