"""Série temporal de volume para a camada Gold."""

import logging
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/gold/... -> sobe 2 níveis para raiz
DATA_GOLD = PROJECT_ROOT / "data" / "gold"


def create_temporal_series() -> pd.DataFrame:
    """
    Cria série temporal de volume diário.
    
    Pergunta respondida: "Como o volume de manifestações evoluiu no tempo?"
    
    Aggregação:
    - Por data de publicação dos vídeos
    - Por data de criação dos comentários
    
    Returns:
        DataFrame com colunas:
        - data: date (formato YYYY-MM-DD)
        - videos_novos: int (quantidade de vídeos publicados)
        - comentarios_novos: int (quantidade de comentários postados)
        - likes_total: int (soma de likes dos comentários)
        - engajamento_medio: float (média de comentários por vídeo)
        - sentimento_medio: float (score médio de sentimento)
    """
    LOGGER.info("Criando série temporal de volume...")
    
    # Carregar dados Silver
    videos_path = PROJECT_ROOT / "data" / "silver" / "videos_silver.parquet"
    comments_path = PROJECT_ROOT / "data" / "silver" / "comments_silver.parquet"
    
    if not videos_path.exists() or not comments_path.exists():
        raise FileNotFoundError(f"Arquivos Silver não encontrados em {PROJECT_ROOT / 'data' / 'silver'}")
    
    df_videos = pd.read_parquet(videos_path)
    df_comments = pd.read_parquet(comments_path)
    
    LOGGER.info(f"Videos carregados: {len(df_videos)}")
    LOGGER.info(f"Comentários carregados: {len(df_comments)}")
    
    # Converter datas para formato datetime se necessário
    df_videos["published_at"] = pd.to_datetime(df_videos["published_at"], utc=True)
    df_comments["published_at"] = pd.to_datetime(df_comments["published_at"], utc=True)
    
    # Extrair apenas a data (sem hora)
    df_videos["data"] = df_videos["published_at"].dt.date
    df_comments["data"] = df_comments["published_at"].dt.date
    
    # Agregação por data
    videos_by_date = df_videos.groupby("data").size().reset_index(name="videos_novos")
    
    comments_by_date = df_comments.groupby("data").agg({
        "like_count": "sum",
        "comment_id": "count"  # Contar comentários
    }).reset_index()
    comments_by_date.rename(columns={"like_count": "likes_total", "comment_id": "comentarios_novos"}, inplace=True)
    
    # Calcular sentimento médio por data (se coluna existir)
    if "score_sentimento" in df_comments.columns:
        sentimento_by_date = df_comments.groupby("data")["score_sentimento"].mean().reset_index(name="sentimento_medio")
    else:
        LOGGER.warning("Coluna 'score_sentimento' não encontrada. Sentimento não será incluído.")
        sentimento_by_date = None
    
    # Calcular engajamento médio por data
    # Engajamento = comentários que mencionam cada vídeo
    videos_by_date_count = df_videos.groupby("data").size().reset_index(name="videos_por_data")
    comments_by_date_count = df_comments.groupby("data").size().reset_index(name="comentarios_por_data")
    
    engajamento = videos_by_date_count.merge(comments_by_date_count, on="data", how="outer")
    engajamento["engajamento_medio"] = engajamento["comentarios_por_data"] / engajamento["videos_por_data"]
    engajamento = engajamento[["data", "engajamento_medio"]]
    
    # Fazer merge de todas as agregações
    temporal_df = videos_by_date.merge(comments_by_date, on="data", how="outer")
    temporal_df = temporal_df.merge(engajamento, on="data", how="outer")
    
    if sentimento_by_date is not None:
        temporal_df = temporal_df.merge(sentimento_by_date, on="data", how="outer")
    
    # Preencher NaNs com 0 (datas sem dados)
    temporal_df["videos_novos"] = temporal_df["videos_novos"].fillna(0).astype(int)
    temporal_df["comentarios_novos"] = temporal_df["comentarios_novos"].fillna(0).astype(int)
    temporal_df["likes_total"] = temporal_df["likes_total"].fillna(0).astype(int)
    temporal_df["engajamento_medio"] = temporal_df["engajamento_medio"].fillna(0.0)
    
    if "sentimento_medio" in temporal_df.columns:
        temporal_df["sentimento_medio"] = temporal_df["sentimento_medio"].fillna(0.0)
    
    # Converter data para datetime
    temporal_df["data"] = pd.to_datetime(temporal_df["data"])
    
    # Ordenar por data
    temporal_df = temporal_df.sort_values("data").reset_index(drop=True)
    
    LOGGER.info(f"Série temporal criada com {len(temporal_df)} dias")
    LOGGER.info(f"\nResumo da série temporal:")
    LOGGER.info(f"Período: {temporal_df['data'].min()} até {temporal_df['data'].max()}")
    LOGGER.info(f"Total de vídeos: {temporal_df['videos_novos'].sum()}")
    LOGGER.info(f"Total de comentários: {temporal_df['comentarios_novos'].sum()}")
    LOGGER.info(f"Total de likes: {temporal_df['likes_total'].sum()}")
    
    return temporal_df


def save_temporal_series(df: pd.DataFrame):
    """
    Salva série temporal em parquet.
    
    Args:
        df: DataFrame da série temporal
    """
    DATA_GOLD.mkdir(parents=True, exist_ok=True)
    
    output_path = DATA_GOLD / "serie_temporal_volume.parquet"
    df.to_parquet(output_path, index=False)
    
    LOGGER.info(f"Série temporal salva em {output_path}")


def main():
    """Orquestra a criação da série temporal."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    temporal_df = create_temporal_series()
    save_temporal_series(temporal_df)
    
    print("\n✅ Série temporal criada com sucesso!")
    print(f"\nPrimeiras linhas:\n{temporal_df.head()}")


if __name__ == "__main__":
    main()
