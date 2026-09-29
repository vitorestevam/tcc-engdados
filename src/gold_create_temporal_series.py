#!/usr/bin/env python3
"""Gera a serie temporal de volume da camada Gold."""

import argparse
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
VIDEOS_FILE = SILVER_DIR / "videos_silver.parquet"
COMMENTS_FILE = GOLD_DIR / "comments_with_sentiment.parquet"
OUTPUT_FILE = GOLD_DIR / "serie_temporal_volume.parquet"


def create_temporal_series(
    videos_file: Path | str = VIDEOS_FILE,
    comments_file: Path | str = COMMENTS_FILE,
    output_file: Path | str = OUTPUT_FILE,
) -> None:
    videos = pd.read_parquet(videos_file)
    comments = pd.read_parquet(comments_file)
    videos["data"] = pd.to_datetime(videos["published_at"], utc=True).dt.date
    comments["data"] = pd.to_datetime(comments["published_at"], utc=True).dt.date

    videos_by_date = videos.groupby("data").size().reset_index(name="videos_novos")
    comments_by_date = comments.groupby("data").agg(
        comentarios_novos=("comment_id", "count"),
        likes_total=("like_count", "sum"),
        sentimento_medio=("score_sentimento", "mean"),
    ).reset_index()
    temporal = videos_by_date.merge(comments_by_date, on="data", how="outer")
    temporal["videos_novos"] = temporal["videos_novos"].fillna(0).astype(int)
    temporal["comentarios_novos"] = temporal["comentarios_novos"].fillna(0).astype(int)
    temporal["likes_total"] = temporal["likes_total"].fillna(0).astype(int)
    temporal["engajamento_medio"] = (
        temporal["comentarios_novos"] / temporal["videos_novos"].replace(0, pd.NA)
    ).fillna(0.0)
    temporal["sentimento_medio"] = temporal["sentimento_medio"].fillna(0.0)
    temporal["data"] = pd.to_datetime(temporal["data"])
    temporal = temporal.sort_values("data").reset_index(drop=True)

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporal.to_parquet(output_file, index=False)
    print(f"{len(temporal)} dias gravados em {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera a serie temporal da camada Gold.")
    parser.add_argument("--videos-file", type=Path, default=VIDEOS_FILE)
    parser.add_argument("--comments-file", type=Path, default=COMMENTS_FILE)
    parser.add_argument("--output-file", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()
    create_temporal_series(args.videos_file, args.comments_file, args.output_file)


if __name__ == "__main__":
    main()
