import cv2
import time

streams = [
    f"https://video.dot.state.mn.us/public/C{i}.stream/playlist.m3u8" for i in range(110, 115)
]

for url in streams:
    print(f"Testing {url}...")
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print(f"FAILED to open {url}")
        continue
    
    ret, frame = cap.read()
    if ret:
        print(f"SUCCESS: Read frame from {url}, shape: {frame.shape}")
        cv2.imwrite(f"test_{url.split('/')[-2]}.jpg", frame)
    else:
        print(f"FAILED: Opened but could not read frame from {url}")
    cap.release()
