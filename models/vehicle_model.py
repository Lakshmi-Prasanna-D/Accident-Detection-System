from ultralytics import YOLO

class VehicleModel:
    def __init__(self, model_path="yolo11n.pt"):
        # We also check Yolov8n.pt if yolo11n.pt fails
        try:
            self.model = YOLO(model_path)
        except:
            self.model = YOLO("yolov8n.pt")
            
        self.vehicle_classes = [2, 3, 5, 7] # car, motorcycle, bus, truck in COCO
        
    def predict(self, frame):
        results = self.model.track(frame, classes=self.vehicle_classes, persist=True, verbose=False)
        detections = []
        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    # YOLO track assigns persistent IDs to recognized moving targets
                    track_id = int(box.id[0]) if (box.id is not None) else -1
                    
                    if conf > 0.3:
                        detections.append({
                            "bbox": (x1, y1, x2, y2),
                            "conf": conf,
                            "class": f"Target #{track_id}" if track_id != -1 else "Vehicle",
                            "track_id": track_id,
                            "color": (0, 255, 0)
                        })
        return detections
