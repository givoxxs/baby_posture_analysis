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
   git clone https://github.com/yourusername/baby_posture_analysis.git
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
   Create an `.env` file in the project root with the following variables:
   ```
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

## 🖥️ Usage

### Starting the Server

1. **Run the API server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Or simply use:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the API documentation**:
   Open your web browser and navigate to:
   ```
   http://localhost:8000/docs
   ```
   This provides interactive Swagger UI documentation for testing all API endpoints.

3. **Test with the web interface**:
   Open your browser and go to:
   ```
   http://localhost:8000
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

Project Developer - [Your Name](mailto:your.email@example.com)

Project Link: [https://github.com/yourusername/baby_posture_analysis](https://github.com/yourusername/baby_posture_analysis)