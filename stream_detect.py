import cv2
import time
from ultralytics import YOLO
from sms_service import send_sms_alert   # your SMS file

# -------------------------------
# LOAD MODELS (ONLY ONCE)
# -------------------------------
vehicle_model = YOLO("yolo11n.pt")
accident_model = YOLO("acc_best.pt")
severity_model = YOLO("car-damage.pt")

# -------------------------------
# CONFIG
# -------------------------------
CAMERA_URL = "https://video.dot.state.mn.us/public/C9181.stream/playlist.m3u8"

ACCIDENT_CONF = 0.3
SEVERITY_CONF = 0.4
SMS_COOLDOWN = 30   # seconds

# -------------------------------
# STATE VARIABLES
# -------------------------------
last_sms_time = 0

# -------------------------------
# START STREAM
# -------------------------------
cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print("❌ Error opening stream")
    exit()

print("✅ Stream started...")

while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Stream ended")
        break

    frame = cv2.resize(frame, (960, 540))

    accident_detected = False
    severity_label = "UNKNOWN"

    # -------------------------------
    # VEHICLE DETECTION
    # -------------------------------
    vehicle_results = vehicle_model.track(
        frame,
        persist=True,
        classes=[2, 3, 5, 7]
    )

    if vehicle_results:
        for r in vehicle_results:
            if r.boxes is None:
                continue

            for box in r.boxes.xyxy:
                x1, y1, x2, y2 = map(int, box)

                # Draw vehicle box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

                # -------------------------------
                # CROP VEHICLE REGION (IMPORTANT)
                # -------------------------------
                crop = frame[y1:y2, x1:x2]

                if crop.size == 0:
                    continue

                # -------------------------------
                # ACCIDENT DETECTION (ON CROP)
                # -------------------------------
                accident_results = accident_model(crop, conf=ACCIDENT_CONF)

                for ar in accident_results:
                    if ar.boxes is None:
                        continue

                    accident_detected = True

                    # Draw accident box (relative → convert to full frame)
                    for abox in ar.boxes.xyxy:
                        ax1, ay1, ax2, ay2 = map(int, abox)

                        cv2.rectangle(
                            frame,
                            (x1 + ax1, y1 + ay1),
                            (x1 + ax2, y1 + ay2),
                            (0, 0, 255),
                            3
                        )

                        cv2.putText(
                            frame,
                            "ACCIDENT",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 0, 255),
                            2
                        )

                # -------------------------------
                # SEVERITY DETECTION
                # -------------------------------
                if accident_detected:
                    severity_results = severity_model(crop)

                    for sr in severity_results:
                        if sr.boxes is None:
                            continue

                        for sbox, cls, conf in zip(
                            sr.boxes.xyxy,
                            sr.boxes.cls,
                            sr.boxes.conf
                        ):
                            if conf < SEVERITY_CONF:
                                continue

                            severity_label = f"Level {int(cls)}"

                            sx1, sy1, sx2, sy2 = map(int, sbox)

                            cv2.rectangle(
                                frame,
                                (x1 + sx1, y1 + sy1),
                                (x1 + sx2, y1 + sy2),
                                (255, 0, 0),
                                2
                            )

                            cv2.putText(
                                frame,
                                severity_label,
                                (x1, y2 + 20),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255, 0, 0),
                                2
                            )

    # -------------------------------
    # SEND SMS (WITH COOLDOWN)
    # -------------------------------
    if accident_detected:
        current_time = time.time()

        if current_time - last_sms_time > SMS_COOLDOWN:
            print("🚨 Accident detected! Sending SMS...")
            send_sms_alert("CAMERA_01", severity_label)
            last_sms_time = current_time

    # -------------------------------
    # DISPLAY
    # -------------------------------
    cv2.imshow("AURA - Accident Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# -------------------------------
# CLEANUP
# -------------------------------
cap.release()
cv2.destroyAllWindows()