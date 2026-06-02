import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os

from sms_service import send_sms_alert   # ✅ SMS integration

# -------------------------------
# CONFIGURATION
# -------------------------------
SENDER_EMAIL = "sailakshmiprasannadulam@gmail.com"
SENDER_PASSWORD = "lrmtfbytbdxzfawb"  # ⚠️ replace this
RECIPIENT_EMAIL = "sailakshmiprasannadulam@gmail.com"


def send_accident_notification(location, timestamp, severity):
    """
    Sends email + SMS alert
    """

    # -------------------------------
    # FORMAT TIME
    # -------------------------------
    if isinstance(timestamp, (int, float)):
        formatted_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    else:
        formatted_time = str(timestamp)

    subject = f"🚨 Accident Detected at {location}"
    
    message_body = (
        f"AURA Alert System\n"
        f"-----------------\n"
        f"Event: ACCIDENT DETECTED\n"
        f"Location: {location}\n"
        f"Timestamp: {formatted_time}\n"
        f"Severity: {severity}\n"
        f"-----------------\n"
        f"Please check immediately."
    )

    # -------------------------------
    # EMAIL ALERT
    # -------------------------------
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject

        msg.attach(MIMEText(message_body, 'plain'))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"[NOTIFIER] ✅ Email sent to {RECIPIENT_EMAIL}")

    except Exception as e:
        print(f"[ERROR] Email failed: {e}")

    # -------------------------------
    # SMS ALERT (REAL)
    # -------------------------------
    try:
        send_sms_alert(location, severity)
        print("[NOTIFIER] ✅ SMS API CALLED")
    except Exception as e:
        print(f"[ERROR] SMS failed: {e}")