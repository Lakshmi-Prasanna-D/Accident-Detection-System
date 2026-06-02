import cv2
import os
import sys
import glob
import time

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from detection.pipeline import DetectionPipeline

def debug_accidents():
    test_dir = "test_images"
    image_paths = glob.glob(os.path.join(test_dir, "*.png"))
    
    if not image_paths:
        print("No test images found!")
        return

    # Initialize pipeline (this loads the models)
    pipeline = DetectionPipeline("", pipeline_id="DEBUG")
    pipeline.start()
    
    print("\n--- Model Recognition Test ---")
    for img_path in image_paths:
        print(f"\nScanning: {os.path.basename(img_path)}")
        frame = cv2.imread(img_path)
        if frame is None:
            print("Failed to load image.")
            continue
            
        # 1. Check Raw Model Scores (bypass pipeline logic for a moment to see reality)
        results = pipeline.accident_model.model(frame, verbose=False)
        print("Raw Accident Confidence Scores:")
        found_any = False
        for r in results:
            if r.boxes:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    print(f"  - Accident Core: {conf:.4f}")
                    found_any = True
        if not found_any:
            print("  - [FAIL] No accident boxes detected by model at any confidence.")

        # 2. Check Pipeline Processing Logic
        pipeline.set_stream_url(img_path)
        
        # Give the read thread time to load the image
        retries = 10
        while pipeline.latest_frame is None and retries > 0:
            time.sleep(0.5)
            retries -= 1
            
        processed_frame = pipeline.process_frame()
        
        # Check if pipeline flagged it
        status = pipeline.last_status
        if status == "ACCIDENT":
            print(f"  - [SUCCESS] Pipeline flagged as ACCIDENT.")
        else:
            print(f"  - [FAIL] Pipeline missed the accident. Current status: {status}")

if __name__ == "__main__":
    debug_accidents()
