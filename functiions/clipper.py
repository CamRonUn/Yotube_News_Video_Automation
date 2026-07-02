import subprocess
from pathlib import Path
import re

cwd = Path(".")
video_dir = cwd.parent / "videos"
clips_dir = cwd.parent / "clips"


def ffmpeg_trim(file_name: str, start_time: str, end_time: str, title, tries:int = 0, max_retries: int = 3 ) -> str:
    
    best_match = ""
    best_score = 0 
    file_name_parts = re.split(r'[ \[\]\.,\?]', file_name)
    for file in video_dir.iterdir():
        if file.name[-4:] == ".mp4":
            file_split = re.split(r'[ \[\]\.,\?]', file.name)
            score = 0
            for part in file_split:
                if part in file_name_parts: 
                    score += 1
            if score > best_score:
                best_score = score
                best_match = file.name
    
    original_path = Path(video_dir / best_match).resolve()
    output_path = str((clips_dir / f"{title}.mp4").resolve())
    
    print(f"original path: {original_path}")
    print(f"original path: {output_path}")

    strategy = [
        "ffmpeg",
        "-y",
        "-ss",
        start_time,
        "-to",
        end_time,
        "-i",
        str(original_path),
        # FIXED FILTER: Scale width to 1080 (maintaining aspect ratio), then letterbox pad to 1080x1920
        "-vf",
        "scale=1080:-1,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        output_path,
    ]

    try:
        # Added check=True so an FFmpeg crash actually triggers the except block
        result = subprocess.run(strategy, capture_output=True, text=True, check=True)
        print(f"{title} trimmed success ✅")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg failed on attempt {tries}. Error log:")
        print(e.stderr)  # Directly prints the exact error FFmpeg threw

        if tries < max_retries:
            print(f"Retrying entry... ({tries + 1}/{max_retries})")
            return ffmpeg_trim(
                file_name, start_time, end_time, title, tries + 1, max_retries
            )
        else:
            print(f"Giving up on {(title)} ❌")
            return ""
    except Exception as e:
        print(f"Unexpected Python error: {e}")
        return ""

