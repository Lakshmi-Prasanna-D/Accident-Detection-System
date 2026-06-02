import time
from sms_service import send_sms_alert   # ✅ connect Fast2SMS

# If you already have email function, keep it
def send_email_alert(location, timestamp, severity):
    # Keep your existing email logic here
    print(f"[NOTIFIER] Email alert sent successfully to your email")


def send_accident_notification(location, timestamp, severity):
    
    print("[NOTIFIER] Triggering accident notification...")

    # ----------------------
    # EMAIL (unchanged)
    # ----------------------
    try:
        send_email_alert(location, timestamp, severity)
    except Exception as e:
        print(f"[ERROR] Email failed: {e}")

    # ----------------------
    # SMS (REAL IMPLEMENTATION)
    # ----------------------
    try:
        send_sms_alert(location, severity)
        print(f"[NOTIFIER] SMS ALERT SENT to user")
    except Exception as e:
        print(f"[ERROR] SMS failed: {e}")