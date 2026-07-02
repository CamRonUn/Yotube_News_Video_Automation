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

def ffmpeg_trim(file_name: str, start_time: str, end_time:str) -> str:
    #enter times as '00:00:20' (HH:MM:SS)
    #saves video as trimmed file name at video_dir
    result = subprocess.run(["ffmpeg", "-y", "-i", file_name, "-ss", start_time, "-to", end_time,'-c:v', 'libx264', video_dir / f"trimmed_{file_name}"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) 
    if result.returncode == 0:
        print("Success!")
    else:
        print(f"Error: {result.stderr}")
        
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
        "--write-comments",
        "--write-subs",
        "--write-auto-subs",
        "-f", "bestvideo[height<=240]+bestaudio/best[height<=240]",
        "-t", "mp4",
        "--no-part",
        "--live-from-start",
        "--wait-for-video", "30",
        searchTerm + f" after:{yesterdayAfter}",
    ], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)



