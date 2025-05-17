# Hướng dẫn Triển khai CI/CD với Docker và GitHub Actions

## 1. Thiết lập VPS

### 1.1. Kết nối SSH vào VPS
```bash
ssh username@ip_address
```

### 1.2. Cài đặt môi trường
Tải và chạy script thiết lập:
```bash
wget -O setup-vps.sh https://raw.githubusercontent.com/givoxxs/baby_posture_analysis/main/setup-vps.sh
chmod +x setup-vps.sh
./setup-vps.sh
```

### 1.3. Tạo thư mục dự án và thiết lập secrets
```bash
mkdir -p ~/baby_posture_analysis

# Tải và chạy script thiết lập secrets
wget -O setup-secrets.sh https://raw.githubusercontent.com/givoxxs/baby_posture_analysis/main/setup-secrets.sh
chmod +x setup-secrets.sh
./setup-secrets.sh

# Chỉnh sửa các file nhạy cảm với thông tin thực tế
nano ~/baby_posture_analysis/.env
nano ~/baby_posture_analysis/babycare_connection.json
```

## 2. Thiết lập GitHub Actions

### 2.1. Tạo SSH Key trên VPS

```bash
wget -O setup-ssh-key.sh https://raw.githubusercontent.com/givoxxs/baby_posture_analysis/main/setup-ssh-key.sh
chmod +x setup-ssh-key.sh
./setup-ssh-key.sh
```

### 2.2. Thêm GitHub Secrets

Trong GitHub, truy cập vào repository (https://github.com/givoxxs/baby_posture_analysis), vào mục Settings > Secrets and variables > Actions, thêm các secrets sau:

- `SSH_PRIVATE_KEY`: Nội dung của file `~/.ssh/github_actions_key` trên VPS
- `VPS_USERNAME`: Tên người dùng trên VPS
- `VPS_IP`: Địa chỉ IP của VPS

### 2.3. Thêm Secrets cho các file nhạy cảm

Thêm nội dung của các file nhạy cảm vào GitHub Secrets:

- `ENV_FILE_CONTENT`: Toàn bộ nội dung của file `.env`
- `BABYCARE_CONNECTION_JSON`: Toàn bộ nội dung của file `babycare_connection.json`

Để lấy nội dung file `.env`:
```bash
cat ~/baby_posture_analysis/.env
```

Để lấy nội dung file `babycare_connection.json`:
```bash
cat ~/baby_posture_analysis/babycare_connection.json
```

## 3. Cách xử lý các file nhạy cảm

Dự án này sử dụng 3 lớp bảo mật cho các file nhạy cảm:

1. **GitHub Actions**:
   - Các file nhạy cảm được lưu trữ an toàn trong GitHub Secrets
   - Khi triển khai, GitHub Actions tạo tạm thời các file này
   - Các file này được sao chép đến VPS

2. **VPS**:
   - Các file nhạy cảm được giữ lại giữa các lần triển khai
   - Các file mới sẽ không ghi đè lên file cũ nếu chúng đã tồn tại

3. **Docker**:
   - Docker mount các file nhạy cảm từ host vào container
   - Nếu không tìm thấy file, Docker sẽ tạo từ build args (nhưng thường không sử dụng)

Các file nhạy cảm **không được commit** vào repository vì đã được thêm vào `.gitignore`.

## 4. Thư mục và files không cần thiết cho triển khai

Một số thư mục và files không được bao gồm trong quá trình triển khai:

1. **ML_train/**: Thư mục chứa các notebook và mã nguồn dùng để thử nghiệm và huấn luyện mô hình, không cần thiết cho ứng dụng sản xuất.
2. **.git/**: Thư mục Git không cần thiết cho việc chạy ứng dụng.
3. **.github/**: Chứa cấu hình GitHub Actions, không cần thiết trên môi trường sản xuất.
4. Các file cấu hình và tài liệu như README.md, DEPLOY.md, v.v.

Các thư mục và files này được loại trừ thông qua:
- File `.dockerignore` khi build Docker image
- Quy trình deploy trong GitHub Actions workflow

## 5. Cấu hình Uvicorn cho WebSocket

Dự án này sử dụng Uvicorn để chạy ứng dụng FastAPI với hỗ trợ WebSocket. Uvicorn là lựa chọn tốt nhất cho các ứng dụng yêu cầu hỗ trợ WebSocket đầy đủ.

### 5.1. Cấu hình Uvicorn Tối ưu

Uvicorn được cấu hình trong Dockerfile với các tham số tối ưu cho WebSocket:

```
uvicorn app.main:app --host 0.0.0.0 --port 8080 --ws-ping-interval 30 --ws-ping-timeout 120 --log-level info
```

Các tham số chính:
- `--ws-ping-interval`: Khoảng thời gian giữa các ping WebSocket (giây)
- `--ws-ping-timeout`: Thời gian tối đa chờ đợi pong response (giây)
- `--log-level`: Mức độ logging

### 5.2. Biến Môi trường cho Uvicorn

Uvicorn có thể được cấu hình thông qua các biến môi trường trong `docker-compose.yml`:

- `UVICORN_HOST`: Địa chỉ IP để lắng nghe
- `UVICORN_PORT`: Cổng để lắng nghe
- `UVICORN_LOG_LEVEL`: Mức độ logging
- `UVICORN_WS_PING_INTERVAL`: Khoảng thời gian giữa các ping WebSocket
- `UVICORN_WS_PING_TIMEOUT`: Thời gian tối đa chờ đợi pong response

## 6. Triển khai thủ công lần đầu

### 6.1. Sao chép dự án sang VPS
```bash
git clone https://github.com/givoxxs/baby_posture_analysis.git ~/baby_posture_analysis_temp
cd ~/baby_posture_analysis_temp
```

### 6.2. Di chuyển files từ bản tạm sang thư mục chính (giữ lại các file nhạy cảm)
```bash
# Loại bỏ thư mục ML_train nếu tồn tại
rm -rf ~/baby_posture_analysis_temp/ML_train

# Sao chép các file cần thiết
cp -r ~/baby_posture_analysis_temp/* ~/baby_posture_analysis/
cd ~/baby_posture_analysis
rm -rf ~/baby_posture_analysis_temp
```

### 6.3. Khởi chạy ứng dụng
```bash
cd ~/baby_posture_analysis
docker-compose up -d --build
```

## 7. Quy trình CI/CD

1. Push code lên nhánh `main` hoặc `master` của repository https://github.com/givoxxs/baby_posture_analysis
2. GitHub Actions sẽ tự động tạo các file nhạy cảm từ GitHub Secrets
3. GitHub Actions chỉ sao chép các thư mục và files cần thiết, loại bỏ thư mục ML_train
4. GitHub Actions triển khai code lên VPS, giữ lại các file nhạy cảm hiện có
5. Docker sử dụng các file nhạy cảm thông qua volumes
6. Kiểm tra ứng dụng tại http://your-vps-ip:8080

## 8. Kiểm tra logs

```bash
# Xem logs của container
docker logs baby_posture_analysis

# Xem logs ứng dụng
cat ~/baby_posture_analysis/logs/app.log
```

## 9. Quản lý ứng dụng

```bash
# Khởi động ứng dụng
cd ~/baby_posture_analysis
docker-compose up -d

# Dừng ứng dụng
cd ~/baby_posture_analysis
docker-compose down

# Khởi động lại ứng dụng
cd ~/baby_posture_analysis
docker-compose restart
```

## 10. Bảo mật file nhạy cảm

Để đảm bảo an toàn cho các file nhạy cảm:

1. Không bao giờ commit file `.env` và `babycare_connection.json` vào repository
2. Đảm bảo các file này đã được thêm vào `.gitignore`
3. Chỉ những người có quyền truy cập vào GitHub Secrets mới có thể xem/chỉnh sửa thông tin nhạy cảm
4. Định kỳ thay đổi các thông tin nhạy cảm và cập nhật cả trên VPS và GitHub Secrets
5. Sao lưu các file nhạy cảm ở nơi an toàn ngoài VPS

## 11. Tối ưu hóa hiệu suất WebSocket

Để tối ưu hóa hiệu suất WebSocket trong môi trường sản xuất:

1. **Điều chỉnh tham số WebSocket**:
   - Tăng giá trị `--ws-ping-interval` nếu kết nối giữa client và server ổn định
   - Giảm giá trị này nếu mạng không ổn định để phát hiện disconnect sớm hơn
   - Điều chỉnh `--ws-ping-timeout` tùy thuộc vào độ trễ mạng

2. **Giám sát kết nối**:
   - Theo dõi số lượng kết nối WebSocket đồng thời
   - Theo dõi thời gian sống của các kết nối
   - Phát hiện sớm các lỗi kết nối

3. **Khi cần mở rộng quy mô**:
   - Xem xét giải pháp load balancing nếu số lượng kết nối WebSocket tăng cao
   - Sử dụng công cụ như HAProxy hoặc Nginx với module stream để cân bằng tải WebSocket 