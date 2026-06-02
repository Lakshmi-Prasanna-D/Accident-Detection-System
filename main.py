import uvicorn
from webapp.app import app

def main():
    print("Starting  - AI Urban Response & Analysis Web Server...")
    uvicorn.run("webapp.app:app", host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
