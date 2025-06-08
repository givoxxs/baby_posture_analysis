# Baby Posture Analysis

<div align="center">

![Baby Posture Analysis](https://img.shields.io/badge/Project-Baby_Posture_Analysis-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-blue)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-orange)
![OpenCV](https://img.shields.io/badge/OpenCV-Latest-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

</div>

## 📋 Overview

A sophisticated system for analyzing baby posture in images to detect potential safety risks during sleep. This project uses computer vision and machine learning to identify potentially dangerous sleeping positions and provide recommendations for safer baby sleep practices.

## ✨ Features

- **Advanced Image Analysis**: Process and enhance images for optimal pose detection
- **MediaPipe Integration**: Skeletal keypoint detection with 3D coordinates
- **ML-Powered Risk Assessment**: Evaluate baby sleeping positions for safety concerns
- **Detailed Analysis Reports**: Get comprehensive insights on posture risks
- **API-First Design**: RESTful endpoints for easy integration with other systems
- **Interactive Web Interface**: Simple visual testing of the analysis system
- **🔥 Firebase Real-time Threshold Listener**: Tự động cập nhật threshold từ Firebase mà không cần đọc liên tục

## 🏗️ Architecture

The system follows a modular pipeline architecture:

### 1. Image Preprocessing Module

- Image normalization and enhancement
- Noise reduction and filtering
- Dimension standardization
- Quality optimization for pose detection

### 2. Keypoint Extraction Module

- MediaPipe Pose for skeletal keypoint detection
- 33 standard body keypoints with 3D coordinates (x, y, z)
- Confidence scores for reliable pose estimation
- Visibility metrics for each detected keypoint

### 3. Posture Feature Construction Module

- Head-torso angle detection for sleeping position
- Limb angle calculations for unnatural positions
- Blanket coverage detection
- Face-down position detection (higher risk factor)

### 4. Risk Analysis Module

- Comprehensive assessment of sleeping position safety
- Risk scoring system (1-10 scale)
- Detailed reasoning for risk assessment
- Specific recommendations based on identified risks

## 🛠️ Technologies

- **Python 3.8+**: Core programming language
- **FastAPI**: High-performance web framework
- **MediaPipe**: Google's ML solution for pose estimation
- **OpenCV**: Computer vision for image processing
- **NumPy/Pandas**: Data manipulation and analysis
- **Scikit-learn**: Machine learning models
- **PIL/Pillow**: Image handling and processing

## 🚀 Setup & Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/givoxxs/baby_posture_analysis.git
   cd baby_posture_analysis
   ```

2. **Set up a virtual environment (recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**:
   Copy the `.env.example` file to create your own `.env` file:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file to configure your settings:
   ```
   # Firebase Storage
   CLOUDINARY_CLOUD_NAME=your_cloud_name   
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret

   # Ngrok Configuration (optional, for public URL access)
   NGROK_AUTHTOKEN=your_ngrok_authtoken

   # FastAPI Settings
   API_HOST=0.0.0.0
   API_PORT=8080
   # Other settings...
   ```

## 🖥️ Usage

### Starting the Server

You can start the server using one of the following methods:

1. **Using the Python module directly**:
   ```bash
   python -m app.main
   ```

2. **Using Uvicorn with options from your `.env` file**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

3. **Or simply with default configuration**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the API documentation**:
   Open your web browser and navigate to:
   ```
   http://localhost:8080/docs
   ```
   This provides interactive Swagger UI documentation for testing all API endpoints.

3. **Test with the web interface**:
   Open your browser and go to:
   ```
   http://localhost:8080
   ```
   The simple web interface allows you to upload images and visualize the analysis results.

## 📡 API Endpoints

### Image Processing

- **POST** `/api/images/process`
  - Process an image with quality enhancements
  - **Parameters**: 
    - `file`: Image file upload (required)
    - `high_resolution`: Boolean to maintain higher resolution (optional)
    - `apply_filter`: Boolean to apply image enhancement filters (optional)
  - **Returns**: Processed image with quality improvements

### Pose Detection

- **POST** `/api/pose/detect`
  - Detect pose keypoints from an image
  - **Parameters**:
    - `file`: Image file upload (required)
    - `high_resolution`: Boolean to maintain higher resolution (optional)
    - `include_annotated_image`: Boolean to include visualized keypoints (optional)
    - `include_analysis`: Boolean to include basic analysis (optional)
  - **Returns**: Detected keypoints and optional analysis

### Posture Analysis

- **POST** `/api/pose/analyze`
  - Analyze baby posture and risk level
  - **Parameters**:
    - `file`: Image file upload (required)
    - `high_resolution`: Boolean to maintain higher resolution (optional)
  - **Returns**: Comprehensive posture analysis and risk assessment

### Complete Pipeline

- **POST** `/api/pipeline/analyze`
  - Process image, detect pose, and analyze risk in one request
  - **Parameters**:
    - `file`: Image file upload (required)
    - `high_resolution`: Boolean to maintain higher resolution (optional)
  - **Returns**: Complete analysis with:
    - Position detection
    - Face-down detection
    - Coverage assessment
    - Risk level and score
    - Confidence rating
    - Analysis reasoning
    - Safety recommendations
    - Annotated image

### Video Analysis

- **POST** `/api/video/analyze`
  - Analyze baby posture from video footage
  - **Parameters**:
    - `file`: Video file upload (required)
    - `sample_rate`: Frames per second to analyze (optional)
  - **Returns**: Time-series analysis of posture throughout the video

## 🔬 Machine Learning Models

This system uses trained machine learning models to analyze posture features:

- **Random Forest Classification**: Used for posture classification
- **Feature Scaling**: Input normalization for consistent analysis
- **Pre-trained Models**: Located in the `app/models` directory
- **Model Training**: Notebooks for model training in `ML_train` directory

## 🧪 Testing

The project includes notebooks for testing and validation:
- `ML_train/5_test_each_image.ipynb`: Individual image testing
- `ML_train/4_test.ipynb`: Model validation tests

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

Project Developer - [Phan Văn Toàn](mailto:phanvantoan.contact@gmail.com)

Project Link: [https://github.com/givoxxs/baby_posture_analysis](https://github.com/givoxxs/baby_posture_analysis)

## 🔥 Firebase Threshold Listener

### Tính năng mới: Real-time Threshold Updates

Hệ thống hiện đã được tích hợp Firebase Snapshot Listener để lắng nghe thay đổi threshold values theo thời gian thực, loại bỏ việc phải đọc liên tục.

### Cách hoạt động

1. **Snapshot Listener**: Tự động lắng nghe thay đổi từ Firebase Firestore
2. **Real-time Updates**: Cập nhật threshold ngay lập tức khi có thay đổi
3. **Performance Optimization**: Giảm thiểu số lần gọi Firebase API
4. **Automatic Cleanup**: Tự động dọn dẹp listener khi device disconnect

### Threshold Values

- `sideThreshold`: Ngưỡng thời gian cho tư thế nằm nghiêng (giây)
- `proneThreshold`: Ngưỡng thời gian cho tư thế nằm sấp (giây)  
- `noBlanketThreshold`: Ngưỡng thời gian không có chăn (giây)

### Testing Firebase Threshold Listener

#### Chạy Test Cơ Bản

```bash
# Sử dụng script được cung cấp
python run_threshold_test.py
```

#### Test Manual

```bash
# Chạy test trực tiếp
python app/tests/test_firebase_threshold_listener.py
```

#### Quy trình Test

1. **Khởi chạy test**: Script sẽ kết nối tới device test ID
2. **Thiết lập listener**: Đăng ký lắng nghe thay đổi threshold
3. **Thay đổi threshold trên Firebase**:
   - Truy cập [Firebase Console](https://console.firebase.google.com/)
   - Tìm collection `devices`
   - Tìm document với ID: `18ff6551-820b-4aad-b714-1143629970f0`
   - Thay đổi các field: `sideThreshold`, `proneThreshold`, `noBlanketThreshold`
4. **Quan sát kết quả**: Test sẽ ghi nhận và hiển thị mọi thay đổi trong 60 giây

#### Kết quả mong đợi

```
🔥 THRESHOLD THAY ĐỔI LÚC 14:30:25:
   Side Threshold: 15
   Prone Threshold: 20  
   No Blanket Threshold: 120
```

### Implementation Details

#### Firebase Threshold Listener Service

- **File**: `app/services/firebase_threshold_listener.py`
- **Singleton Pattern**: Đảm bảo chỉ có một instance duy nhất
- **Thread-safe**: An toàn cho môi trường đa luồng
- **Auto-cleanup**: Tự động dọn dẹp khi không sử dụng

#### WebSocket Integration

- **Real-time updates**: Threshold được cập nhật ngay trong WebSocket connection
- **No polling**: Không cần đọc threshold định kỳ
- **Efficient**: Chỉ cập nhật khi có thay đổi thực sự

#### Device State Management

- **Dynamic thresholds**: DeviceState tự động cập nhật threshold từ listener
- **Backward compatibility**: Vẫn hỗ trợ cách cũ nếu cần
- **Logging**: Ghi log đầy đủ cho việc debug

### Benefits

1. **Performance**: Giảm số lần gọi Firebase API
2. **Real-time**: Cập nhật ngay lập tức khi threshold thay đổi
3. **Reliability**: Ít bị lỗi do network hoặc rate limiting
4. **Scalability**: Có thể handle nhiều devices đồng thời
5. **Maintainability**: Code sạch và dễ bảo trì

### Configuration

Threshold listener tự động hoạt động khi:
- Device kết nối qua WebSocket
- Firebase connection đã được thiết lập
- Device tồn tại trong Firestore

Không cần cấu hình thêm gì!