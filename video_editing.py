import subprocess
from pathlib import Path
from datetime import date, timedelta, datetime
import os
import json
import moviepy.config as mpy_config
from api_configs.gemini_config import gemma
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip, concatenate_videoclips, ImageClip
from icrawler.builtin import BingImageCrawler
from moviepy.video.fx.all import loop
import time
import re
import unicodedata
import requests
import logging
import random
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

mpy_config.IMAGEMAGICK_BINARY = "magick"

# important paths
cwd = Path(".")
video_dir = cwd / "videos"
clip_dir = cwd / "video_clips"
script_dir = cwd / "script"
audio_dir = cwd / "audio_files"
upload_dir = cwd / "ready_to_upload"
image_dir = cwd / "generated_images"

# date
today = date.today().strftime("%Y%m%d")
yesterday = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
todayAfter = date.today().strftime("%Y-%m-%d")
yesterdayAfter = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
nowtime = datetime.now()

def sanitize_filename(file_name: str) -> str:
    """Strip emoji and special chars, replace spaces/brackets with underscores."""
    # Normalize unicode (handles Thai and other multi-byte chars)
    normalized = unicodedata.normalize('NFKD', file_name)
    
    # Remove emoji and non-ASCII characters
    ascii_only = normalized.encode('ascii', 'ignore').decode('ascii')
    
    # Replace problematic shell characters with underscores
    sanitized = re.sub(r'[^\w\s\-.]', '_', ascii_only)
    
    # Collapse multiple underscores/spaces into one
    sanitized = re.sub(r'[\s_]+', '_', sanitized).strip('_')
    
    # Keep the .mp4 extension clean
    return sanitized if sanitized.endswith('.mp4') else sanitized + '.mp4'



def ffmpeg_trim(file_name: str, start_time: str, end_time: str, mute: bool, scene, tries:int = 0, max_retries: int = 3 ) -> str:
    
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

    if best_match:
        
        original_path = Path(video_dir / best_match).resolve()
        output_path = str((clip_dir / f"scene_{scene}.mp4").resolve())
        
        print(f"original path: {original_path}")
        print(f"original path: {output_path}")

        if mute:
            strategy = ['ffmpeg', "-y",
                        "-ss", start_time, 
                        "-to", end_time,
                        "-i",  original_path,
                        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                        "-an",
                        output_path
                        ]
        else:
            strategy = ['ffmpeg', "-y",
                        "-ss", start_time, 
                        "-to", end_time,
                        "-i",  original_path,
                        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                        "-c:a", "aac", "-b:a", "128k",
                        output_path
                        ]

        try:
            result = subprocess.run(
                strategy,
                capture_output=True, text=True)
            print(result.stdout)
            print(result.stderr)
            print(f"{scene} trimmed success ✅")
        except Exception as e:
            print(f"error: {e}")
            if tries <= max_retries:
                ffmpeg_trim(file_name, start_time, end_time, mute, scene, tries + 1)
            else:
                print(f"giving up on {(scene)} ❌")
    else: 
        with open(script_dir / "video_script.json", "r+") as file:
            data = json.load(file)  
            data[int(scene)-1]['video'] = "x"
            file.seek(0)  
            file.truncate()  
            json.dump(data, file, indent=4)
    


def trim_videos():
    with open(script_dir / "video_script.json", "r") as file:
        data = json.load(file)  
    
    failed_scenes = []
    
    for scene in data:
        if scene['video'] != "x":
            try:
                ffmpeg_trim(scene['video'], scene['start_time'], scene['end_time'], scene['mute'], scene['scene'])
            except RuntimeError as e:
                print(f"🚨 Giving up on scene_{scene['scene']}: {e}")
                failed_scenes.append(scene['scene'])
                return trim_videos()
    
    if failed_scenes:
        print(f"Trim phase complete but {len(failed_scenes)} scene(s) failed: {failed_scenes}")
        return trim_videos()

    
    print("🎉 All scenes trimmed successfully!")


def loop_video_to_duration(video: VideoFileClip, target_duration: float) -> VideoFileClip:
    """Loop a video clip until it reaches at least target_duration, then trim."""
    return loop(video, duration=target_duration).set_duration(target_duration)


def make_subtitle_clips(text: str, video_w: int, video_h: int, total_duration: float, font_path) -> list:
    """Split text into 4 chunks and return timed TextClips alternating colors."""
    COLORS = ['white', 'yellow', '#00cfff', '#ff6b6b']  # alter these to your taste

    words = text.split()
    if not words:
        return []

    # Split words as evenly as possible into 4 parts
    n = len(words)
    chunk_size = max(1, n // 4)
    chunks = []
    for i in range(4):
        start = i * chunk_size
        # Last chunk gets any remainder
        end = start + chunk_size if i < 3 else n
        chunk = ' '.join(words[start:end])
        if chunk:
            chunks.append(chunk)

    chunk_duration = total_duration / len(chunks)
    subtitle_clips = []

    for i, chunk in enumerate(chunks):
        color = COLORS[i % len(COLORS)]
        start_t = i * chunk_duration

        txt = TextClip(
            chunk,
            fontsize=40,
            color=color,
            font=str(font_path),
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(video_w - 100, None)
        )
        txt = (txt
               .set_position(('center', video_h - 150))
               .set_start(start_t)
               .set_duration(chunk_duration))
        subtitle_clips.append(txt)

    return subtitle_clips

def validate_and_repair_scenes():
    """Check all scene clips are valid before add_voiceover runs. Re-trim any that are corrupt."""
    with open(script_dir / "video_script.json", "r") as file:
        data = json.load(file)
    
    corrupt = []
    
    for scene in data:
        if scene['video'] == "x":
            continue
        
        clip_path = clip_dir / f"scene_{scene['scene']}.mp4"
        
        # Check 1: file exists and is large enough
        if not clip_path.exists() or clip_path.stat().st_size < 10_000:
            print(f"⚠️ scene_{scene['scene']} missing or too small — re-trimming...")
            corrupt.append(scene)
            continue
        
        # Check 2: actually openable by MoviePy
        try:
            test = VideoFileClip(str(clip_path.resolve()))
            _ = test.get_frame(0)  # force it to actually read a frame
            test.close()
            print(f"✅ scene_{scene['scene']} OK")
        except Exception as e:
            if test is not None:
                test.close()
            print(f"⚠️ scene_{scene['scene']} corrupt ({e}) — re-trimming...")
            with open(script_dir / "video_script.json", "r") as file:
                    data = json.load(file)
            modified = data[int(scene['scene']) - 1]['video'] = 'x'
            with open(script_dir / "video_script.json", "w") as file:
                json.dump(data, file, indent=4)
            corrupt.append(scene)
        finally:
            if test is not None:
                test.close()
    
    # Re-trim anything that failed validation
    if corrupt:
        print(f"\n🔧 Re-trimming {len(corrupt)} corrupt scene(s)...")
        still_failed = []
        for scene in corrupt:
            try:
                ffmpeg_trim(scene['video'], scene['start_time'], scene['end_time'], scene['mute'], scene['scene'])
                print(f"✅ scene_{scene['scene']} re-trimmed successfully")
            except Exception as e:
                modified = data[int(scene['scene']) - 1]['video'] = 'x'
                with open(script_dir / "video_script.json", "w") as file:
                    json.dump(data, file, indent=4)
                print(f"🚨 scene_{scene['scene']} could not be repaired: {e}")
                still_failed.append(scene['scene'])
        
        if still_failed:
            raise RuntimeError(f"❌ Could not repair scenes: {still_failed}. Check source videos.")
    else:
        print("\n✅ All scene clips validated successfully")


def add_voiceover():
    validate_and_repair_scenes()
    
    with open(script_dir / "video_script.json", "r") as file:
        data = json.load(file)

    font_path = cwd / "Mochi.ttf"
    TARGET_W = 1280
    TARGET_H = 720

    for scene in data:
        if scene['video'] == "x":
            continue
        if not (scene['mute'] or scene['script'] != 'x'):
            continue

        video_path = Path(clip_dir / f"scene_{scene['scene']}.mp4")
        temp_output_path = Path(clip_dir / f"scene_{scene['scene']}_voiceover_temp.mp4")
        audio_path = str(audio_dir / f"scene_{scene['scene']}_audio.wav")

        if os.path.getsize(audio_path) < 100:
            print(f"Warning: {audio_path} seems to be empty or corrupted!")
            continue

        subtitle_clips = []
        video = None
        audio = None
        base_video = None
        final_video = None

        try:
            video = VideoFileClip(str(video_path)).resize(newsize=(TARGET_W, TARGET_H))
            audio = AudioFileClip(audio_path)
            target_duration = audio.duration
            render_fps = video.fps if video.fps is not None else 30

            if audio.duration > video.duration:
                base_video = loop_video_to_duration(video, target_duration)
            else:
                base_video = video.set_duration(target_duration)

            caption_text = scene.get('script', '')

            if caption_text and caption_text != 'x':
                subtitle_clips = make_subtitle_clips(
                    caption_text,
                    TARGET_W,
                    TARGET_H,
                    target_duration,
                    font_path.resolve()
                )
                final_video = CompositeVideoClip([base_video] + subtitle_clips, size=(TARGET_W, TARGET_H))
            else:
                final_video = base_video

            final_video = final_video.set_audio(audio)

            # Write to a TEMP file — never touch the original until fully done
            final_video.write_videofile(
                str(temp_output_path),
                fps=render_fps,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(clip_dir / f"temp_{scene['scene']}.m4a"),
                remove_temp=True
            )

            # Only replace the original once the write fully succeeded
            temp_output_path.replace(video_path)
            print(f"✅ scene_{scene['scene']} voiceover complete")

        except Exception as e:
            print(f"🚨 scene_{scene['scene']} failed: {e}")
            # Clean up the failed temp file if it exists
            if temp_output_path.exists():
                temp_output_path.unlink()
            # Original video_path is still intact — skip and continue
            continue

        finally:
            for sub in subtitle_clips:
                try: sub.close()
                except: pass
            for clip in [final_video, base_video, video, audio]:
                try: clip.close()
                except: pass

def download_safe_stock_image(search_term: str, sceneNumber:str, topic):
    number_of_imgs = 3
    url = f"https://api.pexels.com/v1/search?query={search_term}&per_page={number_of_imgs}"
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        print(response)
        if response.status_code != 200:
            print(f"❌ Pexels API Error: {response.status_code}")
            return download_safe_stock_image(topic, sceneNumber, topic)
            
        data = response.json()
        if not data.get("photos"):
            print(f"⚠️ No images found on Pexels for: '{search_term}'")
            return False  # Let your retry logic handle this
        # Get the URL for the large image size
        number = 0
        used = []
        def get_num(used):
            if len(used) == number_of_imgs :
                used = []
            number = random.randint(0, number_of_imgs -1)
            if number in used:
                return get_num()
            used.append(number)
            return number, used
        #useless until api starts giving me more results 
        if topic == search_term:
            number, used = get_num(used)
        print(number)
        image_url = data["photos"][number]["src"]["large"]
        
        # Download the file cleanly
        img_data = requests.get(image_url).content
        target_file =  image_dir / f"scene_{sceneNumber}.jpg"
        
        with open(target_file, "wb") as handler:
            handler.write(img_data)
            
        print(f"✅ Clean stock image saved for scene_{sceneNumber}")
        return True

    except Exception as e:
        print(f"❌ Error downloading from Pexels: {e}")
        return False 

def generate_search(topic, scene):
        imagesearch = gemma(f"Im making a daily news video on {topic} i need a pexels image to go with the part of my script that says ###{scene['script']} ### output the search term only for theis sction, output no more than 5 words for a pexels stock image search ")
        if "Gemini SDK Error" in imagesearch or "Sorry, I'm having trouble thinking right now. Please try again later." in imagesearch:
            time.sleep(20)
            return generate_search()
        else: 
            return imagesearch

def image_collector(topic):
    with open(script_dir / "video_script.json", "r") as file:
        data = json.load(file)
    for scene in data:
        if scene['video'] == "x":
            print(f"getting image for {scene['scene']}")
            imagesearch = generate_search(topic, scene)
            print(imagesearch)
            download_safe_stock_image(imagesearch , scene['scene'], topic )
            time.sleep(60)

def create_image_videos():
    with open(script_dir / "video_script.json", "r") as file:
        data = json.load(file)

    for scene in data:
        if scene['video'] != "x":
            continue

        video_path = (clip_dir / f"scene_{scene['scene']}.mp4").resolve()
        image_path = (image_dir / f"scene_{scene['scene']}.jpg").resolve()
        audio_path = (audio_dir / f"scene_{scene['scene']}_audio.wav").resolve()

        TARGET_W = 1280
        TARGET_H = 720

        if not audio_path.exists():
            print(f"❌ Missing Audio File! Checked: {audio_path}")
            continue

        if not image_path.exists():
            print(f"❌ Missing Image File! Checked: {image_path}")
            continue

        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        image = ImageClip(str(image_path)).resize(height=TARGET_H)
        extra_width = image.w - TARGET_W

        if extra_width > 0:
            # KEY FIX: Use fl_image instead of set_position with a lambda.
            # fl_image applies a function per-frame that receives (t, frame) and
            # returns the frame — but we only need the crop offset, so we derive
            # it via make_frame instead.
            #
            # Simpler approach: use fl() to crop at each frame's timestamp.
            def make_panned_clip(img_clip, extra_w, dur):
                def pan_filter(get_frame, t):
                    frame = get_frame(t)
                    offset = int(extra_w * (t / dur))
                    return frame[:, offset:offset + TARGET_W]
                return img_clip.fl(pan_filter, apply_to=['mask'])

            panned = make_panned_clip(image, extra_width, duration)
            panned = panned.set_duration(duration)
        else:
            panned = image.resize(newsize=(TARGET_W, TARGET_H)).set_duration(duration)

        # Now composite subtitles on top of the panned clip (which has correct size)
        panned = panned.set_audio(audio)

        caption_text = scene.get('script', '')
        font_path = cwd / "Mochi.ttf"
        subtitle_clips = []

        if caption_text and caption_text != 'x':
            subtitle_clips = make_subtitle_clips(
                caption_text,
                TARGET_W,
                TARGET_H,
                duration,
                font_path.resolve()
            )

        final_video = CompositeVideoClip([panned] + subtitle_clips, size=(TARGET_W, TARGET_H))

        temp_audio_path = clip_dir / f"temp_{scene['scene']}.m4a"
        final_video.write_videofile(
            str(video_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(temp_audio_path.resolve()),
            remove_temp=True
        )

        final_video.close()
        image.close()
        audio.close()

def final_video_creation(topic): 
    print("creating video")

    filename = f"{topic}_news_{today}"
    with open(script_dir / "video_script.json", "r") as file:
        data = json.load(file)
    
    print("\n\n\n save script ✅")
    scenes = []
    output_file_path = upload_dir / f"{filename}.mp4"

    
    try:
        # 1. Load all individual scene clips safely
        for scene in data:
            video_path = str((clip_dir / f"scene_{scene['scene']}.mp4").resolve())
            video = VideoFileClip(video_path)
            scenes.append(video)
        print("\n\n\n compile videos from script ✅ ")
            
        # 2. Stitch the videos together
        final_clip = concatenate_videoclips(scenes, method="compose")
        print("\n\n\n concat videos ✅")

        # 3. Load and set up background music
        audio_path = str((cwd / "background.mp3").resolve())
        bg_audio = AudioFileClip(audio_path).set_duration(final_clip.duration).volumex(0.15)
        print("\n\n\n audio ✅")
        # 4. SAFE AUDIO CHECK: Handle scenes that might be totally silent
        audio_layers = [bg_audio]
        if final_clip.audio is not None:
            audio_layers.append(final_clip.audio)
        print("\n\n\n handle silent ✅")
        final_audio = CompositeAudioClip(audio_layers)
        final_clip.audio = final_audio
        print("\n\n\n final audio ✅")
        
        # 6. Render the final output
        final_clip.write_videofile(
            str(output_file_path.resolve()),
            fps=30,
            codec="libx264",
            audio_codec="aac"
        )
        print("\n\n\n write video ✅")
        # Close the master composition layout
        final_clip.close()
        bg_audio.close()
        print("\n\n\n close audio ✅")
        #move the script file
        script_path = cwd / "script/video_script.json"
        script_path.rename(upload_dir / f"{topic}_script_{today}.json")
        print("🎉 Full compilation successful!")
        print("\n\n\n move script ✅")

    except Exception as e:
        videolengths = ""
        for video in video_dir.iterdir():
            if video.suffix == ".mp4":
                try:
                    with VideoFileClip(str(video.resolve())) as v_clip:
                        videolengths += f"\n video: {video.name}, duration: {v_clip.duration}"
                except Exception:
                    videolengths += f"\n video: {video.name}, duration: unknown/unreadable"
        with open(upload_dir / f"{nowtime}_final_video_error.txt", "w") as File:
            File.write(f"error: {e} \n\n video lengths {videolengths} \n \n script: {data} ")
        print(f"❌ error in final_video: {e} ❌")
        return False
    finally:
        # 7. CRUCIAL RESOURCE CLEANUP: 
        # The finally block runs even if the render crashes, forcing your Mac 
        # to unlock all the original scene video files.
        print("Cleaning up scene clips from memory...")
        for video in scenes:
            try:
               video.close() 
            except:
                pass
            
    return str(output_file_path.resolve())

