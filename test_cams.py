import cv2
from streaming.cctv_scraper import CCTVScraper

scraper = CCTVScraper()
streams = scraper.get_streams()

for i, stream in enumerate(streams):
    print(f"Testing stream {i}: {stream}")
    cap = cv2.VideoCapture(stream)
    if not cap.isOpened():
        print("  ❌ Failed to open stream.")
        continue
    
    ret, frame = cap.read()
    if not ret:
        print("  ❌ Opened, but failed to read a frame.")
    else:
        print(f"  ✅ Success! Frame shape: {frame.shape}")
    cap.release()
