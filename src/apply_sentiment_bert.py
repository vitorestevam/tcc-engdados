"""Script para aplicar análise BERT de sentimento aos comentários processados."""

import logging
import os
from pathlib import Path

import pandas as pd

from src.silver.sentiment_bert import add_sentiment_bert_to_comments

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def apply_bert_sentiment_to_comments(
    comments_file: str = None,
    output_file: str = None,
    use_bert: bool = True
) -> str:
    """
    Aplica análise BERT de sentimento aos comentários Silver.
    
    Args:
        comments_file: Caminho do arquivo parquet de comentários Silver
        output_file: Caminho de saída (opcional, sobrescreve entrada se None)
        use_bert: Se True, usa BERT; se False, usa análise simplista
        
    Returns:
        Caminho do arquivo de saída
    """
    # Definir caminhos padrão
    if comments_file is None:
        silver_dir = Path("data/silver")
        if not silver_dir.exists():
            raise FileNotFoundError(f"Diretório {silver_dir} não encontrado")
        
        # Procurar arquivo de comentários
        comment_files = list(silver_dir.glob("comments_silver*.parquet"))
        if not comment_files:
            raise FileNotFoundError(f"Nenhum arquivo comments_silver*.parquet encontrado em {silver_dir}")
        
        comments_file = str(comment_files[0])  # Usar o mais recente
    
    if output_file is None:
        output_file = comments_file
    
    LOGGER.info(f"Carregando comentários de: {comments_file}")
    df = pd.read_parquet(comments_file)
    
    LOGGER.info(f"Total de comentários: {len(df)}")
    
    # Aplicar análise BERT
    df = add_sentiment_bert_to_comments(df, use_bert=use_bert)
    
    # Salvar resultado
    LOGGER.info(f"Salvando resultado em: {output_file}")
    df.to_parquet(output_file, engine="pyarrow", compression="snappy")
    
    LOGGER.info(f"✓ Análise BERT concluída! Arquivo salvo em: {output_file}")
    
    return output_file


def generate_emotion_tables(comments_file: str = None) -> tuple[str, str]:
    """
    Gera tabelas GOLD de análise de emoções.
    
    Args:
        comments_file: Caminho do arquivo parquet de comentários com BERT
        
    Returns:
        Tupla (arquivo_emocoes_distribuicao, arquivo_candidatos_emocoes)
    """
    # Definir caminhos
    if comments_file is None:
        silver_dir = Path("data/silver")
        comment_files = list(silver_dir.glob("comments_silver*.parquet"))
        if not comment_files:
            raise FileNotFoundError("Nenhum arquivo de comentários encontrado")
        comments_file = str(comment_files[0])
    
    gold_dir = Path("data/gold")
    gold_dir.mkdir(parents=True, exist_ok=True)
    
    LOGGER.info(f"Carregando comentários com BERT: {comments_file}")
    df_comments = pd.read_parquet(comments_file)
    
    # 1. Distribuição de emoções
    LOGGER.info("Gerando tabela: emocoes_distribuicao.parquet")
    emotion_dist = df_comments["emocao"].value_counts().reset_index()
    emotion_dist.columns = ["emocao", "total"]
    emotion_dist["pct"] = (emotion_dist["total"] / emotion_dist["total"].sum() * 100).round(2)
    
    emotion_file = str(gold_dir / "emocoes_distribuicao.parquet")
    emotion_dist.to_parquet(emotion_file, engine="pyarrow", compression="snappy")
    LOGGER.info(f"✓ Salvo em: {emotion_file}")
    
    # 2. Candidatos x Emoções
    LOGGER.info("Gerando tabela: candidatos_emocoes.parquet")
    
    # Precisamos dos vídeos para ter a info de candidatos
    video_files = list(Path("data/silver").glob("videos_silver*.parquet"))
    if not video_files:
        LOGGER.warning("Arquivo de vídeos não encontrado, pulando candidatos_emocoes")
        return emotion_file, None
    
    df_videos = pd.read_parquet(video_files[0])
    
    # Mesclar comentários com vídeos para ter candidatos
    df_merged = df_comments.merge(
        df_videos[["video_id", "candidatos_mencionados"]],
        on="video_id",
        how="left"
    )
    
    # Explodir candidatos_mencionados
    df_merged = df_merged.explode("candidatos_mencionados")
    df_merged = df_merged.rename(columns={"candidatos_mencionados": "candidato"})
    
    # Agrupar por candidato e emoção
    candidato_emocoes = df_merged.groupby(["candidato", "emocao"]).size().reset_index(name="total")
    candidato_emocoes = candidato_emocoes.pivot_table(
        index="candidato",
        columns="emocao",
        values="total",
        fill_value=0
    )
    
    candidato_file = str(gold_dir / "candidatos_emocoes.parquet")
    candidato_emocoes.to_parquet(candidato_file, engine="pyarrow", compression="snappy")
    LOGGER.info(f"✓ Salvo em: {candidato_file}")
    
    return emotion_file, candidato_file


if __name__ == "__main__":
    import sys
    
    LOGGER.info("=" * 70)
    LOGGER.info("PIPELINE: Análise BERT de Sentimento e Emoções")
    LOGGER.info("=" * 70)
    
    try:
        # Etapa 1: Aplicar BERT
        LOGGER.info("\nEtapa 1: Aplicando análise BERT aos comentários...")
        comments_output = apply_bert_sentiment_to_comments()
        
        # Etapa 2: Gerar tabelas GOLD
        LOGGER.info("\nEtapa 2: Gerando tabelas GOLD de emoções...")
        emotion_file, candidato_file = generate_emotion_tables(comments_output)
        
        LOGGER.info("\n" + "=" * 70)
        LOGGER.info("✓ Pipeline BERT concluído com sucesso!")
        LOGGER.info("=" * 70)
        LOGGER.info(f"\nArquivos gerados:")
        LOGGER.info(f"  - Comentários com BERT: {comments_output}")
        LOGGER.info(f"  - Distribuição de emoções: {emotion_file}")
        if candidato_file:
            LOGGER.info(f"  - Candidatos x emoções: {candidato_file}")
        
    except Exception as e:
        LOGGER.error(f"Erro ao executar pipeline: {e}", exc_info=True)
        sys.exit(1)
