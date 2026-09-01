import pandas as pd
from pathlib import Path
from collections import defaultdict

def split_files_by_label(file_paths: list):
    """
    Splits a list of file paths by their labels. Returns: dict[label] = [file_paths]
    """
    split_by_label_file_paths = {}
    for file_path in file_paths:
        label = file_path.stem.split("_")[-2]
        split_by_label_file_paths.setdefault(label, []).append(file_path)
    # merge NoGesture and Move
    if "NoGesture" in split_by_label_file_paths and "Move" in split_by_label_file_paths:
        split_by_label_file_paths["NoGesture"].extend(split_by_label_file_paths.pop("Move"))
    return split_by_label_file_paths

def create_files_mapping(by_corpus_data: dict, files_folder: Path, file_extension: str):
    """
    Returns: dict[corpus_name][speaker][label] = [file_paths]
    """
    files_mapping = defaultdict(dict)
    for corpus_name, corpus_details in by_corpus_data.items():
        print(f"Processing corpus: {corpus_name}")
        unique_speakers = corpus_details.get("unique_speakers_count", []).keys()
        # files_mapping[corpus_name] = {}
        for speaker in unique_speakers:
            file_paths = list(files_folder.rglob(f"{corpus_name}_{speaker}*{file_extension}"))
            files_mapping[corpus_name][speaker] = split_files_by_label(file_paths)

    return files_mapping

def greedy_split_speakers(speaker_label_files: dict, train_ratio: float):
    """
    speaker_label_files: dict[speaker_id][label] = [file_path, ...]
    train_ratio: fraction of files targeted for train, per label
 
    Returns: (train_speakers: dict[speaker][label] = [file_path, ...], test_speakers: dict[speaker][label] = [file_path, ...])
    """
    # total files per label, across all speakers -> per-label train target
    label_totals = defaultdict(int)
    for labels_files in speaker_label_files.values():
        for label, files in labels_files.items():
            label_totals[label] += len(files)
    label_targets = {label: total * train_ratio for label, total in label_totals.items()}
 
    # per-speaker per-label counts, for greedy scoring
    speaker_label_counts = {
        speaker: {label: len(files) for label, files in labels.items()}
        for speaker, labels in speaker_label_files.items()
    }
 
    # process largest speakers first (by total file count across labels)
    ordered = sorted(
        speaker_label_counts.items(),
        key=lambda kv: sum(kv[1].values()), # kv is (speaker, label_counts)
        reverse=True,
    )
 
    train_counts = defaultdict(int)
    train_speaker_label_files, test_speaker_label_files = dict(), dict()
 
    for speaker, label_counts in ordered:
        def deviation(to_train: bool): # decide where to put this speaker, based on how it affects deviation from label targets
            dev = 0.0
            for label, cnt in label_counts.items():
                projected = train_counts[label] + (cnt if to_train else 0)
                dev += abs(projected - label_targets[label])
            return dev
 
        if deviation(to_train=True) <= deviation(to_train=False):
            train_speaker_label_files[speaker] = speaker_label_files[speaker]
            for label, cnt in label_counts.items():
                train_counts[label] += cnt
        else:
            test_speaker_label_files[speaker] = speaker_label_files[speaker]
 
    return train_speaker_label_files, test_speaker_label_files

def split_dataset_saga_saga_plus(files_mapping: dict, SAGA_name: str, SAGA_plus_name: str, train_ratio: float):
    training_set, testing_set = dict(), dict()
    SAGA_files_mapping = files_mapping.pop(SAGA_name, {})
    SAGA_plus_files_mapping = files_mapping.pop(SAGA_plus_name, {})
    common_corpus = f"{SAGA_name}_{SAGA_plus_name}" # for speakers that have both SAGA and SAGA+ clips

    common_speakers_mapping = defaultdict(dict) # speaker -> label -> [file_paths] # creates empty dicts for new speakers automatically
    speakers_to_remove = [] # from saga
    for saga_speaker, saga_label_files in SAGA_files_mapping.items():
        saga_plus_speaker = f"{saga_speaker}K2"
        if saga_plus_speaker in SAGA_plus_files_mapping: # find common speakers
            for label, saga_files in saga_label_files.items():
                common_speakers_mapping[f"{saga_speaker}_{saga_plus_speaker}"][label] = saga_files + SAGA_plus_files_mapping[saga_plus_speaker].get(label, [])

            SAGA_plus_files_mapping.pop(saga_plus_speaker)  # Remove the paired SAGA+ speaker to avoid duplication
            speakers_to_remove.append(saga_speaker)  # Add the paired SAGA speaker to the list of speakers to remove

    for speaker in speakers_to_remove:
        SAGA_files_mapping.pop(speaker)  # Remove the paired SAGA speaker to avoid duplication

    training_set[common_corpus], testing_set[common_corpus] = greedy_split_speakers(common_speakers_mapping, train_ratio)
    training_set[SAGA_plus_name], testing_set[SAGA_plus_name] = greedy_split_speakers(SAGA_plus_files_mapping, train_ratio)
    training_set[SAGA_name], testing_set[SAGA_name] = greedy_split_speakers(SAGA_files_mapping, train_ratio)

    return training_set, testing_set

def flatten_split(split_dict: dict, set_name: str):
    """
    split_dict: corpus -> speaker -> label -> [file_paths]
    Returns: list of dict per file
    """
    rows = []
    for corpus_name, speakers in split_dict.items():
        for speaker, label_dict in speakers.items():
            for label, file_paths in label_dict.items():
                for file_path in file_paths:
                    rows.append({
                        "corpus": corpus_name,
                        "speaker": speaker,
                        "label": label,
                        "set": set_name,
                        "file_path": file_path,
                    })
    return rows
 
def build_df(training_set: dict, testing_set: dict):
    """
    Input: training_set, testing_set: dict[corpus][speaker][label] : [file_paths]
 
    Returns:
      detailed_df columns: corpus, speaker, label, set, file_path   (one row per file)
      summary_df  columns: corpus, speaker, label, set, count       (one row per group)
    """
    rows = flatten_split(training_set, "train") + flatten_split(testing_set, "test")
    detailed_df = pd.DataFrame(rows)
 
    summary_df = (
        detailed_df.groupby(["corpus", "speaker", "label", "set"])
        .size()
        .reset_index(name="count")
    ) # file count
 
    return detailed_df, summary_df

def run_split_pipeline(by_corpus_data: dict, files_folder_path: Path, file_extension: str, train_ratio: float, metadata_detailed_path: str, metadata_summary_path: str):
    files_mapping = create_files_mapping(by_corpus_data, files_folder_path, file_extension)

    # these 2 need special treatment - we initialize training and testing sets from here
    SAGA_name = "SAGA"
    SAGA_plus_name = "SAGAplus"
    training_set, testing_set = split_dataset_saga_saga_plus(files_mapping, SAGA_name, SAGA_plus_name, train_ratio)
    print(f"Created training and testing sets for {SAGA_name} and {SAGA_plus_name}")

    training_only_corpora = ["ZHUBO"] # these corpora will have no testing set
    for corpus_name in training_only_corpora:
        speaker_mapping = files_mapping.pop(corpus_name, {}) # remove from files_mapping so it doesn't get processed again
        training_set[corpus_name], testing_set[corpus_name] = greedy_split_speakers(speaker_mapping, 1.0) # all go to training set
    print(f"Created training set for {training_only_corpora}")

    for corpus_name, speakers in files_mapping.items(): # process remaining corpora
        training_set[corpus_name], testing_set[corpus_name] = greedy_split_speakers(speakers, train_ratio)
    print("Created training and testing sets for remaining corpora")

    metadata_detailed_df, metadata_summary_df = build_df(training_set, testing_set)
    metadata_detailed_df.to_csv(metadata_detailed_path, index=False)
    metadata_summary_df.to_csv(metadata_summary_path, index=False)
    print("Saved metadata csv files")