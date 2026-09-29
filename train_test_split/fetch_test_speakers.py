import os
import json
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()  # Load environment variables from .env file

INPUT_FOLDER_CLIPS = Path("TEST_NPZ_FOLDER")
json_save_path = Path('speaker_distribution.json')

speaker_distribution = {}
speaker_distribution['test'] = {}

for metalabel_dir in INPUT_FOLDER_CLIPS.iterdir():
    if metalabel_dir.is_dir():
        metalabel = metalabel_dir.name
        speaker_distribution['test'][metalabel] = {}
        unique_speakers = set()

        for npz_file in metalabel_dir.glob("*.npz"):
            file_name = npz_file.stem
            parts = file_name.rsplit('_', 3)[0]  # Get the part before the last three underscores
            unique_speakers.add(parts) # corpus_speakerId

        speaker_distribution['test'][metalabel] = list(unique_speakers)

for metalabel, speakers in speaker_distribution['test'].items():
    print(f"Metalabel: {metalabel}, Unique Speakers: {len(speakers)}")


with open(json_save_path, 'w') as f:
    json.dump(speaker_distribution, f, indent=4)