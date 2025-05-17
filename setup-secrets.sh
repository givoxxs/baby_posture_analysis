#!/bin/bash

# Thiết lập các file nhạy cảm
mkdir -p ~/baby_posture_analysis

# Tạo file .env
echo "Thiết lập file .env"
cat > ~/baby_posture_analysis/.env << EOF
# Thông tin API
API_HOST=0.0.0.0
API_PORT=8080
API_TITLE=Baby Posture Analysis
API_DESCRIPTION=API for analyzing baby posture from images and videos
API_VERSION=1.0.0

# Thêm các thông tin nhạy cảm khác ở đây
# ...
EOF

# Tạo file babycare_connection.json
echo "Thiết lập file babycare_connection.json"
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

# Thông báo hướng dẫn
echo ""
echo "===== HƯỚNG DẪN ====="
echo "1. Vui lòng điều chỉnh các file nhạy cảm vừa được tạo với thông tin thực tế:"
echo "   - ~/baby_posture_analysis/.env"
echo "   - ~/baby_posture_analysis/babycare_connection.json"
echo ""
echo "2. Sau đó, lấy nội dung của chúng để thêm vào GitHub Secrets:"
echo "   - ENV_FILE_CONTENT: cat ~/baby_posture_analysis/.env"
echo "   - BABYCARE_CONNECTION_JSON: cat ~/baby_posture_analysis/babycare_connection.json"
echo ""
echo "3. Thêm các secrets này vào GitHub repository: https://github.com/givoxxs/baby_posture_analysis > Settings > Secrets and variables > Actions" 