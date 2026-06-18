from api_configs.gemini_config import generate_chat_response
from pathlib import Path
import json
import time
import re


#directories 
cwd = Path(".")
news = cwd / "news" / "TodaysNews.txt"
videos = cwd / "videos"
script = cwd / "script"

#get news file 
def get_news():
    with open(news, "r", encoding="utf-8") as file:
        google_news = file.read()
    return google_news

#Get Video Titles 
def get_titles():
    titles = ""
    for file in videos.iterdir():
        if file.is_file() and file.suffix.lower() == '.mp4': 
            titles += f"{file.name} \n" 
    return titles


def read_vtt_structured(file_path: str | Path) -> list[dict]:
    """
    Manually parses the VTT file into a structured list of dictionaries
    containing start time, end time, and text.
    """
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split cues using double newlines
    blocks = content.strip().split("\n\n")
    structured_cues = []

    timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})')

    for block in blocks:
        lines = block.strip().split("\n")
        start_time, end_time, text_lines = None, None, []

        for line in lines:
            match = timestamp_pattern.search(line)
            if match:
                start_time = match.group(1)
                end_time = match.group(2)
            elif line != "WEBVTT" and not line.startswith("Kind:") and not line.startswith("Language:") and not line.isdigit():
                cleaned = re.sub(r'<[^>]+>', '', line).strip()
                if cleaned:
                    text_lines.append(cleaned)

        if start_time and end_time and text_lines:
            structured_cues.append({
                "start": start_time,
                "end": end_time,
                "text": " ".join(text_lines)
            })

    return structured_cues

#get transcripts
def transcripts(titles):
    videotranscripts = []
    for file in videos.iterdir():
        if file.is_file() and file.suffix.lower() =='.vtt' and file.name[:-15] in titles:
            string = ""
            string += f"\n \n video title: {file.name} subtitles \n"
            string += str(read_vtt_structured(file.resolve()))
            videotranscripts.append(string)
    return videotranscripts

def get_idea(topic) -> str:
    #Generates 3 ideas for the video story based on the news and votes for the best one 

    google_news = get_news()
    titles = get_titles()

    #idea generation
    yotube_expert_prompt = f"you are a youtube clickbait and story telling expert that loves {topic} meme your goal is to create a brief outline for a {topic} entertaining news video you thin will do well, develop a story that people would like to watch based on the top articles on google news under {topic} today {google_news} and the top videos on youtube today about {topic} are {titles} feel free to exclude anything that doesnt sound relivint/ exiting/ entertaining or interstingnote but we want to include most of the top youtube videos posted today video is made by ai clipping up clips from videos so focus on the storyline as visuals will be basic we also do not have acess to any other videos, clips or music outside of the videos metioned. split the video plan into parts for each topic video needs to have at least 5-7 topics deo seperated by &&& example scene 1 talk about this topic scene 2 talk about this topic .... &&& scene x scene x+1...  talk about this topic and at the end of the sections include the videos you are going to use in double || example ||videotitle1.mp4, videotitle2.mp4,...|| so section 1 includes different videos to section. try focus on talking about youtube videos only include the most interesting or entertaining article unless they are really important then absolute max include 2, feel free to talk about vlogs thats intersting news too what the top youtubers / pros are doing. try make a plan that will flow well and make sence for a whole video. focus on any pro news pro races first then go into influencer news. if video is about triathlon you must have at least 1 section for any proffesional ironman or t100 race / livestream you recieve. make sure the plan is focused on being a daily news video"
    topic_and_meme_enthuisest_prompt = f"you are a {topic} enthuisest that loves everything about {topic} and loves {topic} memes and news this is the latest google news on {topic} {google_news} and here are the top {topic} videos posted today on youtube {titles} make a quick summary of an entertaing {topic} news video stringing these togethor in an imformative way that would be interestign and enterating to a {topic} fan. note video is made by ai clipping up clips from videos so focus on the storyline as visuals will be basic we also do not have acess to any other videos, clips or music outside of the videos metioned split the video plan into parts for each topic video needs to have at least 5-7 topics seperated by &&& example scene 1 talk about this topic scene 2 talk about this topic .... &&& scene x scene x+1...  talk about this topic and at the end of the sections include the videos you are going to use in double || example ||videotitle1.mp4, videotitle2.mp4,...|| so section 1 includes different videos to section try focus on talking about youtube videos only include the most interesting or entertaining article unless they are really important then absolute max include 2, feel free to talk about vlogs thats intersting news too what the top youtubers / pros are doing  try make a plan that will flow well and make sence for a whole video focus on any pro news pro races first then go into influencer news focus on any pro news pro races first then go into influencer news.if video is about triathlon you must have at least 1 section for any proffesional ironman or t100 race / livestream you recieve.  make sure the plan is focused on being a daily news video"
    triathon_nerd_prompt = f"you are a {topic} nerd, and want to make a entertaining news recap on todays {topic} news, this is the top news from google news on {topic} {google_news} and the top youtube videos posted today on {topic} {titles} how would you structure a entertaing {topic} news video give a brief plan.  note video is made by ai clipping up clips from videos so focus on the storyline as visuals will be basic we also do not have acess to any other videos, clips or music outside of the videos metionedat. split the video plan into parts for each topic video needs to have at least 5 topics by &&& example scene 1 talk about this topic scene 2 talk about this topic .... &&& scene x scene x+1...  talk about this topic and at the end of the sections include the videos you are going to use in double || example ||videotitle1.mp4, videotitle2.mp4,...|| so section 1 includes different videos to section try focus on talking about youtube videos only include the most interesting or entertaining article unless they are really important then absolute max include 2, feel free to talk about vlogs thats intersting news too what the top youtubers / pros are doing try make a plan that will flow well and make sence for a whole video. focus on any pro news pro races first then go into influencer news focus on any pro news pro races first then go into influencer news. if video is about triathlon you must have at least 1 section for any proffesional ironman or t100 race / livestream you recieve. make sure the plan is focused on being a daily news video"
    
    yotube_expert_result = generate_chat_response(yotube_expert_prompt)
    time.sleep(60)
    if "Gemini SDK Error" in yotube_expert_result or "Sorry, I'm having trouble thinking right now. Please try again later." in yotube_expert_result:
        time.sleep(120)
        return get_idea(topic)
    print(yotube_expert_result)

    topic_and_meme_enthuisest_result = generate_chat_response(topic_and_meme_enthuisest_prompt)
    time.sleep(60)
    print(topic_and_meme_enthuisest_result)
    if "Gemini SDK Error" in topic_and_meme_enthuisest_result or "Sorry, I'm having trouble thinking right now. Please try again later." in topic_and_meme_enthuisest_result:
        time.sleep(120)
        return get_idea(topic)

    triathon_nerd_result = generate_chat_response(triathon_nerd_prompt)
    time.sleep(60)
    print(triathon_nerd_result)
    if "Gemini SDK Error" in triathon_nerd_result or "Sorry, I'm having trouble thinking right now. Please try again later." in triathon_nerd_result:
        time.sleep(120)
        return get_idea(topic)

    #ai idea voting
    output_format = """{"option1": 0, "option2": 0, "option3": 0}"""
    voteprompt_yotube_focus = f"""Must return a json object {output_format} no text before or after and put your votes in the 0 spot, you are a audience of 50 youtube {topic} experts and you are pitched 3 ideas for todays news video vote on which video will do the best option 1 {yotube_expert_result}, {topic_and_meme_enthuisest_result}, {triathon_nerd_result} """
    voteprompt_fan_focus = f"""Must return a json object {output_format} no text before or after and put your votes in the 0 spot, you are a audience of 50 {topic} fans and you are pitched 3 ideas for todays news video vote on which video will be the most enjoyable option 1 {yotube_expert_result}, {topic_and_meme_enthuisest_result}, {triathon_nerd_result} """
    vote_youtube_focus = generate_chat_response(voteprompt_yotube_focus)
    print(vote_youtube_focus)
    if "Gemini SDK Error" in vote_youtube_focus or "Sorry, I'm having trouble thinking right now. Please try again later." in vote_youtube_focus:
        time.sleep(120)
        vote_youtube_focus = {"option1": 0, "option2": 0, "option3": 0}
    time.sleep(90)

    vote_fan_focus = generate_chat_response(voteprompt_fan_focus)
    print(vote_fan_focus)
    if "Gemini SDK Error" in vote_fan_focus or "Sorry, I'm having trouble thinking right now. Please try again later." in vote_fan_focus:
        time.sleep(120)
        vote_fan_focus = {"option1": 0, "option2": 0, "option3": 0}
    time.sleep(60)

    #converting ai votes into my data and pick best idea 
    option1 = 0
    option2 = 0
    option3 = 0
    vote1 = json.loads(vote_youtube_focus)
    vote2 = json.loads(vote_fan_focus)
    option1 += vote1["option1"] + vote2["option1"]
    option2 += vote1["option2"] + vote2["option2"]
    option3 += vote1["option3"] + vote2["option3"]
    print([option1,option2,option3])
    if option1 >= option2 and option1 >= option3:
        return yotube_expert_result
    elif option2 >= option3:
        return topic_and_meme_enthuisest_result
    else:
        return triathon_nerd_result
    
def generate_script(topic:str, idea:str)-> str:

    google_news = get_news()
    titles = get_titles()

    #split idea by &&& into parts 
    idea = idea.replace(" && "," &&& ").replace(" & "," &&& ")
    parts = idea.split("&&&")
    if len(parts) < 2:
        generate_script(topic, get_idea(topic))
    print(parts)
    #generate script
    full_plan = ""
    for part in parts:

        titles = part.split("||")
        if len(titles) > 0:
            titles = titles[0]
        else:
            titles = ""

        #get comments 
        comments = []
        for file in videos.iterdir():
            if file.is_file() and file.suffix.lower() =='.json' and file.name[:-15] in titles:
                comment_str = ""
                comment_str += f"\n {file.name[:-10]} comments:"
                with open(file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    comment_list = data.get("comments", [])
                    for comment_item in comment_list:
                        text = comment_item.get("text", "")
                        author = comment_item.get("author", "Anonymous")
                        likes = comment_item.get("like_count", 0)
                        comment_str += f"\n comment: {text}, author: {author}, likes: {likes}"
                comments.append(comment_str)

        videotranscripts = transcripts(titles)

        def gen_part(part_, current_accumulated_plan):
            #print(f" ----- part: {part_} \n \n \n")
            json_style_guide = """[{"scene": 1, "script": what the ai voice is going to say on this scene,"mute": bool if they AI Voice is talking make true if your trying to show a clip mark false so the clip audio can play, "video": this is the video that will trimmed to be shown, "start_time": format HH:MM:SS you need pick a time stamp in the video based on the subtitles where you think there will be a interesting visual this will be used to trim the original video,"end_time": format HH:MM:SS where the video trim will be cut off}{same for next scene}...{last scene}] do not include anything other than this no words or spaces"""
            prompt = f"""You are a yotube and ### {topic} ### expert you are making a daily news video we have drafted a ruff script as an organisation: full video script ### {idea} ### you are not generating the whole script.
            your free to change things legistacly but your now part of the ai process to create the videos.
            also if any comments are interesting from the comment section of the videos we are talking about include them only if they are really funny or add to the video.
            i need you to return a json file that looks like exactly like this ### {json_style_guide} ###
                these are the news articles from today that you can talk about ### {google_news} ###.
                these are the full tanscripts of the most popular videos from today ### {videotranscripts} ### and comments ### {comments} ###
                if you do not have related video to show for what you are talking about mark "video", "start_time" and "end_time" as x only do this if you dont have a video related to what your talking about use the tanscript to guid the timestamp. 
                "video"should be the filename from the transcript but replace .en.vtt with .mp4 


                this is the part i need you to generate this request: ### {part_} ### this time unless this is the final part of the whole script do not finish the video - finishing the vidio includes asking for final engagement as like or subsribes / comments

                the video title im sending from the tanscript of is found in the part between the || ... || use it the largge majority of scenes should have video and time frames just gues the time stamps in video that would be good to show. and try make time of clip the same as a estimation of the voice over

                if you are trying to show audio from a video clip mark script as x and mute: false else have script: what ai voice is saying, mute: true if some one says something interesting in there video or there is a good commentation clip that fits into the video well include it by marking script x and including the video and start_time and end_time of the clip
                make sure each video clip that mute: true is at least 15 seconds length if mute:false can be under 15 seconds no more than 15 seconds 
                
                try actually explain topics not just mention them you can go in a lot more detail than the plan    
                make it atleast 12-20 scenes mention comments, include clips of people talking if it stengthens a point (find in transcript and put the start_end time so clip can be cut in there).

                make sure the video is focused on being a daily news video.
                
                this is the full script so far before your part ### {current_accumulated_plan} ### try make the whole script flow well and make sense. do not repeat yourself and focus on the part of the full script ive given you. 

                """
            video_plan = generate_chat_response(prompt)
            print(f"plan: {video_plan} \n \n \n")
            print(f"accumulated: {current_accumulated_plan} \n \n \n")
            #print(f" ----- video_plan: {video_plan} \n \n \n")            
            time.sleep(40)
            if "Gemini SDK Error" in video_plan or "Sorry, I'm having trouble thinking right now. Please try again later." in video_plan:
                return gen_part(part_, current_accumulated_plan)
            else: 
                return video_plan
        full_plan += gen_part(part, full_plan)
    if len(str(full_plan)) < 15000:
        return generate_script(topic, get_idea(topic))
    with open(script / "TodaysScript.txt", "w") as file:
        file.write(full_plan)
    return full_plan


