from pathlib import Path
import re
import json

cwd = Path(".")
news_dir = cwd / "news"
script_dir = cwd / "script"
videos_dir = cwd / "videos"

def delete_all_files(folder_path: str | Path):
    #Delete all files in a dir

    directory = Path(folder_path)

    if not directory.is_dir():
        print("not directory")
        return 
    
    for item in directory.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
                print(f"deleteted {item.name}")
        except Exception as e:
            print(f"failed to detelete {item.name} reason {e}") 


def script_to_json(): 
    with open (script_dir / "TodaysScript.txt", "r") as script: 
        content = script.read()
    raw_dicts = re.findall(r"\{[^}]+\}", content)

    scenes_list = []
    for d in raw_dicts:
        try:
            # Load each item individual and append it to our master list
            scenes_list.append(json.loads(d))
        except json.JSONDecodeError as e:
            # Catch minor syntax anomalies inside a specific block if they exist
            continue

    for index, scene in enumerate(scenes_list, start=1):
        scene["scene"] = index
        scene["start_time"] = scene["start_time"][0:8] 
        scene["end_time"] = scene["end_time"][0:8] 

    output_file = "video_script.json"

    with open(script_dir / output_file, "w", encoding="utf-8") as f:
        json.dump(scenes_list, f, indent=2, ensure_ascii=False)

