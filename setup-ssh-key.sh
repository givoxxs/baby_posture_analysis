#!/bin/bash

# Tạo SSH key cho GitHub Actions
ssh-keygen -t ed25519 -f ~/.ssh/github_actions_key -C "github-actions-deploy" -N ""

# Thêm khóa công khai vào authorized_keys
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys

# Hiển thị khóa riêng tư để thêm vào GitHub Secrets
echo "===== SSH_PRIVATE_KEY để thêm vào GitHub Secrets ====="
cat ~/.ssh/github_actions_key

# Hướng dẫn
echo ""
echo "===== HƯỚNG DẪN ====="
echo "1. Sao chép toàn bộ nội dung khóa riêng tư ở trên (bao gồm cả dòng BEGIN và END)"
echo "2. Thêm vào GitHub repository: Settings > Secrets and variables > Actions > New repository secret"
echo "3. Đặt tên là SSH_PRIVATE_KEY"
echo "4. Thêm hai secrets khác:"
echo "   - VPS_USERNAME: $(whoami)"
echo "   - VPS_IP: $(curl -s ifconfig.me)"
echo ""
echo "===== THÔNG TIN CHO GITHUB SECRETS ====="
echo "VPS_USERNAME: $(whoami)"
echo "VPS_IP: $(curl -s ifconfig.me)" 