import yaml
import json
from pathlib import Path

from split_pipeline import run_split_pipeline
from plotting import create_plots

if __name__ == "__main__":
    config_path = Path("config/corpus_details_template.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    output_directory = Path(config.get("defaults", {}).get("output_directory", ""))
    if not output_directory:
        raise ValueError("Output directory not specified in the configuration file.")

    metadata_path = output_directory / "clips_metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    file_extension = ".mp4"
    train_ratio = 0.75 # test ratio is 0.25

    PLOTS_DIR = Path("plots")
    CSV_DIR = Path("csv")
    PLOTS_DIR.mkdir(exist_ok=True)
    CSV_DIR.mkdir(exist_ok=True)

    # store the train test split metadata in csv format
    metadata_detailed_path = CSV_DIR / "metadata_detailed.csv"
    metadata_summary_path = CSV_DIR / "metadata_summary.csv"

    by_corpus = metadata.get("by_corpus", {})
    run_split_pipeline(by_corpus, output_directory, file_extension, train_ratio, metadata_detailed_path, metadata_summary_path)
    create_plots(metadata_summary_path, metadata_detailed_path, PLOTS_DIR)
