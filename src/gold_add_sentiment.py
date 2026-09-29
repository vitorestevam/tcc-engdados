#!/usr/bin/env python3
"""Adiciona análise de sentimento aos comentários da Silver e gera tabelas Gold."""

import argparse
from pathlib import Path

import pandas as pd

from silver.sentiment import add_sentiment_to_comments

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
INPUT_FILE = SILVER_DIR / "comments_silver.parquet"
OUTPUT_FILE = GOLD_DIR / "comments_with_sentiment.parquet"


def add_sentiment(
    input_file: Path | str = INPUT_FILE,
    output_file: Path | str = OUTPUT_FILE,
) -> None:
    input_file = Path(input_file)
    output_file = Path(output_file)
    enriched = add_sentiment_to_comments(pd.read_parquet(input_file))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_parquet(output_file, index=False)
    print(f"{len(enriched)} comentarios com sentimento gravados em {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Adiciona sentimento aos comentarios para a camada Gold.")
    parser.add_argument("--input-file", type=Path, default=INPUT_FILE)
    parser.add_argument("--output-file", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()
    add_sentiment(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
