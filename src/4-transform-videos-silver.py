#!/usr/bin/env python3
"""Limpa e padroniza os videos ja filtrados como relevantes (Etapa 2 da Silver).

Classificacao por tema e agregacoes ficam para a camada Gold.
"""

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from silver.cleaning import clean_text
from silver.relevance import RELEVANCE_FILE, parse_relevance_terms

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SILVER_DIR = PROJECT_ROOT.parent / "data" / "silver"
INPUT_FILE = SILVER_DIR / "videos_relevantes.parquet"
OUTPUT_FILE = SILVER_DIR / "videos_silver.parquet"

OUTPUT_COLUMNS = [
    "video_id",
    "channel_id",
    "channel_title",
    "source",
    "category",
    "title_clean",
    "description_clean",
    "published_at",
    "view_count",
    "like_count",
    "comment_count",
    "privacy_status",
    "candidatos_mencionados",
    "source_file",
    "processed_at",
]


def build_candidate_lookup(terms: list[dict[str, str]]) -> dict[str, str]:
    # mapeia o termo (ja usado na Etapa 1) para o rotulo do candidato/vice correspondente
    return {term["termo"]: term["rotulo"] for term in terms if term["tipo"] in {"candidato", "vice"}}


def candidatos_mencionados(matched_terms, lookup: dict[str, str]) -> list[str]:
    return sorted({lookup[termo] for termo in matched_terms if termo in lookup})


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpa e padroniza os videos relevantes (camada Silver).")
    parser.add_argument("--input-file", type=Path, default=INPUT_FILE)
    parser.add_argument("--relevance-file", type=Path, default=RELEVANCE_FILE)
    parser.add_argument("--output-file", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()

    df = pd.read_parquet(args.input_file)
    relevance_terms = parse_relevance_terms(args.relevance_file)
    candidate_lookup = build_candidate_lookup(relevance_terms)

    df["title_clean"] = df["title"].apply(clean_text)
    df["description_clean"] = df["description"].apply(clean_text)
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
    df["candidatos_mencionados"] = df["matched_terms"].apply(
        lambda terms: candidatos_mencionados(terms, candidate_lookup)
    )
    df["processed_at"] = datetime.now(UTC)

    silver_df = df[OUTPUT_COLUMNS].drop_duplicates(subset="video_id", keep="last")

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    silver_df.to_parquet(args.output_file, index=False)
    print(f"{len(silver_df)} videos gravados em {args.output_file}")


if __name__ == "__main__":
    main()
