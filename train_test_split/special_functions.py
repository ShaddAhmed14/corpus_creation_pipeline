import pandas as pd
from pathlib import Path

def long_path_process(file_path: Path):
    """
    Converts a file path to a long path format to handle long file paths in Windows.
    """
    file_path = file_path.resolve()
    str_path = str(file_path)
    required_string = "\\\\?\\"
    if not str_path.startswith(required_string):
        str_path = required_string + str_path
    return Path(str_path)

def copy_renderings(detailed_df_path: Path, output_directory: Path):
    """
    Copies the files from the original location to the new split folder structure.
    """
    def file_path_convertor(file_path: Path):
        # hardcoded changing file path to rendering file path
        RENDERINGS_DIR = Path("PATH_TO_RENDERINGS_DIRECTORY") # this is where the rendering files are located
        rendering_file_paths = (RENDERINGS_DIR / file_path.stem).rglob(f"{file_path.stem}_*.mp4")
        rendering_file_paths = list(rendering_file_paths)
        return long_path_process(rendering_file_paths[0]) if rendering_file_paths else None

    detailed_df = pd.read_csv(detailed_df_path)
    sets = detailed_df['set'].unique()
    labels = detailed_df['label'].unique()
    for s in sets:
        for l in labels:
            s_l_dir = output_directory / s / l
            s_l_dir.mkdir(exist_ok=True, parents=True)
            files_to_copy = detailed_df[(detailed_df['set'] == s) & (detailed_df['label'] == l)]['file_path']
            for file_path in files_to_copy:
                rendering_file_path = file_path_convertor(Path(file_path))
                if rendering_file_path is None:
                    print(f"Rendering file not found for {file_path}, skipping.")
                    continue
                try:
                    destination = s_l_dir / rendering_file_path.name

                    if not destination.exists():
                        destination.write_bytes(rendering_file_path.read_bytes())
                except Exception as e:
                    print(f"Error occurred while copying rendering of {rendering_file_path} to {s_l_dir}: \n {e}\n")