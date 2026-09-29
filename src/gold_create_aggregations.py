#!/usr/bin/env python3
"""Gera agregacoes de candidatos e temas para a camada Gold."""

import argparse
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
VIDEOS_FILE = SILVER_DIR / "videos_silver.parquet"
COMMENTS_FILE = GOLD_DIR / "comments_with_sentiment.parquet"
CANDIDATES_OUTPUT_FILE = GOLD_DIR / "candidatos_manifestacoes.parquet"
THEMES_OUTPUT_FILE = GOLD_DIR / "temas_engajamento.parquet"


def add_sentiment_percentages(frame: pd.DataFrame) -> pd.DataFrame:
    for sentiment in ("positivo", "negativo", "neutro"):
        frame[f"sentimento_{sentiment}_pct"] = (
            frame[f"sentimento_{sentiment}"]
            .div(frame["comentarios_total"].replace(0, pd.NA))
            .mul(100)
            .fillna(0.0)
            .round(2)
        )
    return frame


def aggregate_sentiment(group: pd.DataFrame) -> pd.Series:
    return pd.Series(
        {
            "comentarios_total": group["comment_id"].count(),
            "likes_comentarios_total": group["like_count"].sum(),
            "sentimento_positivo": (group["sentimento"] == "POSITIVO").sum(),
            "sentimento_negativo": (group["sentimento"] == "NEGATIVO").sum(),
            "sentimento_neutro": (group["sentimento"] == "NEUTRO").sum(),
            "score_sentimento_medio": group["score_sentimento"].mean(),
        }
    )


def create_gold_aggregations(
    videos_file: Path | str = VIDEOS_FILE,
    comments_file: Path | str = COMMENTS_FILE,
    candidates_output_file: Path | str = CANDIDATES_OUTPUT_FILE,
    themes_output_file: Path | str = THEMES_OUTPUT_FILE,
) -> None:
    videos = pd.read_parquet(videos_file)
    comments = pd.read_parquet(comments_file)

    candidates = videos.explode("candidatos_mencionados").dropna(subset=["candidatos_mencionados"])
    candidates_summary = candidates.groupby("candidatos_mencionados").agg(
        videos_total=("video_id", "count"),
        likes_videos_total=("like_count", "sum"),
    ).reset_index(names="candidato")
    candidate_comments = candidates[["video_id", "candidatos_mencionados"]].merge(
        comments, on="video_id", how="left"
    )
    candidates_sentiment = (
        candidate_comments.groupby("candidatos_mencionados")
        .apply(aggregate_sentiment)
        .reset_index(names="candidato")
    )
    candidates_table = add_sentiment_percentages(
        candidates_summary.merge(candidates_sentiment, on="candidato", how="outer").fillna(0)
    ).sort_values("comentarios_total", ascending=False)

    theme_comments = videos[["video_id", "channel_title"]].merge(comments, on="video_id", how="left")
    themes_table = (
        theme_comments.groupby("channel_title")
        .apply(
            lambda group: pd.Series(
                {
                    "videos_total": group["video_id"].nunique(),
                    "comentarios_total": group["comment_id"].count(),
                    "likes_media": group["like_count"].mean(),
                    "sentimento_positivo": (group["sentimento"] == "POSITIVO").sum(),
                    "sentimento_negativo": (group["sentimento"] == "NEGATIVO").sum(),
                    "sentimento_neutro": (group["sentimento"] == "NEUTRO").sum(),
                    "score_sentimento_medio": group["score_sentimento"].mean(),
                }
            )
        )
        .reset_index(names="tema")
    )
    themes_table = add_sentiment_percentages(themes_table.fillna(0)).sort_values(
        "comentarios_total", ascending=False
    )

    candidates_output_file = Path(candidates_output_file)
    themes_output_file = Path(themes_output_file)
    candidates_output_file.parent.mkdir(parents=True, exist_ok=True)
    themes_output_file.parent.mkdir(parents=True, exist_ok=True)
    candidates_table.to_parquet(candidates_output_file, index=False)
    themes_table.to_parquet(themes_output_file, index=False)
    print(f"{len(candidates_table)} candidatos gravados em {candidates_output_file}")
    print(f"{len(themes_table)} temas gravados em {themes_output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera agregacoes de candidatos e temas da camada Gold.")
    parser.add_argument("--videos-file", type=Path, default=VIDEOS_FILE)
    parser.add_argument("--comments-file", type=Path, default=COMMENTS_FILE)
    parser.add_argument("--candidates-output-file", type=Path, default=CANDIDATES_OUTPUT_FILE)
    parser.add_argument("--themes-output-file", type=Path, default=THEMES_OUTPUT_FILE)
    args = parser.parse_args()
    create_gold_aggregations(
        args.videos_file,
        args.comments_file,
        args.candidates_output_file,
        args.themes_output_file,
    )


if __name__ == "__main__":
    main()
