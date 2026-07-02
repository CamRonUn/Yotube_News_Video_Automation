from info_scraping.news_outlets import getNews 
from info_scraping.youtube import getVideos
from script_generate import get_idea, generate_script
from file_functions import delete_all_files, script_to_json
from video_editing import trim_videos, add_voiceover, image_collector, create_image_videos, final_video_creation
from pathlib import Path
from moviepy.editor import VideoFileClip
from textToSpeech import generate_video_audio
from youtube_upload import authenticate_youtube, video_upload, generate_meta, upload_thumbnail, publish_video
from api_configs.gemini_config import grok, generate_chat_response
from functiions.ai import clips
from datetime import date, datetime
import json
import time
import re

#important paths 
cwd = Path(".")
news_dir = cwd / "news"
script_dir = cwd / "script"
videos_dir = cwd / "videos"
audio_dir = cwd / "audio_files"
images_dir = cwd / "generated_images"
clips_dir = cwd / "video_clips"
upload_dir = cwd / "ready_to_upload"
today = date.today().strftime("%Y%m%d")
timenow = datetime.now()


def make_both():
    topic1 = "Triathlon"
    topic2= "swimming"
    topicx="running"
    topic3 = "Cycling"
    topic4 = "Coding and AI"
    topic5 = "Chineese Technology"
    topic6= "Travel Deals"
    #login to youtube 
    print("starting make_both")
    print(topic1)
    youtube1 = authenticate_youtube()
    
    print(topic2)
    youtube2 = authenticate_youtube()

    print(topicx)
    youtubex= authenticate_youtube()

    print(topic3)
    youtube3 = authenticate_youtube()

    print(topic4)
    youtube4 = authenticate_youtube()

    print(topic5)
    youtube5 = authenticate_youtube()

    print(topic6)
    youtube6 = authenticate_youtube()
    ###main script to generate video 

    def makeShorts(youtube, topic):
        for file in videos_dir.iterdir():
                    if ".mp4" in file.name:
                        video_path = file.resolve()
                        duration = VideoFileClip(str(video_path)).duration
                        if duration > (60*30):
                            clips(file.name[:-4], youtube, topic)

    def make_1(youtube,topic, attempts = 0):
        def main2():
            try:
                #delete existing files from prev video
                delete_all_files(news_dir.resolve())
                delete_all_files(script_dir.resolve())
                delete_all_files(videos_dir.resolve())
                delete_all_files(audio_dir.resolve())
                delete_all_files(images_dir.resolve())
                delete_all_files(clips_dir.resolve())
                print("all old files deleted")


                #scrape youtube and news 
                getNews(topic)
                getVideos(topic, "10")

                def downloaded(attemptsdown = 0):
                    try:
                        #generate script
                        idea = get_idea(topic)
                        generate_script(topic, idea)

                        #convert script to json
                        script_to_json()

                        #create voice overs
                        generate_video_audio()

                        #video editing 
                        trim_videos()
                        add_voiceover() #adds voice over and subtitles to trimmed clips 
                        image_collector(topic) #get photos for scenes without video 
                        create_image_videos() #turns those photos into videos 
                        video_path = final_video_creation(topic)
                        return video_path
                    except Exception as e:
                        attemptsdown += 1
                        print(f"\n\n\n\n attempt attempt {attemptsdown}/3 \n error: {e} \n\n\n")
                        with open(upload_dir / f"{timenow}_error_download.txt", "w") as File:
                            File.write(f"error {e}")
                        if attemptsdown <= 3:
                            return downloaded(attemptsdown + 1)
                        else:
                            print("downloaded function failed ❌ 3 times")
                            return False

                video_path = downloaded()
                return video_path
            except Exception as e: 
                with open(upload_dir / f"{timenow}_error_main2.txt", "w") as File:
                    File.write(f"error {e}")
                return False
        video_path = main2()
        if video_path:
            meta = generate_meta(topic)
            title = meta['title']
            description = meta['description']
            tags = meta['tags']
            thumbnail_prompt = meta['thumbnail_prompt']
            video_id = video_upload(video_path, youtube, title, description, tags, topic)
            thumbnail_path = grok(topic, today, thumbnail_prompt)
            upload_thumbnail(youtube, video_id, thumbnail_path)
            publish_video(youtube, video_id)
        else:
            if attempts <= 3:
                return make_1(youtube, topic, attempts + 1)
            else:
                print("giving up")
                return False
    
    make_1(youtube1, topic1)
    makeShorts(youtube1, topic1)
    make_1(youtube2, topic2)
    makeShorts(youtube2, topic2)
    make_1(youtubex, topicx)
    makeShorts(youtubex, topicx)
    make_1(youtube3, topic3)
    makeShorts(youtube3, topic3)
    make_1(youtube4, topic4)
    makeShorts(youtube4, topic4)
    make_1(youtube5, topic5)
    makeShorts(youtube5, topic5)
    make_1(youtube6, topic6)
    makeShorts(youtube6, topic6)
    


make_both()