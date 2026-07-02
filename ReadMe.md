# Youtube Video Automation 

## What This Does 
- This Script generates ai daily news videos usually 20-30 mins long using real youtube videos clipped up that were uploaded in the last day, a free ai voice over, free stock images where needed to generate the news video for free then using grok to make a $0.02 thumbnail then auto uploads videos to youtube. then cuts upp videos over 30 mins in shorts and uploads them.

- currently setup to upload a triathlon, cycling, ai, basketball news video but you can edit the **"topics"** in the main.py folder

## How It Works 
1. Authenticate your youtube account or 2 
2. Fetch and download the top youtube videos on a topic via yt-dip also gets subtitles and comments 
3. Fetch the top 5 global google news on that topic 
4. Using the videos and news articles it generates 3 ideas for a video story and then simulates 100 votes 50 from youtube experts and 50 from fans to pick the best plan 
5. Taking the best plan split it into parts for to avoid input token limits and get ai to generate a json giving final script, what clips to cut and where,scene by scene so the json plan can be executed and become a video
6. Solidify the json file into 1 big working json 
7. Generate all script audio scene by scene using koroka 
8. Trim all videos scene by scene using ffmpeg
9. Use moviepy to generate subtitles, and combine audio on each clip 
10. Use gemma to get a search term to find a stock image on pexels for scenes that dont have a video then use moviepy to add subtitles a zoom effect and the audio 
11. Combine all videos into master video with background music 
12. Generate meta data using google gemini for the youtube upload as well as use gemini to generate a thumbnail prompt which is then executed by grok imagine 
13. Use authentication from step 1 to upload full video to youtube with title, description tags
14. add s thumbnail to video automatically 90 seconds after upload 
15. cuts all videos over 30 mins into shorts and uploads them

## How To Use

### audio
- you must get a 40mins - 1 hour long background music track and name it background.mp3 in the main dir

### Add Folders 
- you must add directories audio_files, generated_images, news, ready_to_upload, script, video_clips, videos

### ENV Setup
- GROK_KEY
- GEMINI_API_KEY
- GOOGLE_CLIENT_SECRET -oauth with youtube api enabled 
- GOOGLE_CLIENT_ID -oauth with youtube api enabled 
- PEXELS_API_KEY

### Installation 
This project requires Python 3.10+, several external system dependencies (`ffmpeg`, `yt-dlp`), and the Kokoro TTS model weights. Follow the steps below to set up your environment. ### 1. Prerequisites Before installing the Python packages, you must install the required system tools. * **FFmpeg**: Required for `moviepy` video and audio processing. * **macOS**: `brew install ffmpeg` * **Windows**: Download from the official site or use `choco install ffmpeg` * **Linux**: `sudo apt install ffmpeg` * **yt-dlp**: Required for video fetching. * Ensure it is installed and available in your system's PATH. ### 2. Clone the Repository ```bash git clone <your-repository-url> cd <project-directory>

### Create the virtual environment 
- python -m venv venv # Activate it 
- On Windows (Command Prompt): venv\Scripts\activate # On Windows (PowerShell): .\venv\Scripts\activate 
- On macOS/Linux: source venv/bin/activate

### pip Install
pip install --upgrade pip 
pip install -r requirements.txt

### Run 
Python3 ./main.py

### Tips for your project: 
1. **Kokoro Setup:** The first time you initialize `KPipeline`, it will automatically attempt to download the model weight file (`kokoro-v0_19.pth`) and configuration files to your cache. Make sure your internet connection is active on the first run. 2. **MoviePy + FFmpeg:** `moviepy` usually automatically detects `ffmpeg`. If it throws an error saying it can't find it, you can explicitly point to your system path in your code, or ensure it's successfully added to your system's environmental variables.



## Major Challenges
- trying to make the final json (last process of script generation) because i need to give the ai the transcripts with time stamps, with request requires too many input tokens 
    - solutions: redesign my scripting process to create one plan but in a way that only requires certain videos for each part then i can create a prompt that follows the outline of the one section and only give 1 or 2 transcripts 
    - lots of prompt engineering to include all the data I need the final json script to have
- zonos was too heavy so had to downgrade voice model to kooro
- error handling api’s so errors dont cascade down the pipe line 
- asking ai for help on errors then using there alternative functions and loosing track of the video editing script a little bit.
    - After reviewing functions I had to make a few changes as i was still having trouble handling corrupted files, functions were now bloated due to AI’s attempted fixes but provided great debugging info. I figured it was too hard to handle all cases of corrupt video files so my solution was to rewrite the script if the video file was corrupted so it would become an image instead of a video.
- After beginning the auto upload scripts i realized it might not be possible to make fully automatic uploads since google api requires to login through there page 
    - solution i can authenticate multiple logins first and then run the automations 
- Bing search was outputting inappropriate images which combined with auto upload caused my account to get a content warning
	- solution switch to pexels a stock image api 
- after everything was finished I was having trouble trimming videos again due to file names. Could not figure it out with ai and didnt remember if i had changed anything. the trim Function was becoming bloated and i had lost control (didnt know what was happening in the function)
    - solution restarted ff_mpeg trim function hand wrote and took my time to make a solution that I understood that broke up file names into words and which ever file name had the most matched words was the video i used.

## Major Learnings 
- **(this is notes for my self on some of the packages and functions i learned fo the first time making this project and some of the notes i took from youtube videos)**
- **Python subprocess**
    - Alternative to os 
    - Lets me use the operating system to edit files on my computer this is required for the packages i want to use to download videos, and files such as yt-dlp and ffmpeg which i have never used before 
    - Syntax of subprocess 
        - Need to use .run or .Popen as an alternative subprocess.run(...)
        - Inside subprocess.run([...]) … is a terminal command example [“python3”, “timer.py”] will run the timer.py file in the repl 
        - Then commands after [ ], we have our other options such as stdout,   
        - subprocess.PIPE sends message stream to python instead of terminal 
- Sleep(x) waits x time  
- **PathLib** 
    - Path(“.”) points to cwd 
    - / concat paths example cwd = Path(“.”) => new_path = cwd / “Videos” 
    - Is the videos file 
    - print(new_path.resolve()) gives full path name 
    - Pure paths - for working on different machines from a different machine example windows to linus 
    - filepath.exists() returns bool 
    - Can use to iterate through dir and find files for filename in path.iterdir(): \n if filename.match(“*.txt”): 
    - .unlink() deletes files 
- **Zonos**
    - Too large 
    - But want to explore more with ai models like this that use pytorch 
- **MoviePy**
    - From moviepy.editor import …
    - VideoFileClip(“filename”).subclip(10,20) - trim 10-20 sec
    - Combined = concatenate_videoclips([array of videoClips]) ? how to make all my files video clips? 
    - Combined.write_videofile(path / “file.mp4”)
    - VideoFileClip().fx() - look at library for different effect
    - AudioFileClip, afx 
    - Audio = AudioFileClip(“intro.mp3”).fx(afx.volume, 0.5)
    - Combined.audio = CompositeAudioClip([audio])
    - Thus combined = concat…. \n combined.audio = compositeAudioClip([...]) combined write_videofile(“”)

## Initial Planning: 

- Collect the daily news 
    - scrape Youtube, IPO, ironman, other news outlets 
    - scrape youtube 
	    - yt-dlp
	    - youtube-transcript-api
    - Scrape news 
        - Newspaper 4k api

- Generate script 
    - Gemini api 
    - Give all information into 
    - Comments with over 10 likes filter from .info.json file “comments” like_count

- Generate voice 
    - Zonos - not sure if this will work on macbook

- Edit it together 
    - https://www.bannerbear.com/ can subtitles 
    - How am i going to find the clips i need?
        - .info.json has “chapters” useful in some video
        - Auto subtitles gives time stamps look for key words 
    - Ffmpeg stick everything together and cut videos
