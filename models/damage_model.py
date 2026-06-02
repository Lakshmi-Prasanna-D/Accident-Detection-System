from ultralytics import YOLO

class DamageModel:
    def __init__(self, model_path="car-damage.pt"):
        self.model = YOLO(model_path)
        # Severity might be numerical, map it if possible
        
    def predict(self, frame):
        results = self.model(frame, verbose=False)
        detections = []
        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    if conf > 0.4:
                        label = f"Severity {cls_id}"
                        # Try to map numeric class to standard names if it aligns
                        if cls_id == 0: label = "Minor Damage"
                        elif cls_id == 1: label = "Moderate Damage"
                        elif cls_id == 2: label = "Severe Damage"
                        
                        detections.append({
                            "bbox": (x1, y1, x2, y2),
                            "conf": conf,
                            "class": label,
                            "color": (255, 165, 0) # BGR orange for damage
                        })
        return detections
