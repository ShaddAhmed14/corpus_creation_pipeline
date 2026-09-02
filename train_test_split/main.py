import yaml
import json
from pathlib import Path

from split_pipeline import run_split_pipeline
from plotting import create_plots
from special_functions import copy_renderings

if __name__ == "__main__":
    config_path = Path("config/corpus_details_template.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    metadata_directory = Path(config.get("defaults", {}).get("output_directory", ""))
    if not metadata_directory:
        raise ValueError("Output directory not specified in the configuration file.")

    metadata_path = metadata_directory / "clips_metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    by_corpus = metadata.get("by_corpus", {})

    train_ratio = 0.75 # test ratio is 0.25
    files_directory = Path("PATH_TO_FILES_DIRECTORY") # this is where the files to split are located
    file_extension = ".npz" # this is the file extension of the files to split
 
    output_directory = Path("PATH_TO_OUTPUT_DIRECTORY") # this is where we will store the train test split metadata and plots
    output_directory.mkdir(exist_ok=True, parents=True)
    PLOTS_DIR = output_directory / "plots"
    CSV_DIR = output_directory / "csv"
    PLOTS_DIR.mkdir(exist_ok=True)
    CSV_DIR.mkdir(exist_ok=True)

    # store the train test split metadata in csv format
    metadata_detailed_path = CSV_DIR / "metadata_detailed.csv"
    metadata_summary_path = CSV_DIR / "metadata_summary.csv"

    run_split_pipeline(by_corpus, files_directory, file_extension, train_ratio, metadata_detailed_path, metadata_summary_path, output_directory, copy_files=True)
    create_plots(metadata_summary_path, metadata_detailed_path, PLOTS_DIR)

    # special functions
    copy_renderings(metadata_detailed_path, output_directory)
