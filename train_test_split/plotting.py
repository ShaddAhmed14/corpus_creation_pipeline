import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def plot_bar(totals: pd.Series, title: str, xlabel: str, ylabel: str, output_path: Path):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(totals.index, totals.values, color=["tab:blue", "tab:orange"])
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_title(title)

    total = totals.sum()
    for i, v in enumerate(totals.values): # add text - ratio and count
        pct = v / total * 100 if total else 0
        ax.text(i, v, f"{v} - ({pct:.1f}%)", ha="center", va="bottom")

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

def plot_distribution(summary_df: pd.DataFrame, plots_dir: Path):
    # overall set distribution
    totals = summary_df.groupby("set")["count"].sum()
    plot_bar(totals, "Set Distribution", "Set", "File count", plots_dir / "set_distribution.png")

    # overall label distribution
    totals = summary_df.groupby("label")["count"].sum()
    plot_bar(totals, "Label Distribution", "Label", "File count", plots_dir / "label_distribution.png")

def plot_by_corpus_bar(pivot: pd.DataFrame, title: str, xlabel: str, ylabel: str, output_path: Path):
    ax = pivot.plot(kind="bar", figsize=(8, 5))
    
    row_totals = pivot.sum(axis=1)
    for container, col in zip(ax.containers, pivot.columns):
        for bar, corpus in zip(container, pivot.index):
            v = bar.get_height()
            total = row_totals[corpus]
            pct = v / total if total else 0
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{int(v)}\n{pct:.2f}",
                    ha="center", va="bottom", fontsize=6)
            
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_by_corpus_distribution(summary_df: pd.DataFrame, output_path: Path):
    # set distribution per corpus
    pivot = summary_df.groupby(["corpus", "set"])["count"].sum().unstack(fill_value=0)
    pivot = pivot.reindex(columns=["train", "test"])
    plot_by_corpus_bar(pivot, "Set Distribution per Corpus", "Corpus", "File count", output_path / "set_distribution_per_corpus.png")

    # label distribution per corpus
    pivot = summary_df.groupby(["corpus", "label"])["count"].sum().unstack(fill_value=0)
    plot_by_corpus_bar(pivot, "Label Distribution per Corpus", "Corpus", " File count", output_path / "label_distribution_per_corpus.png")

def plot_file_count_distribution(detailed_df: pd.DataFrame, output_path: Path):
    """
    Histogram of file counts per speaker (across all corpora/labels).
    Shows how skewed speaker sizes are -- large outliers explain why
    some corpora can't hit the target ratio exactly.
    """
    per_speaker_file_count = detailed_df.groupby(["corpus", "speaker"]).size()
 
    fig, ax = plt.subplots(figsize=(7, 5))
    counts, bin_edges, patches = ax.hist(per_speaker_file_count.values, bins=20, color=["tab:blue"], edgecolor="black")

    total_speakers = len(per_speaker_file_count)
    for count, patch in zip(counts, patches):
        if count > 0:
            pct = count / total_speakers
            ax.text(patch.get_x() + patch.get_width() / 2, count, f"{int(count)}\n{pct:.2f}",
                    ha="center", va="bottom", fontsize=6)

    ax.set_xlabel("Files per speaker")
    ax.set_ylabel("Number of speakers")
    ax.set_title("Distribution of File Counts per Speaker")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

def plot_speaker_count_per_set(detailed_df: pd.DataFrame, output_path: Path):
    """
    Per corpus: number of UNIQUE speakers in each set.
    """
    counts = (
        detailed_df.drop_duplicates(["corpus", "speaker", "set"])
        .groupby(["corpus", "set"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["train", "test"])
    )
 
    ax = counts.plot(kind="bar", figsize=(8, 5), color=["tab:blue", "tab:orange"])

    row_totals = counts.sum(axis=1)
    for container, col in zip(ax.containers, counts.columns):
        for bar, corpus in zip(container, counts.index):
            v = bar.get_height()
            total = row_totals[corpus]
            pct = v / total if total else 0
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{int(v)}\n{pct:.2f}",
                    ha="center", va="bottom", fontsize=6)

    ax.set_ylabel("Number of speakers")
    ax.set_title("Speaker Count per Set per Corpus")
    ax.set_xlabel("Corpus")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def create_plots(metadata_summary_path: Path, metadata_detailed_path: Path, plots_dir: Path):
    """Create plots using the metadata."""
    summary_df = pd.read_csv(metadata_summary_path)
    detailed_df = pd.read_csv(metadata_detailed_path)

    plot_distribution(summary_df, plots_dir)
    plot_by_corpus_distribution(summary_df, plots_dir)

    plot_file_count_distribution(detailed_df, plots_dir / "file_count_distribution.png")
    plot_speaker_count_per_set(detailed_df, plots_dir / "speaker_count_per_set.png")

    print(f"Plots created in {plots_dir}.")
