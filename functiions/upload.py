import os
from pathlib import Path
import googleapiclient.discovery
import googleapiclient.http
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timezone, date
from dotenv import load_dotenv
import os
import re
import json
import time


load_dotenv()

utc_now = datetime.now(timezone.utc)
today_time = utc_now.isoformat(timespec='seconds').replace('+00:00', 'Z')
today = date.today().strftime("%Y%m%d")


cwd = Path(".")
upload_dir = cwd / "ready_to_upload"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]

def authenticate_youtube():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    client_id = os.getenv('GOOGLE_CLIENT_ID')

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server(port=0)

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials
    )

    return youtube

def video_upload(video_path, youtube, title: str, description: str, tags: list, topic, tries:int =0):
    time.sleep(20)
    total_file_size = os.path.getsize(video_path)

    topic1 = "Triathlon"
    topic2= "swimming"
    topicx="running"
    topic3 = "Cycling"
    topic4 = "Coding and AI"
    topic5 = "Chineese Technology"
    topic6= "Travel Deals"

    if topic == topic1 or topic == topic2 or topic == topic3 or topic == topicx:
        cat = "17"
    elif topic == topic4 or topic == topic5:
        cat = "28"
    else: 
        cat = "19"

    request_body = {
        "snippet": {
            "title": title, 
            "description": description,
            "categoryId": cat,
            "tags": tags,
            "defaultLanguage": "en"
        },
        "status": {
            "privacyStatus": "public",
            "embeddable": True,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": False,
            "recordingDate": today_time
        }
    }

    chunksize = 5 * 1024 * 1024 
    media_file = googleapiclient.http.MediaFileUpload(
        str(video_path), 
        chunksize=chunksize, 
        resumable=True
    )


    request = youtube.videos().insert(
        part="snippet,status",
        body = request_body,
        media_body=media_file
    )

    response = None
    max_retries = 5 
    attempt = 0
    bytes_uploaded = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                bytes_uploaded = status.resumable_progress
                percent = int(status.progress() * 100)
                print(f"Upload Progress: {percent}% ({bytes_uploaded}/{total_file_size} bytes)")

            if response is not None:
                bytes_uploaded = total_file_size
                print(f"Upload Progress: 100% ({bytes_uploaded}/{total_file_size} bytes)")

            attempt = 0  # reset on success
        except googleapiclient.errors.HttpError as e:
            if e.status_code in (500, 502, 503, 504):  # retryable server errors
                attempt += 1
                if attempt > max_retries:
                    print(f"Max retries reached. Giving up.")
                    raise
                wait = 2 ** attempt
                print(f"Server error {e.status_code}, retrying in {wait}s (attempt {attempt}/{max_retries})...")
                time.sleep(wait)
            else:
                print(f"Non-retryable HTTP error: {e.status_code} - {e.reason}")
                raise
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                print(f"Max retries reached. Giving up.")
                raise
            wait = 2 ** attempt
            print(f"Unexpected error: {e}, retrying in {wait}s (attempt {attempt}/{max_retries})...")
            time.sleep(wait)

    if bytes_uploaded < total_file_size:
        print(f"CRITICAL: Upload loop finished but only transferred {bytes_uploaded} of {total_file_size} bytes.")
        if tries <= 3:
            return video_upload(video_path, youtube, title, description, tags, topic, tries +1)

    print(f"Upload complete! Video ID: {response['id']}")
    video_id = response['id']
    video_url = f"https://youtu.be/{video_id}"
    print(f"video_id: {video_id}")
    return video_id
