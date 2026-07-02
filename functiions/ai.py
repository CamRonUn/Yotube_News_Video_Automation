import os
from dotenv import load_dotenv
import re
from google import genai 
from pathlib import Path
from functiions.file_functions import script_to_json
from functiions.clipper import ffmpeg_trim
from functiions.upload import video_upload

load_dotenv()
cwd = Path(".")
videos_dir = cwd.parent / "videos"


# The client is now inside 'genai'
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_chat_response(prompt: str):
    try:
        # Note: In the latest SDK, it's client.models.generate_content
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini SDK Error: {e}")
        return "I'm having trouble thinking right now."
    
def gemma(prompt: str):
    try:
        # Note: In the latest SDK, it's client.models.generate_content
        response = client.models.generate_content(
            model="gemma-4-31b-it", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini SDK Error: {e}")
        return "I'm having trouble thinking right now."

def clips(title, youtube,topic):
    best_match = ""
    best_score = 0 
    file_name_parts = re.split(r'[ \[\]\.,\?]', title)
    try:
        for file in videos_dir.iterdir():
            if file.name[-4:] == ".mp4":
                file_split = re.split(r'[ \[\]\.,\?]', file.name)
                score = 0
                for part in file_split:
                    if part in file_name_parts: 
                        score += 1
                if score > best_score:
                    best_score = score
                    best_match = file.name[:-4]
        with open(videos_dir / f"{best_match}.en.vtt") as file:
            script = file.read()
        outputFormat = "{title: video title, description: description: tags: [tag1, tag2, ... 300 characters worth of tage], start_time: HH:MM:SS, end_time: HH:MM:SS,}"
        prompt = f"""please clips this video up into youtube shorts make as many promising shorts as possible based on the subtitles {script}
                    out put it with the youtube meta data needed in exactly this format for json no trailing white space or characters ### {outputFormat} ###
                    try use athletes names in title and the event name in title on description title of the video is {title}
                    make sure video is no longer than 45 seconds"""
        response = generate_chat_response(prompt)
        json = script_to_json(response)
        for index, video in enumerate(json): 
            output_path = ffmpeg_trim(best_match, video['start_time'], video['end_time'], video['title'])
            video_upload(output_path, youtube, video['title'], video['description'], video['tags'], topic)
    except:
        return False

        
