#!/usr/bin/env python3
"""Seleciona, dentre os videos coletados na Bronze, os relacionados a eleicao a governador do Ceara 2026."""

import argparse
import json
from pathlib import Path

import pandas as pd

from silver.relevance import RELEVANCE_FILE, is_relevant, parse_relevance_terms

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRONZE_VIDEOS_DIR = PROJECT_ROOT / "data" / "videos"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def load_bronze_videos(bronze_dir: Path) -> list[dict]:
    videos = []
    for path in sorted(bronze_dir.glob("videos_*.json")):
        videos.extend(load_bronze_video_file(path))
    return videos


def load_bronze_video_file(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    collected_at = payload.get("collected_at")
    videos = []
    for video in payload.get("videos", []):
        video = dict(video)
        video["source_file"] = path.name
        video["collected_at"] = collected_at
        videos.append(video)
    return videos


def deduplicate_latest(videos: list[dict]) -> list[dict]:
    # mantem, por video_id, o registro coletado na execucao mais recente (metricas mais atuais)
    latest_by_id: dict[str, dict] = {}
    for video in videos:
        existing = latest_by_id.get(video["video_id"])
        if existing is None or video["collected_at"] >= existing["collected_at"]:
            latest_by_id[video["video_id"]] = video
    return list(latest_by_id.values())


def write_parquet(records: list[dict], path: Path) -> None:
    if not records:
        print(f"Nenhum registro para {path.name}, arquivo nao foi gerado.")
        return
    pd.DataFrame(records).to_parquet(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Filtra videos relevantes ao tema da eleicao.")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--videos-dir", type=Path, default=BRONZE_VIDEOS_DIR)
    input_group.add_argument("--videos-file", type=Path, help="JSON Bronze de uma execucao especifica")
    parser.add_argument("--relevance-file", type=Path, default=RELEVANCE_FILE)
    parser.add_argument("--output-dir", type=Path, default=SILVER_DIR)
    args = parser.parse_args()

    terms = parse_relevance_terms(args.relevance_file)
    source_videos = (
        load_bronze_video_file(args.videos_file)
        if args.videos_file
        else load_bronze_videos(args.videos_dir)
    )
    videos = deduplicate_latest(source_videos)

    relevantes = []
    descartados = []
    for video in videos:
        relevant, matched_terms = is_relevant(video["title"], video.get("description", ""), terms)
        record = {**video, "matched_terms": matched_terms}
        (relevantes if relevant else descartados).append(record)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_parquet(relevantes, args.output_dir / "videos_relevantes.parquet")
    write_parquet(descartados, args.output_dir / "videos_descartados.parquet")

    print(
        f"{len(videos)} videos unicos avaliados | "
        f"{len(relevantes)} relevantes | {len(descartados)} descartados"
    )


if __name__ == "__main__":
    main()
