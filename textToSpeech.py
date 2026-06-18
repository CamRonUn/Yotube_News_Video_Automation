import soundfile as sf
from kokoro import KPipeline
from pathlib import Path
import json

cwd = Path(".")
audio_dir = cwd / "audio_files"
script_dir = cwd / "script"

def text_to_speech(text_to_say,scene):
    pipeline = KPipeline(lang_code='a')

    print("⚡ Processing text and generating audio...")

    # 2. Run the pipeline
    # 'af_heart' is a highly rated, built-in premium female voice style
    generator = pipeline(
        text_to_say, 
        voice='af_heart', 
        speed=1.0, 
        split_pattern=r'\n+' # How it chunk-splits long paragraphs
    )

    # 3. Iterate through the generated segments and write them out
    # Kokoro operates at a crisp 24kHz sampling rate
    for i, (graphemes, phonemes, audio) in enumerate(generator):
        output_filename = f"scene_{scene}_audio.wav"
        sf.write(audio_dir / output_filename, audio, 24000)
        print(f"💾 Saved segment {i} to {output_filename}")

    print("🎉 Audio generation complete!")

def generate_video_audio():
    with open(script_dir / "video_script.json", "r") as file: 
        data = json.load(file)
    for scene in data:
        if scene['script'] != "x":
            text_to_speech(scene['script'], scene['scene'])



