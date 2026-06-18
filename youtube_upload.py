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
from api_configs.gemini_config import generate_chat_response



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

def video_upload(video_path, youtube, title: str, description: str, tags: list, tries:int = 0):
    time.sleep(20)
    total_file_size = os.path.getsize(video_path)

    request_body = {
        "snippet": {
            "title": title, 
            "description": description,
            "categoryId": "17",
            "tags": tags,
            "defaultLanguage": "en"
        },
        "status": {
            "privacyStatus": "private",
            "embeddable": True,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
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
            return video_upload(video_path, youtube, title, description, tags, tries +1)

    print(f"Upload complete! Video ID: {response['id']}")
    video_id = response['id']
    video_url = f"https://youtu.be/{video_id}"
    print(f"video_id: {video_id}")
    return video_id

def upload_thumbnail(youtube, video_id, thumbnail_path):
    """
    Uploads a local image file as the custom thumbnail for a specific YouTube Video ID.
    """
    time.sleep(30)
    try:
        print(f"Uploading custom thumbnail: {thumbnail_path}...")
        
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=googleapiclient.http.MediaFileUpload(
                thumbnail_path, 
                mimetype="image/jpeg" # Change to image/png if using PNG
            )
        )
        response = request.execute()
        print("Thumbnail uploaded successfully!")
        return response
    except Exception as e:
        print(f"Failed to upload thumbnail: {e}")
        return None



def generate_meta(topic):
    with open(upload_dir / f"{topic}_script_{today}.json", "r") as file:
        data = json.load(file)
    
    format = """{'title': title..., 'description': description..., 'tags': [tag1, tag2, tag3... no more than 400 character worth of seo optimized tags], 'thumbnail_prompt': generate a prompt for grok to generate a related thumbnail to the video}"""
    prompt = f"here is the script of my daily news video on {topic}: ### {data} ### please write clickbait title, seo optimised description and no more than 400 characters worth of seo optomised tages seperated by commas in a list [] inside a json like ### {format} ### out put only the object / json no spaces or words either side, no trailing charcters or symbols. trying include at least one opular name mentioned in the video in the title. you are a youtube clickbait and seo expert. make sure the prompt for the thumbnail is well detailed related to the video and a little bit clickbait. in the description include 'triathlon news for {today}' and 'this video is auto generated as part of a computer science students personal project, if this video contains your media and you dont want it on here comment in the comment section and i will remove the video within a couple of days thank you' "
    def generate_meta_gemini(prompt):
        result = generate_chat_response(prompt)
        if "Gemini SDK Error" in result or "Sorry, I'm having trouble thinking right now. Please try again later." in result:
                return generate_meta_gemini(prompt)
        else:
            return result
    result = generate_meta_gemini(prompt)
    print(result)
    clean_response = result.strip()
    cleaned = re.sub(r'^```[a-zA-Z]*\n|```$', '', clean_response, flags=re.MULTILINE).strip()
    result_json = json.loads(cleaned)
    return result_json

def publish_video(youtube, video_id):
    """
    Updates the video privacy status from private to public.
    """
    try:
        print(f"Publishing video {video_id} to public...")
        request = youtube.videos().update(
            part="status",
            body={
                "id": video_id,
                "status": {
                    "privacyStatus": "public"
                }
            }
        )
        response = request.execute()
        print("Video is now PUBLIC!")
        return response
    except Exception as e:
        print(f"Failed to publish video: {e}")
        return None
