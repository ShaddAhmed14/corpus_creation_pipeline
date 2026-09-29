# Corpus creation pipeline

This project extracts labeled gesture and non-gesture video clips from source corpora, builds clip metadata and summary figures, and provides a separate train/test split for derived files.

## Clip creation

Requirements: Python, `ffmpeg` and `ffprobe` on `PATH`, plus `pyyaml`, `pandas`, `numpy`, and `matplotlib`:

```powershell
python -m pip install pyyaml pandas numpy matplotlib
```

Copy `config/corpus_details_template.yaml` to `config/corpus_details.yaml`. Set `defaults.output_directory` and replace the example under `corpora` with entries containing a name, source directory, and class path. Set `enabled: false` to skip an entry.

| Corpus name | Module value | Source files |
| --- | --- | --- |
| ECOLANG | `corpora.ecolang.Ecolang` | `*final.txt` annotations and matching MP4 files |
| GESRes | `corpora.gesres.GesRes` | `GESRes_dataset.csv` and source MP4 files |
| Multisimo | `corpora.multisimo.Multisimo` | Matching `.mp4` and `.txt` files |
| SAGA | `corpora.saga.Saga` | Video and annotation subdirectories with MP4 and CSV files |
| SAGAplus | `corpora.saga_plus.SagaPlus` | Video and annotation subdirectories with MP4 and TXT files |
| TEDM3D | `corpora.tedm3d.TedM3D` | Matching `.csv` and `.mp4` files |
| ZHUBO | `corpora.zhubo.Zhubo` | `*.h264.mp4` videos and matching `.actions.json` files |

Use these corpus names if you will run the split stage, which has name-specific handling for SAGA, SAGAplus, and ZHUBO. See `corpus_clips_creation/corpora/` for exact filename and annotation rules.

Run from `corpus_clips_creation`, since its entry point opens the configuration relative to the current directory:

```powershell
cd corpus_clips_creation
python main.py
```

The output directory contains `GestureClips/`, `NoGestureClips/`, and `MoveClips/`; per-video JSON records in `ClipsInfo/`; aggregate `clips_metadata.json`; CSV tables and PNG figures in `summary_plots_tables/`; and timestamped logs in `logs/`. `num_workers` controls corpus-level concurrency. Set `create_clips: false` to rebuild metadata and summaries from existing `ClipsInfo/` records.

## Train/test split

The separate `train_test_split/main.py` stage reads `clips_metadata.json` and groups matching derived files by corpus and speaker. Before running it, edit `files_directory` (derived files), `file_extension` (default `.npz`), and `output_directory` in that script. Set `defaults.output_directory` in `config/corpus_details_template.yaml` to the directory containing `clips_metadata.json`, since the split script reads the template directly. Set `RENDERINGS_DIR` in `train_test_split/special_functions.py` if you want matching rendering videos copied.

Run this stage from the project root:

```powershell
python train_test_split/main.py
```

The script targets a 75/25 split by speaker within each corpus, keeps ZHUBO in training, groups paired SAGA and SAGAplus speakers together, and treats `Move` as `NoGesture`. It writes `csv/metadata_detailed.csv`, `csv/metadata_summary.csv`, plots in `plots/`, and copies matching files into `train/<label>/` and `test/<label>/` under the chosen split directory.

### List test speakers

`train_test_split/fetch_test_speakers.py` collects the unique speaker identifiers present in test `.npz` files. Set `INPUT_FOLDER_CLIPS` in the script to the test directory containing one subdirectory per metalabel, such as `test/Gesture/` and `test/NoGesture/`. Install its additional dependency with `python -m pip install python-dotenv`, then run it from the project root:

```powershell
python train_test_split/fetch_test_speakers.py
```

It prints the speaker count for each metalabel and writes `speaker_distribution.json` in the current directory. The JSON has a `test` object mapping each metalabel to a list of speaker identifiers, extracted from `.npz` filenames by removing their last three underscore-separated fields.
