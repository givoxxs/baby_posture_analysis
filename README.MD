# Baby Posture Analysis

A system for analyzing baby posture in images to detect potential risks.

## Features

* Image preprocessing for optimal pose detection
* MediaPipe-based pose keypoint detection
* Posture feature extraction and analysis
* Risk assessment for baby sleeping positions

## Architecture

The system follows a modular pipeline architecture:

1. **Image Preprocessing Module**:
   * Resize images to standard dimensions
   * Color normalization and enhancement
   * Noise filtering
   * Special enhancements for pose detection

2. **Keypoint Extraction Module**:
   * MediaPipe Pose for skeletal keypoint detection
   * 33 standard body keypoints with 3D coordinates
   * Confidence/visibility scores for each keypoint

3. **Posture Feature Construction Module**:
   * Head-torso angle detection
   * Limb angle calculations
   * Blanket kicked-off detection
   * Face-down detection

4. **Risk Analysis Module**:
   * Assessment of sleeping position safety
   * Risk scoring system (1-10 scale)
   * Detailed reasoning for risk assessment

## Setup & Installation

### Prerequisites

* Python 3.8+
* OpenCV
* MediaPipe
* FastAPI

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/baby_posture_analysis.git
   cd baby_posture_analysis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create an `.env` file (or use the example provided):
   ```
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

## Usage

1. **Run the API server:**
   ```bash
   uvicorn app.main:app --reload --host $API_HOST --port $API_PORT
   ```
   Or
   ```bash
   uvicorn app.main:app --reload
   ```
   (using default values from `.env`)

2. **Access the API documentation:**
   Open your web browser and go to `http://localhost:8000/docs` for interactive API documentation.

3. **Test with the HTML page:**
   Open your web browser and go to `http://localhost:8000`. You'll see a simple HTML page that allows you to upload an image and see the analysis results.

## API Endpoints

* `/api/images/process` (POST):
  * Process an image with quality enhancements
  * Parameters: `file`, `high_resolution`, `apply_filter`

* `/api/pose/detect` (POST):
  * Detect pose keypoints from an image
  * Parameters: `file`, `high_resolution`, `include_annotated_image`, `include_analysis`

* `/api/pose/analyze` (POST):
  * Analyze baby posture and risk level
  * Parameters: `file`, `high_resolution`

* `/api/pipeline/analyze` (POST):
  * Complete pipeline - process image, detect pose, and analyze risk
  * Parameters: `file`, `high_resolution`

## License

This project is licensed under the MIT License - see the LICENSE file for details.