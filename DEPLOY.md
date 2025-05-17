# Hướng dẫn Triển khai CI/CD với Docker và GitHub Actions

## 1. Thiết lập VPS

### 1.1. Kết nối SSH vào VPS
```bash
ssh username@ip_address
```

### 1.2. Cài đặt môi trường
Tải và chạy script thiết lập:
```bash
wget -O setup-vps.sh https://raw.githubusercontent.com/your-username/baby_posture_analysis/main/setup-vps.sh
chmod +x setup-vps.sh
./setup-vps.sh
```

### 1.3. Tạo thư mục dự án và thiết lập secrets
```bash
mkdir -p ~/baby_posture_analysis

# Tải và chạy script thiết lập secrets
wget -O setup-secrets.sh https://raw.githubusercontent.com/your-username/baby_posture_analysis/main/setup-secrets.sh
chmod +x setup-secrets.sh
./setup-secrets.sh

# Chỉnh sửa các file nhạy cảm với thông tin thực tế
nano ~/baby_posture_analysis/.env
nano ~/baby_posture_analysis/babycare_connection.json
```

## 2. Thiết lập GitHub Actions

### 2.1. Tạo SSH Key trên VPS

```bash
wget -O setup-ssh-key.sh https://raw.githubusercontent.com/your-username/baby_posture_analysis/main/setup-ssh-key.sh
chmod +x setup-ssh-key.sh
./setup-ssh-key.sh
```

### 2.2. Thêm GitHub Secrets

Trong GitHub, truy cập vào repository, vào mục Settings > Secrets and variables > Actions, thêm các secrets sau:

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

## 4. Sử dụng Gunicorn cho môi trường sản xuất

Dự án này sử dụng Gunicorn với Uvicorn worker trong môi trường sản xuất, mang lại nhiều lợi ích:

1. **Hiệu suất cao hơn**: Gunicorn quản lý nhiều worker processes, tận dụng tối đa tài nguyên CPU.
2. **Độ tin cậy**: Tự động khởi động lại các worker processes khi chúng gặp sự cố.
3. **Khả năng mở rộng**: Dễ dàng điều chỉnh số lượng worker processes thông qua biến môi trường.
4. **Bảo mật tốt hơn**: Gunicorn được thiết kế để xử lý các vấn đề bảo mật trong môi trường sản xuất.

### 4.1. Cấu hình Gunicorn

Cấu hình Gunicorn được định nghĩa trong file `gunicorn_conf.py` và có thể được tùy chỉnh thông qua các biến môi trường trong `docker-compose.yml`:

- `WORKERS_PER_CORE`: Số lượng worker processes trên mỗi CPU core (mặc định: 2)
- `WEB_CONCURRENCY`: Tổng số worker processes (ghi đè công thức mặc định)
- `TIMEOUT`: Thời gian tối đa cho một worker để xử lý một request (giây)
- `MAX_REQUESTS`: Số lượng requests tối đa mà một worker sẽ xử lý trước khi khởi động lại

Để tối ưu hóa cấu hình Gunicorn cho máy chủ của bạn, hãy điều chỉnh các biến môi trường trong `docker-compose.yml`.

## 5. Triển khai thủ công lần đầu

### 5.1. Sao chép dự án sang VPS
```bash
git clone https://github.com/your-username/baby_posture_analysis.git ~/baby_posture_analysis_temp
cd ~/baby_posture_analysis_temp
```

### 5.2. Di chuyển files từ bản tạm sang thư mục chính (giữ lại các file nhạy cảm)
```bash
cp -r * ~/baby_posture_analysis/
cd ~/baby_posture_analysis
rm -rf ~/baby_posture_analysis_temp
```

### 5.3. Khởi chạy ứng dụng
```bash
cd ~/baby_posture_analysis
docker-compose up -d --build
```

## 6. Quy trình CI/CD

1. Push code lên nhánh `main` hoặc `master`
2. GitHub Actions sẽ tự động tạo các file nhạy cảm từ GitHub Secrets
3. GitHub Actions triển khai code lên VPS, giữ lại các file nhạy cảm hiện có
4. Docker sử dụng các file nhạy cảm thông qua volumes
5. Kiểm tra ứng dụng tại http://your-vps-ip:8080

## 7. Kiểm tra logs

```bash
# Xem logs của container
docker logs baby_posture_analysis

# Xem logs ứng dụng
cat ~/baby_posture_analysis/logs/app.log
```

## 8. Quản lý ứng dụng

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

## 9. Bảo mật file nhạy cảm

Để đảm bảo an toàn cho các file nhạy cảm:

1. Không bao giờ commit file `.env` và `babycare_connection.json` vào repository
2. Đảm bảo các file này đã được thêm vào `.gitignore`
3. Chỉ những người có quyền truy cập vào GitHub Secrets mới có thể xem/chỉnh sửa thông tin nhạy cảm
4. Định kỳ thay đổi các thông tin nhạy cảm và cập nhật cả trên VPS và GitHub Secrets
5. Sao lưu các file nhạy cảm ở nơi an toàn ngoài VPS

## 10. Tối ưu hóa hiệu suất

Để tối ưu hóa hiệu suất của ứng dụng trong môi trường sản xuất:

1. Điều chỉnh số lượng worker processes trong docker-compose.yml phù hợp với tài nguyên máy chủ
2. Sử dụng reverse proxy như Nginx để phục vụ các tệp tĩnh và cân bằng tải
3. Theo dõi sử dụng bộ nhớ và CPU để đảm bảo hiệu suất tối ưu 