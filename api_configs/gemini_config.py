import os
from dotenv import load_dotenv
from google import genai 
import base64
from openai import OpenAI
import xai_sdk
from pathlib import Path
import requests

load_dotenv()
cwd = Path(".")
upload_dir = cwd / "ready_to_upload"

# The client is now inside 'genai'
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
XAI_Key = os.getenv('GROK_KEY')

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
    
def grok(topic, date, prompt):
    try:
        xai_client = xai_sdk.Client(api_key=os.getenv("GROK_KEY"))
                
        response = xai_client.image.sample(
            model="grok-imagine-image",
            prompt=prompt,
            aspect_ratio="16:9",
            resolution="1k"
        )   
        
        img_url = response.url
        image_data = requests.get(img_url).content
        output_url = upload_dir / f"{topic}_thumbnail_{date}.jpg"
        with open(output_url, "wb") as handler:
            handler.write(image_data)
        print(f"Your YouTube Thumbnail URL: {response.url}")
        return output_url.resolve()
        
    except Exception as e:
        print(f"Grok SDK Error: {e}")
        return None
    
