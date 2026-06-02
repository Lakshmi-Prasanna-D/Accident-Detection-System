from ultralytics import YOLO

class AccidentModel:
    def __init__(self, model_path="acc_best.pt"):
        self.model = YOLO(model_path)
        
    def predict(self, frame, conf_threshold=0.55):
        results = self.model(frame, verbose=False)
        detections = []
        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    if conf > conf_threshold:
                        detections.append({
                            "bbox": (x1, y1, x2, y2),
                            "conf": conf,
                            "class": "ACCIDENT",
                            "color": (0, 0, 255) # BGR red
                        })
        return detections
