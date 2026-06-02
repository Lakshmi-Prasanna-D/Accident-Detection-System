import cv2
import threading
import time
import os
import sys

# Add the project root to sys.path so we can import models if this script is run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.vehicle_model import VehicleModel
from models.accident_model import AccidentModel
from models.damage_model import DamageModel
from utils.notifications import send_accident_notification


class DetectionPipeline:
    # Shared models to save memory across multiple pipelines
    _models = {}
    _model_lock = threading.Lock()

    def __init__(self, stream_url, pipeline_id="Main"):
        self.stream_url = stream_url
        self.pipeline_id = pipeline_id
        
        if "vehicle" not in DetectionPipeline._models:
            DetectionPipeline._models["vehicle"] = VehicleModel("yolo11n.pt")
        if "accident" not in DetectionPipeline._models:
            DetectionPipeline._models["accident"] = AccidentModel("acc_best.pt")
        if "damage" not in DetectionPipeline._models:
            DetectionPipeline._models["damage"] = DamageModel("car-damage.pt")

        self.vehicle_model = DetectionPipeline._models["vehicle"]
        self.accident_model = DetectionPipeline._models["accident"]
        self.damage_model = DetectionPipeline._models["damage"]
        
        self.is_running = False
        self.latest_alert = None
        self.stats = {
            "accidents": 0, 
            "vehicles": 0,         # Live count in current frame
            "total_detections": 0, # Cumulative unique vehicles
            "frames_processed": 0,
            "total_latency": 0,
            "conf_sum": 0,
            "conf_count": 0
        }
        self.lock = threading.Lock()
        
        self.cap = None
        self.latest_frame = None
        self.read_thread = None
        self.is_image_source = False
        self.last_status = "INITIAL"
        self.seen_vehicles = set() # Track unique IDs
        
    def _read_stream(self):
        current_url = None
        test_img = None
        
        while self.is_running:
            # Check if URL changed
            sync_url = None
            with self.lock:
                sync_url = self.stream_url
                
            if sync_url != current_url:
                current_url = sync_url
                self.is_image_source = False
                test_img = None
                
                cap = self.cap
                if cap is not None:
                    cap.release()
                    self.cap = None
                    
                # Avoid running imread on network URLs
                if current_url and not str(current_url).startswith("http"):
                    try:
                        test_img = cv2.imread(current_url)
                        self.is_image_source = test_img is not None
                    except:
                        pass
                
                if not self.is_image_source and current_url:
                    try:
                        new_cap = cv2.VideoCapture(current_url)
                        if new_cap and new_cap.isOpened():
                            new_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                            self.cap = new_cap
                    except Exception as e:
                        print(f"Error opening stream: {e}")

            if self.is_image_source:
                # If it's a static image, just keep yielding the same frame
                with self.lock:
                    if test_img is not None:
                        self.latest_frame = test_img.copy()
                time.sleep(0.1) # Prevent high CPU usage for static images
                continue
                
            cap = self.cap
            if cap is None or not cap.isOpened():
                # Try re-opening if we have a URL and not an image
                if not self.is_image_source and current_url:
                    try:
                        new_cap = cv2.VideoCapture(current_url)
                        if new_cap and new_cap.isOpened():
                            new_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                            self.cap = new_cap
                        else:
                            time.sleep(2)
                    except:
                        time.sleep(2)
                else:
                    time.sleep(1)
                continue
                
            try:
                ret, frame = cap.read()
            except Exception as e:
                print(f"OpenCV Read Error: {e}")
                ret = False
                
            if not ret:
                if cap is not None:
                    cap.release()
                    self.cap = None
                time.sleep(1)
                continue
                
            with self.lock:
                self.latest_frame = frame
                
    def start(self):
        self.is_running = True
        self.read_thread = threading.Thread(target=self._read_stream, daemon=True)
        self.read_thread.start()
        
    def stop(self):
        self.is_running = False
        if self.read_thread:
            self.read_thread.join(timeout=2)
            
    def set_stream_url(self, new_url):
        with self.lock:
            self.stream_url = new_url
            self.latest_frame = None
            
    def get_latest_alert(self):
        with self.lock:
            alert = self.latest_alert
            self.latest_alert = None
            return alert
            
    def get_stats(self):
        with self.lock:
            s = self.stats.copy()
            # Calculate dynamic processing latency (avg of last frames)
            if s["frames_processed"] > 0:
                s["avg_latency"] = s["total_latency"] / s["frames_processed"]
                s["avg_conf"] = (s["conf_sum"] / s["conf_count"]) if s["conf_count"] > 0 else 0
            else:
                s["avg_latency"] = 0.1
                s["avg_conf"] = 0
            return s
            
    def process_frame(self):
        start_t = time.time()
        with self.lock:
            if self.latest_frame is None:
                return None
            frame = self.latest_frame.copy()
            self.latest_frame = None # Consume
            
        frame = cv2.resize(frame, (960, 540))
        
        # 1. Vehicle Detection - Use standard predict for images, track for video
        with DetectionPipeline._model_lock:
            if self.is_image_source:
                # Use standard predict for static images to avoid tracking artifacts
                vehicle_detections = self.vehicle_model.model(frame, classes=self.vehicle_model.vehicle_classes, verbose=False)
                # Convert results [Need to manually parse YOLO results object if calling .model directly]
                formatted_v_dets = []
                for r in vehicle_detections:
                    for box in r.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        if conf > 0.3: # Lowered from 0.5 to capture more vehicles in images
                            formatted_v_dets.append({"bbox": (x1, y1, x2, y2), "conf": conf, "class": "Vehicle", "color": (0, 255, 0)})
                vehicle_detections = formatted_v_dets
            else:
                vehicle_detections = self.vehicle_model.predict(frame)
        
        vehicles_detected = len(vehicle_detections) > 0
        
        # 2. Performance & Cumulative Tracking
        local_latency = time.time() - start_t
        conf_vals = [d["conf"] for d in vehicle_detections]
        
        with self.lock:
            self.stats["vehicles"] = len(vehicle_detections)
            self.stats["frames_processed"] += 1
            self.stats["total_latency"] += local_latency
            
            # Cumulative Unique Vehicles
            for d in vehicle_detections:
                tid = d.get("track_id", -1)
                if tid != -1 and tid not in self.seen_vehicles:
                    self.seen_vehicles.add(tid)
                    self.stats["total_detections"] += 1

            if conf_vals:
                self.stats["conf_sum"] += sum(conf_vals)
                self.stats["conf_count"] += len(conf_vals)
        
        max_severity = "Minor"
        accident_detections = []
        damage_detections = []
        
        # 3. Accident Detection
        # Separate thresholds: 
        # - Live Streams (CAM_): High threshold (0.75) to prevent false positives from moving traffic
        # - Uploads/Images: Low threshold (0.30) to catch everything in static media
        is_upload = "upload" in str(self.stream_url).lower() or self.is_image_source
        acc_threshold = 0.30 if is_upload else 0.75
        
        with DetectionPipeline._model_lock:
            accident_detections = self.accident_model.predict(frame, conf_threshold=acc_threshold) 
        
        # 4. Persistence Check for Live Video
        # We only flag a real accident in video if it persists for 3 frames
        force_detect = False
        if not is_upload:
            if len(accident_detections) > 0:
                self.acc_frame_count = getattr(self, "acc_frame_count", 0) + 1
                if self.acc_frame_count >= 3:
                    force_detect = True
            else:
                self.acc_frame_count = 0
        else:
            # For static uploads, immediate detection is fine
            force_detect = len(accident_detections) > 0

        # Run alert logic if confirmed
        if force_detect:
            with self.lock:
                current_time = time.time()
                cooldown = 20 # 20 second cooldown between alerts for same stream
                
                if current_time - getattr(self, "last_accident_time", 0) > cooldown:
                    self.stats["accidents"] += 1
                    self.last_accident_time = current_time
                    
                    # Populate damage detections to determine severity
                    with DetectionPipeline._model_lock:
                        damage_detections = self.damage_model.predict(frame)
                    
                    # Apply damage model classifications
                    max_severity = "Minor"
                    if len(damage_detections) > 0:
                        severity_labels = [d["class"].lower() for d in damage_detections]
                        if any("severe" in s for s in severity_labels): max_severity = "Severe"
                        elif any("moderate" in s for s in severity_labels): max_severity = "Moderate"
                        else: max_severity = "Minor"
                    
                    camera_id = self.pipeline_id if self.pipeline_id != "Main" else (self.stream_url.split("/")[-2] if "/" in self.stream_url else "Upload")
                    if "?" in camera_id: camera_id = camera_id.split("?")[0]
                    if "." in camera_id: camera_id = camera_id.split(".")[0]
                    if "uploads" in str(self.stream_url).lower(): camera_id = "Upload"

                    self.latest_alert = {
                        "type": "ACCIDENT",
                        "severity": max_severity,
                        "timestamp": int(time.time()),
                        "camera_id": camera_id
                    }
                    self.last_status = "ACCIDENT"

                    # Send external notifications (Email and Phone)
                    send_accident_notification(
                        location=camera_id,
                        timestamp=self.latest_alert["timestamp"],
                        severity=max_severity
                    )
        elif vehicles_detected:
            if self.last_status != "SAFE" and self.last_status != "ACCIDENT":
                with self.lock:
                    camera_id = self.pipeline_id if self.pipeline_id != "Main" else (self.stream_url.split("/")[-2] if "/" in self.stream_url else "Upload")
                    if "?" in camera_id: camera_id = camera_id.split("?")[0]
                    if "." in camera_id: camera_id = camera_id.split(".")[0]
                    
                    self.latest_alert = {
                        "type": "SAFE",
                        "severity": "None",
                        "timestamp": int(time.time()),
                        "camera_id": camera_id,
                        "msg": "Safe Flow: Vehicles Passing"
                    }
                self.last_status = "SAFE"
        else:
            if self.last_status != "IDLE":
                with self.lock:
                    camera_id = self.pipeline_id if self.pipeline_id != "Main" else (self.stream_url.split("/")[-2] if "/" in self.stream_url else "Upload")
                    if "?" in camera_id: camera_id = camera_id.split("?")[0]
                    
                    self.latest_alert = {
                        "type": "SAFE",
                        "severity": "None",
                        "timestamp": int(time.time()),
                        "camera_id": camera_id,
                        "msg": "Road Status: Clear"
                    }
                self.last_status = "IDLE"
        
        # 5. Drawing
        for d in vehicle_detections:
            self._draw_box(frame, d)
            
        if len(accident_detections) != 0:
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 60), (0, 0, 255), -1)
            cv2.putText(frame, "CRITICAL: ACCIDENT DETECTED - EMERGENCY CALLED", (50, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
            for d in accident_detections:
                self._draw_box(frame, d, thickness=4)
            for d in damage_detections:
                self._draw_box(frame, d, thickness=2, offset_y=-30)
            
        return frame
        
    def _draw_box(self, frame, det, thickness=2, offset_y=0):
        x1, y1, x2, y2 = det["bbox"]
        color = det["color"]
        label = det["class"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, thickness)
        text_bg_y1 = y1 - 25 + offset_y
        text_bg_y2 = y1 + offset_y
        if text_bg_y1 < 0:
            text_bg_y1 = y1 + 5
            text_bg_y2 = text_bg_y1 + 25
        cv2.rectangle(frame, (x1, text_bg_y1), (x1 + w, text_bg_y2), color, -1)
        cv2.putText(frame, label, (x1, text_bg_y2 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), max(thickness-1, 1))
