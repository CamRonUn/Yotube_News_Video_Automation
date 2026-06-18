from info_scraping.news_outlets import getNews 
from info_scraping.youtube import getVideos
from script_generate import get_idea, generate_script
from file_functions import delete_all_files, script_to_json
from video_editing import trim_videos, add_voiceover, image_collector, create_image_videos, final_video_creation
from pathlib import Path
from textToSpeech import generate_video_audio
from youtube_upload import authenticate_youtube, video_upload, generate_meta, upload_thumbnail, publish_video
from api_configs.gemini_config import grok, generate_chat_response
from datetime import date
import json
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


def make_both():
    topic1 = "triathlon"
    topic2= "cycling"
    #login to youtube 
    print("starting make_both")
    youtube1 = authenticate_youtube()
    youtube2 = authenticate_youtube()
    ###main script to generate video 
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
                def downloaded(attempts = 0):
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
                    except:
                        attempt += 1
                        if attempt < 3:
                            return downloaded(attempts + 1)
                        else:
                            print("downloaded function failed ❌ 3 times")
                            return False

                video_path = downloaded()
                return video_path
            except: 
                return False
        video_path = main2()
        if video_path:
            meta = generate_meta(topic)
            title = meta['title']
            description = meta['description']
            tags = meta['tags']
            thumbnail_prompt = meta['thumbnail_prompt']
            video_id = video_upload(video_path, youtube, title, description, tags)
            thumbnail_path = grok(topic, today, thumbnail_prompt)
            upload_thumbnail(youtube, video_id, thumbnail_path)
            publish_video(youtube, video_id)
        else:
            if attempts <= 3:
                return make_1(youtube1 if topic == topic1 else youtube2, topic1 if topic == topic1 else topic2, attempts + 1)
            else:
                print("giving up")
                return False
    
    make_1(youtube1, topic1)
    make_1(youtube2, topic2)


def test():
    topic = "triathlon"
    idea = """
            What’s up, tri-fam! Welcome back to your daily dose of swim-bike-run chaos. Whether you’re scrubbing your wetsuit after an E. coli scare or tapering for your next big race, we’ve got the pulse of the sport right here. Let’s dive into today’s headlines!

            &&&

            **The Speed Demons: Alex Yee and Cassandre Beaugrand Take on the Track!**
            Are they the best runners in the game? The debate is heating up. Both Olympic gold medalists are shifting gears from the transition zone to the Diamond League in Monaco on July 10th. Beaugrand is coming off a scorching 14:40 5k, while Yee is looking to prove he’s the fastest triathlete to ever hit a 5k track. We’re watching to see if they can hang with the pure-track specialists—or if they’re just prepping to dominate the triathlon world with even more lethal run splits. 
            ||HIGHLIGHTS： MEN'S 2026 HUATULCO WORLD CUP [WFnvM-GQ5yI].mp4||

            &&&

            **Huatulco Highs: The Latest World Cup Action**
            The racing in Huatulco was absolute fire. If you missed the Men's World Cup, you missed a masterclass in tactical racing. We’re breaking down the moves that made the difference and looking at who’s peaking as we head deeper into the 2026 season. The intensity is ramping up, and the gap between the contenders and the rest of the pack is shrinking.
            ||HIGHLIGHTS： MEN'S 2026 HUATULCO WORLD CUP [WFnvM-GQ5yI].mp4||

            &&&

            **The "Is Triathlon Dying?" Crisis**
            The crew over at GTN is asking the big questions today: Is the sport losing its best athletes to other disciplines? With superstars flirting with pure running and the constant grind of the WTCS circuit, the landscape is changing. Are we seeing a shift in how pros view their careers? We’re diving into the debate on whether the triathlon "path" is still the golden ticket.
            ||Is Triathlon Losing Its Best Athletes？ ｜ GTN Show #456 [8-B6k1L3DwI].mp4||

            &&&

            **The E. Coli Blues: Pigman Triathlon’s Swim Cancelled**
            Not everything goes to plan. The Pigman Triathlon in Iowa had to cut the swim portion after heavy rains sent E. coli levels through the roof. It’s a heartbreaking reality for those who spent months in the pool, but the silver lining? The race went on as a duathlon, proving once again that triathletes are the most adaptable athletes on the planet. Just another reminder to check your water reports before race day!
            ||Is Triathlon Losing Its Best Athletes？ ｜ GTN Show #456 [8-B6k1L3DwI].mp4||

            &&&

            **Future Stars: Avalyn Thompson’s Road to Dakar**
            Huge props to Avalyn Thompson! She’s been selected to represent Team USA at the 2026 Youth Olympic Games in Senegal. She’s a product of the USA Triathlon development pipeline and a Gwen Jorgensen Scholarship recipient. Keep an eye on her—she’s the future of the sport and heading to the world stage as the sole U.S. representative. 
            ||HIGHLIGHTS： MEN'S 2026 HUATULCO WORLD CUP [WFnvM-GQ5yI].mp4||

            &&&

            **Gear Check: Zone3’s New Tech**
            If you’re looking to shave some time off your next race, Zone3 just dropped some serious heat. From the Ascend sleeveless wetsuit to the new "Aerostripe" trisuit, it looks like they’re trying to make sure we all look—and go—faster this season. Whether you’re an amateur or a pro, gear updates are always the best way to get that pre-race hype.
            ||Is Triathlon Losing Its Best Athletes？ ｜ GTN Show #456 [8-B6k1L3DwI].mp4||

            &&&

            **Weekend Vibes: Jordanelle Returns**
            To wrap it up, the Jordanelle Triathlon is back this Saturday in Utah! With 700 athletes signed up, it’s going to be a massive day. It’s a perfect reminder of why we do this: the scenery, the community, and that feeling of crossing the line. Good luck to everyone racing, and remember—don’t forget your transition bag!
            ||HIGHLIGHTS： MEN'S 2026 HUATULCO WORLD CUP [WFnvM-GQ5yI].mp4||"
            """
    script = generate_script(topic, idea)
    print(f"----------------- script before json --------------- \n \n\n\n {script}")
    print("generating json")
    script_to_json()

make_both()