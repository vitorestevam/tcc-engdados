"""Gera tabelas candidatos e temas para camada Gold."""

import logging
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_GOLD = PROJECT_ROOT / "data" / "gold"


def create_candidatos_table() -> pd.DataFrame:
    """Cria tabela de candidatos e manifestações."""
    LOGGER.info("Criando tabela de candidatos e manifestações...")
    
    videos_path = PROJECT_ROOT / "data" / "silver" / "videos_silver.parquet"
    comments_path = PROJECT_ROOT / "data" / "silver" / "comments_silver.parquet"
    
    df_videos = pd.read_parquet(videos_path)
    df_comments = pd.read_parquet(comments_path)
    
    # Expandir candidatos (transformar lista em múltiplas linhas)
    df_videos_expanded = df_videos.explode("candidatos_mencionados").reset_index(drop=True)
    
    # Agregar por candidato
    candidatos_agg = df_videos_expanded.groupby("candidatos_mencionados").agg({
        "video_id": "count",
        "like_count": "sum"
    }).reset_index()
    candidatos_agg.rename(columns={
        "candidatos_mencionados": "candidato",
        "video_id": "videos_total",
        "like_count": "likes_videos_total"
    }, inplace=True)
    
    # Contar comentários por candidato
    # Merge videos com comentários
    df_merged = df_videos[["video_id", "candidatos_mencionados"]].explode("candidatos_mencionados").reset_index(drop=True)
    df_merged = df_merged.merge(df_comments, on="video_id", how="left")
    
    # Agregar comentários por candidato
    comentarios_agg = df_merged.groupby("candidatos_mencionados").agg({
        "comment_id": "count",
        "like_count": "sum",
        "sentimento": lambda x: (x == "POSITIVO").sum(),
        "sentimento": lambda x: (x == "NEGATIVO").sum(),
        "score_sentimento": "mean"
    }).reset_index()
    
    # Função corrigida para sentimento
    def aggregate_sentiment(group):
        return pd.Series({
            "comentarios_total": len(group),
            "likes_comentarios_total": group["like_count"].sum(),
            "sentimento_positivo": (group["sentimento"] == "POSITIVO").sum(),
            "sentimento_negativo": (group["sentimento"] == "NEGATIVO").sum(),
            "sentimento_neutro": (group["sentimento"] == "NEUTRO").sum(),
            "score_sentimento_medio": group["score_sentimento"].mean()
        })
    
    comentarios_agg = df_merged.groupby("candidatos_mencionados").apply(aggregate_sentiment).reset_index()
    comentarios_agg.rename(columns={"candidatos_mencionados": "candidato"}, inplace=True)
    
    # Merge tabelas
    candidatos_table = candidatos_agg.merge(
        comentarios_agg,
        on="candidato",
        how="outer"
    )
    
    # Preencher NaNs
    candidatos_table = candidatos_table.fillna(0)
    
    # Calcular percentuais de sentimento
    candidatos_table["sentimento_positivo_pct"] = (
        candidatos_table["sentimento_positivo"] / candidatos_table["comentarios_total"] * 100
    ).round(2)
    candidatos_table["sentimento_negativo_pct"] = (
        candidatos_table["sentimento_negativo"] / candidatos_table["comentarios_total"] * 100
    ).round(2)
    candidatos_table["sentimento_neutro_pct"] = (
        candidatos_table["sentimento_neutro"] / candidatos_table["comentarios_total"] * 100
    ).round(2)
    
    # Ordenar por volume de comentários
    candidatos_table = candidatos_table.sort_values("comentarios_total", ascending=False).reset_index(drop=True)
    
    LOGGER.info(f"\nTabela de candidatos criada com {len(candidatos_table)} candidatos")
    LOGGER.info(f"\n{candidatos_table[['candidato', 'videos_total', 'comentarios_total', 'sentimento_positivo_pct']]}")
    
    return candidatos_table


def create_temas_table() -> pd.DataFrame:
    """Cria tabela de temas e engajamento."""
    LOGGER.info("\nCriando tabela de temas e engajamento...")
    
    # Usar channel_title como "tema" 
    # Em produção, isso seria gerado por classificação de temas
    
    videos_path = PROJECT_ROOT / "data" / "silver" / "videos_silver.parquet"
    comments_path = PROJECT_ROOT / "data" / "silver" / "comments_silver.parquet"
    
    df_videos = pd.read_parquet(videos_path)
    df_comments = pd.read_parquet(comments_path)
    
    # Usar channel_title como "tema"
    # Merge videos com comentários
    df_merged = df_videos[["video_id", "channel_title"]].merge(df_comments, on="video_id", how="left")
    
    # Agregar por tema (channel_title)
    def aggregate_tema(group):
        return pd.Series({
            "videos_total": group["video_id"].nunique(),
            "comentarios_total": len(group),
            "likes_media": group["like_count"].mean(),
            "sentimento_positivo": (group["sentimento"] == "POSITIVO").sum(),
            "sentimento_negativo": (group["sentimento"] == "NEGATIVO").sum(),
            "sentimento_neutro": (group["sentimento"] == "NEUTRO").sum(),
            "score_sentimento_medio": group["score_sentimento"].mean()
        })
    
    temas_table = df_merged.groupby("channel_title").apply(aggregate_tema).reset_index()
    temas_table.rename(columns={"channel_title": "tema"}, inplace=True)
    
    # Calcular percentuais
    temas_table["sentimento_positivo_pct"] = (
        temas_table["sentimento_positivo"] / temas_table["comentarios_total"] * 100
    ).round(2)
    temas_table["sentimento_negativo_pct"] = (
        temas_table["sentimento_negativo"] / temas_table["comentarios_total"] * 100
    ).round(2)
    
    # Ordenar por engajamento (comentários)
    temas_table = temas_table.sort_values("comentarios_total", ascending=False).reset_index(drop=True)
    
    LOGGER.info(f"\nTabela de temas criada com {len(temas_table)} temas")
    LOGGER.info(f"\n{temas_table[['tema', 'videos_total', 'comentarios_total', 'likes_media']]}")
    
    return temas_table


def main():
    """Orquestra criação das tabelas."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    DATA_GOLD.mkdir(parents=True, exist_ok=True)
    
    # Candidatos
    candidatos_df = create_candidatos_table()
    candidatos_df.to_parquet(DATA_GOLD / "candidatos_manifestacoes.parquet", index=False)
    LOGGER.info(f"✅ Candidatos salvos em {DATA_GOLD / 'candidatos_manifestacoes.parquet'}")
    
    # Temas
    temas_df = create_temas_table()
    temas_df.to_parquet(DATA_GOLD / "temas_engajamento.parquet", index=False)
    LOGGER.info(f"✅ Temas salvos em {DATA_GOLD / 'temas_engajamento.parquet'}")
    
    print("\n✅ Todas as tabelas Gold criadas!")


if __name__ == "__main__":
    main()
