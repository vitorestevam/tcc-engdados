#!/usr/bin/env python3
"""Filtra e padroniza os comentarios dos videos ja selecionados como relevantes (Etapa 3 da Silver).

Classificacao por tema/candidato e agregacoes ficam para a camada Gold.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from silver.cleaning import clean_text, to_utc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRONZE_COMMENTS_DIR = PROJECT_ROOT / "data" / "comments"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
VIDEOS_SILVER_FILE = SILVER_DIR / "videos_silver.parquet"
OUTPUT_FILE = SILVER_DIR / "comments_silver.parquet"

OUTPUT_COLUMNS = [
    "comment_id",
    "video_id",
    "source",
    "category",
    "parent_id",
    "text_clean",
    "published_at",
    "updated_at",
    "is_edited",
    "like_count",
    "source_file",
    "processed_at",
]


def load_bronze_comments(comments_dir: Path) -> list[dict]:
    comments = []
    for path in sorted(comments_dir.glob("comments_*.json")):
        comments.extend(load_bronze_comments_file(path))
    return comments


def load_bronze_comments_file(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    collected_at = payload.get("collected_at")
    comments = []
    for comment in payload.get("comments", []):
        comment = dict(comment)
        comment["source_file"] = path.name
        comment["collected_at"] = collected_at
        comments.append(comment)
    return comments


def deduplicate_latest(comments: list[dict]) -> list[dict]:
    # mantem, por comment_id, o registro coletado na execucao mais recente (ex.: comentario editado)
    latest_by_id: dict[str, dict] = {}
    for comment in comments:
        existing = latest_by_id.get(comment["comment_id"])
        if existing is None or comment["collected_at"] >= existing["collected_at"]:
            latest_by_id[comment["comment_id"]] = comment
    return list(latest_by_id.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Filtra e padroniza os comentarios dos videos relevantes.")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--comments-dir", type=Path, default=BRONZE_COMMENTS_DIR)
    input_group.add_argument("--comments-file", type=Path, help="JSON Bronze de uma execucao especifica")
    parser.add_argument("--videos-silver-file", type=Path, default=VIDEOS_SILVER_FILE)
    parser.add_argument("--output-file", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()

    relevant_video_ids = set(pd.read_parquet(args.videos_silver_file)["video_id"])

    source_comments = (
        load_bronze_comments_file(args.comments_file)
        if args.comments_file
        else load_bronze_comments(args.comments_dir)
    )
    comments = source_comments
    comments = [comment for comment in comments if comment["video_id"] in relevant_video_ids]
    comments = deduplicate_latest(comments)

    df = pd.DataFrame(comments)
    df["text_clean"] = df["text"].apply(clean_text)
    df["published_at"] = df["published_at"].apply(to_utc)
    df["updated_at"] = df["updated_at"].apply(to_utc)
    df["is_edited"] = df["published_at"] != df["updated_at"]
    df["processed_at"] = datetime.now(UTC)

    silver_df = df[OUTPUT_COLUMNS].drop_duplicates(subset="comment_id", keep="last")

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    silver_df.to_parquet(args.output_file, index=False)
    print(f"{len(silver_df)} comentarios gravados em {args.output_file}")


if __name__ == "__main__":
    main()
