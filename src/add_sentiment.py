#!/usr/bin/env python3
"""Adiciona análise de sentimento aos comentários da Silver e gera tabelas Gold."""

import logging
from pathlib import Path

import pandas as pd

from silver.sentiment import add_sentiment_to_comments

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def add_sentiment_to_silver():
    """
    Carrega comentários Silver, adiciona sentimento e salva de volta.
    """
    LOGGER.info("Adicionando sentimento aos comentários Silver...")
    
    comments_path = PROJECT_ROOT / "data" / "silver" / "comments_silver.parquet"
    
    df_comments = pd.read_parquet(comments_path)
    LOGGER.info(f"Comentários carregados: {len(df_comments)}")
    
    # Adicionar sentimento
    df_comments = add_sentiment_to_comments(df_comments)
    
    
    # Salvar de volta
    df_comments.to_parquet(comments_path, index=False)
    LOGGER.info(f"Comentários com sentimento salvos em {comments_path}")
    
    return df_comments


def main():
    """Orquestra adição de sentimento."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    df_comments = add_sentiment_to_silver()
    
    print("\n✅ Sentimento adicionado com sucesso!")
    print(f"\nAmostra de dados com sentimento:\n{df_comments[['text_clean', 'sentimento', 'score_sentimento']].head(10)}")


if __name__ == "__main__":
    main()
