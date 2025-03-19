# Baby Posture Detection API
This project provides a REST API for detecting the posture of a baby from images using MediaPipe. It can identify postures like lying on stomach, face down, folded limbs, kicking off blankets, and lying on the side. The API can trigger alerts when a dangerous posture is detected.

## Features

*   **Image-based posture detection:** Analyzes images to identify baby's posture.
*   **MediaPipe integration:** Uses MediaPipe for fast and efficient keypoint extraction.
*   **Risk analysis:** Assesses the risk level of the detected posture.
*   **Alert system:** Sends alerts (e.g., push notifications, SMS - *configurable*) when a dangerous posture is detected.
*   **REST API:** Provides a simple API for easy integration with other applications (e.g., a mobile app).
*   **Customizable:** Easily configurable through environment variables (`.env` file).
*   **Expandable:** Designed to be easily extended with new features (e.g., video processing, sleep analysis).

## Prerequisites

*   Python 3.7+
*   pip

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <your_repository_url>
    cd baby_posture_detection
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    ```

3.  **Activate the virtual environment:**

    *   **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        venv\Scripts\activate
        ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Create a `.env` file:**

    *   Copy the example `.env.example` file (if you have one) to `.env`:  `cp .env.example .env`
    *  Or Create new .env file
    *   Fill in the required environment variables (API keys, thresholds, etc.) in the `.env` file.  See the `.env` section below for details.

## Usage

1.  **Run the API server:**

    ```bash
    uvicorn app.main:app --reload --host $API_HOST --port $API_PORT
    ```
    Or
     ```bash
    uvicorn app.main:app --reload
    ```
     (sử dụng giá trị mặc định từ `.env`)

2.  **Access the API documentation:**

    Open your web browser and go to `http://localhost:8000/docs` (or `http://localhost:8000/redoc` for alternative documentation). You can test the API endpoints directly from the documentation.

3.  **Test with the HTML page:**

    Open your web browser and go to `http://localhost:8000`.  You'll see a simple HTML page that allows you to upload an image and see the detection results.

## API Endpoints

*   `/images/detect` (POST):
    *   **Request:**  A multipart/form-data request with an `image` field containing the image file.
    *   **Response:**  A JSON object with the following fields:
        *   `posture`: The detected posture (e.g., "An toàn", "Có nguy cơ", "Nguy hiểm").
        *   `risk_level`:  An integer representing the risk level (1-10).
        *   `risk_reason`: String describe the reason.
        *   `keypoints` (optional):  A list of keypoints detected by MediaPipe.
        *   `alert_sent`: True/False
        *   `alert_message`: String.

## .env Configuration

The `.env` file contains environment variables that control the behavior of the application.  Here are some of the key variables:

| Variable                    | Description                                                                       | Default  |
| --------------------------- | --------------------------------------------------------------------------------- | -------- |
| `API_HOST`                  | The host address for the API server.                                                | 0.0.0.0  |
| `API_PORT`                  | The port number for the API server.                                                 | 8000     |
| `RELOAD_ON_CHANGE`          | Whether to automatically reload the server on code changes (for development).    | True     |
| `MODEL_COMPLEXITY`         | The complexity of the MediaPipe Pose model (0, 1, or 2).                          | 2        |
| `MIN_DETECTION_CONFIDENCE` | The minimum confidence score for person detection.                                | 0.5      |
| `ALERT_THRESHOLD`          | The risk level threshold for sending alerts.                                      | 7        |
| `IMAGE_WIDTH`              | Width of image before using mediapipe                                                 | 256        |
| `IMAGE_HEIGHT`             | Height of image before using mediapipe                                                 | 256     |
| ...                         | Other configuration variables (e.g., for alert systems, database, etc.).         |          |

## Project Structure


## Contributing

Contributions are welcome!  Please feel free to submit pull requests or open issues.