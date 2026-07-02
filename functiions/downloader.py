import subprocess
from pathlib import Path
from datetime import date,timedelta
import os 
import json

# important paths 
cwd = Path(".")
video_dir = cwd.parent / "videos"

#date 
today = date.today().strftime("%Y%m%d") #formated for yt-dlp date after
yesterday =  (date.today() - timedelta(days=1)).strftime("%Y%m%d")
todayAfter = date.today().strftime("%Y-%m-%d") #Formated for YT :after search 
yesterdayAfter =  (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        
def check_yt_intalled() -> bool:
    #check if yt-dlp is installed returns bool 
    try: 
        subprocess.run(["yt-dlp", "-h"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False

def getVideos(searchTerm:str, number_of_videos: str = "2"):
    print("Fetching YT Videos: ")
    result = subprocess.run([
        "yt-dlp",
        "--default-search", f"ytsearch{number_of_videos}",
        "--extractor-args", "youtube:search_sort=view_count",
        "-P", video_dir,
        "--dateafter", yesterday,
        "--max-downloads", number_of_videos,
        "--write-subs",
        "--write-auto-subs",
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "-t", "mp4",
        "--no-part",
        "--live-from-start",
        "--wait-for-video", "30",
        searchTerm + f" after:{yesterdayAfter}",
    ], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

def getVideoUrl(url: str):
    print("Fetching YT Video via URL...")
    result = subprocess.run([
        "yt-dlp",
        "-P", video_dir,
        # Keep sub and comment extraction if needed
        "--write-subs",
        "--write-auto-subs",
        # Ensures max height remains 720p 
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "--merge-output-format", "mp4", # Replaced -t mp4 with the cleaner merge argument
        "--no-part",
        "--live-from-start",
        "--wait-for-video", "30",
        url  # Simply pass the target URL string here
    ], capture_output=True, text=True)
    
    print(result.stdout)
    print(result.stderr)

