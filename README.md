<<<<<<< HEAD
# AURA: AI Urban Response & Analysis

AURA is a professional-grade, real-time urban safety monitoring system designed to detect road accidents and traffic anomalies using advanced computer vision. Built for mission-critical monitoring, AURA integrates YOLOv11 deep learning models with a high-concurrency telemetry backend to provide instant situational awareness for emergency responders.

## 🚀 Key Features

- **Real-time Incident Detection**: Automated identification of collisions and vehicle damage across multiple urban nodes using YOLOv11.
- **Smart Telemetry Dashboard**: Live monitoring of "System Health" and "Performance Percent" calculated through CPU load and inference latency.
- **Multi-Node Monitoring**: Synchronized streaming from high-visibility urban sensors (Nodes C111, C112, C114) with optimized contrast for AI processing.
- **Live Alert Center**: Instant WebSocket-based notifications for critical incidents, complete with severity categorization and location tagging.
- **AI Operational Intelligence**: Granular analytics including camera-wise performance metrics, incident trends, and ratio distributions.
- **Data Governance**: Integrated administrative tools to clear active log buffers and purge historical records via secure API endpoints.
- **Media Invalidation**: Support for uploading and analyzing custom video/image files for incident verification and simulation.

## 🧬 Working Principle (Architectural Flow)

The AURA pipeline operates on a high-fidelity "Trigger-Verify-Dispatch" logic:

1.  **Data Ingestion**: High-definition frames are ingested from authorized CCTV streams at a variable FPS based on current network bandwidth.
2.  **Primary Inference**: The frame passes through a specialized YOLOv11 vehicle model to isolate active objects in the urban network.
3.  **Collision Logic (The "Hazard" Check)**: 
    *   If no hazard is detected, the system updates global traffic stats and secures a "Safe Flow" log.
    *   If a potential collision is identified with >0.75 confidence, the system triggers the secondary verification phase.
4.  **Secondary Damage Assessment**: A specialized damage detection model analyzes the hazard zone to classify severity (Minor/Major) and confirm the incident integrity.
5.  **Telemetry Dispatch**: Confirmed alerts are broadcasted via WebSockets to the mission control dashboard, triggering visual alarms and emergency dispatch protocols.

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python) - High performance, asynchronous API framework.
- **Artificial Intelligence**: Ultralytics YOLOv11 - State-of-the-art object detection and instance segmentation.
- **Computer Vision**: OpenCV (cv2) - Real-time image processing and stream handling.
- **Frontend**: Vanilla JS (ES6+), Jinja2 Templates, Modern CSS (Glassmorphism & Dark Mode).
- **Data Visualization**: Chart.js - Dynamic, real-time performance and trend mapping.
- **Communication**: WebSockets (WS) - Bi-directional, low-latency telemetry streaming.

## 🗺️ System Routes

- `/dashboard`: High-level system overview including health, performance, and node status.
- `/live`: Real-time monitoring grid with AI-augmented bounding boxes.
- `/architecture`: Visual breakdown of the AI operational logic and decision pipeline.
- `/history`: Audit trail of previously detected incidents and system logs.
- `/alerts`: Dedicated mission-control feed for active, high-priority incident notifications.
- `/analytics`: Statistical deep-dive into urban safety trends and sensor performance.

## ⚙️ Setup & Execution

1.  **Environment**: Ensure Python 3.9+ is installed.
2.  **Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Server**:
    ```bash
    python main.py
    ```
4.  **Access**: Navigate to `http://localhost:8000` in any modern web browser.

---
**AURA: Securing the Urban Network through Intelligent Observation.**
=======
# Accident-Detection-System
>>>>>>> 967d32bc8dda75d9484805041b6135ff5ff8124a
