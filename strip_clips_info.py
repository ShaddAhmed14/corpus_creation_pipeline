import json
from tqdm import tqdm
from pathlib import Path

def strip_clips_info(clips_info_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fields_to_ignore = ['source_video_path', 'output_path']
    clips_info_files = clips_info_dir.glob('*json')
    for clips_info_file in tqdm(clips_info_files, desc="Processing clips info files"):
        stripped_clips_info = []
        with open(clips_info_file, 'r') as f:
            clips_info = json.load(f)
        for clip in clips_info:
            stripped_clip = {k: v for k, v in clip.items() if k not in fields_to_ignore}
            stripped_clips_info.append(stripped_clip)
        
        output_path = output_dir / clips_info_file.name
        with open(output_path, 'w') as f:
            json.dump(stripped_clips_info, f, indent=4)

        
if __name__ == "__main__":
    clips_info_dir = Path("PATH/TO/CorpusClips/ClipsInfo")
    output_dir = Path("PATH/TO/CorpusClips/ClipsInfo_stripped")
    strip_clips_info(clips_info_dir, output_dir)