import requests

API_KEY = "inAu5IBCdwLtKGXme4ES2Wz301TRYvDxoQHb7hgrPMkpjOcJF9J98aVxMp3wYeTvWbGn0sZyiQ2UfmkI"

def send_sms_alert(location, severity):
    url = "https://www.fast2sms.com/dev/bulkV2"

    message = f"ACCIDENT ALERT!\nLocation: {location}\nSeverity: {severity}"

    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "numbers": "9391736652"   # WITHOUT +91
    }

    headers = {
        "authorization": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("✅ SMS Response:", response.json())
    except Exception as e:
        print("❌ SMS FAILED:", e)
    
    