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


def script_to_json(prompt, script_dir=Path(".")):
    content = prompt

    # Updated regex to handle nested structures like arrays [tag1, tag2] inside the curly braces
    raw_dicts = re.findall(r"\{.*?\}", content, re.DOTALL)

    scenes_list = []
    for d in raw_dicts:
        try:
            # Load each item individually
            scene_data = json.loads(d)
            scenes_list.append(scene_data)
        except json.JSONDecodeError:
            # Catch and skip minor syntax anomalies inside a specific block
            continue

    # Process and format according to the new schema
    for index, scene in enumerate(scenes_list, start=1):
        scene["scene"] = index

        # Safe extraction and slicing for timestamps (HH:MM:SS)
        if "start_time" in scene and scene["start_time"]:
            scene["start_time"] = scene["start_time"][0:8]
        if "end_time" in scene and scene["end_time"]:
            scene["end_time"] = scene["end_time"][0:8]

        # Ensuring the target keys exist based on your outputFormat
        scene["title"] = scene.get("title", f"Scene {index}")
        scene["description"] = scene.get("description", "")

        # Handle tags safely (ensuring it's a list)
        tags = scene.get("tags", [])
        scene["tags"] = tags if isinstance(tags, list) else [tags]

    output_file = "video_script.json"
    output_path = Path(script_dir) / output_file

    # Open, write, and automatically close the file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenes_list, f, indent=2, ensure_ascii=False)

    print(f"Successfully saved JSON to {output_path}")
    
    # Return the clean list of scenes so ai.py can use it!
    return scenes_list
