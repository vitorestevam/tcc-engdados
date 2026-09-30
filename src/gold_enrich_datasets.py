"""
Gold Layer Enrichment Script
=========================================
Cria tabelas temporais para análises Time-Series no dashboard.

Diferencia:
- CANDIDATOS: Apenas canais com category="candidato" em channels.json
- CANAIS/MÍDIA: Apenas canais com category="imprensa" em channels.json

Tabelas geradas:
1. comentarios_gold_enriched.parquet - Comentários com candidato/canal e categoria
2. candidatos_timeline.parquet - Timeline APENAS de CANDIDATOS
3. canais_timeline.parquet - Timeline APENAS de CANAIS/MÍDIA
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# Configuração de caminhos
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
GOLD_DIR = DATA_DIR / "gold"
SILVER_DIR = DATA_DIR / "silver"
SETTINGS_DIR = PROJECT_ROOT / "settings"

print("Iniciando Enrichment da Camada Gold (CORRIGIDO)...")
print(f"Project Root: {PROJECT_ROOT}")

# ============================================================================
# 1. CARREGAR CONFIGURAÇÕES E DADOS
# ============================================================================
print("\nCarregando dados e configurações...")

# Carregar channels.json para saber quem é candidato/mídia
try:
    with open(SETTINGS_DIR / "channels.json", "r", encoding="utf-8") as f:
        channels_config = json.load(f)["channels"]
    
    # Criar mapa: channel_name -> category
    channel_category_map = {ch["source"]: ch["category"] for ch in channels_config}
    candidatos_oficiais = [ch["source"] for ch in channels_config if ch["category"] == "candidato"]
    midia_oficial = [ch["source"] for ch in channels_config if ch["category"] == "imprensa"]
    
    print("Canais carregados de settings/channels.json")
    print(f"   - Candidatos: {candidatos_oficiais}")
    print(f"   - Mídia: {midia_oficial}")
except Exception as e:
    print(f"Erro ao carregar channels.json: {e}")
    exit(1)

# Carregar dados Gold e Silver
try:
    comments_sentiment = pd.read_parquet(GOLD_DIR / "comments_with_sentiment.parquet")
    print(f"Comentários com sentimento: {len(comments_sentiment)} linhas")
    
    videos = pd.read_parquet(SILVER_DIR / "videos_silver.parquet")
    print(f"Vídeos: {len(videos)} linhas")
    
except FileNotFoundError as e:
    print(f"Erro ao carregar arquivos: {e}")
    exit(1)

# ============================================================================
# 2. ENRIQUECER COMENTÁRIOS COM CANDIDATO, CANAL E CATEGORIA
# ============================================================================
print("\nEnriquecendo comentários...")

# Fazer merge de vídeos com comentários
videos_minimal = videos[["video_id", "channel_title", "candidatos_mencionados"]]

comentarios_enriched = comments_sentiment.merge(
    videos_minimal,
    on="video_id",
    how="left"
)

# Determinar categoria baseada em channel_title
comentarios_enriched["category"] = comentarios_enriched["channel_title"].apply(
    lambda x: channel_category_map.get(x, "desconhecido") if pd.notna(x) else "desconhecido"
)

# Determinar candidato mencionado
# Se o canal é um candidato → esse candidato
# Se é mídia → verificar candidatos_mencionados
def get_candidato(row):
    channel = row["channel_title"]
    mencionados = row["candidatos_mencionados"]
    
    # Se o próprio canal é um candidato
    if channel in candidatos_oficiais:
        return channel
    
    # Se é mídia, procurar candidatos mencionados
    if isinstance(mencionados, list) and len(mencionados) > 0:
        # Retornar o primeiro candidato mencionado
        return mencionados[0]
    
    # Se nenhum candidato encontrado
    return "Não Mencionado"

comentarios_enriched["candidato"] = comentarios_enriched.apply(get_candidato, axis=1)

# Validação
print(f"Enriquecimento concluído:")
print(f"   - Total de comentários: {len(comentarios_enriched)}")
print(f"   - Candidatos únicos: {comentarios_enriched['candidato'].nunique()}")
print(f"   - Canais únicos: {comentarios_enriched['channel_title'].nunique()}")
print(f"   - Distribuição por categoria:")
print(f"     - Candidatos: {(comentarios_enriched['category'] == 'candidato').sum()}")
print(f"     - Mídia: {(comentarios_enriched['category'] == 'imprensa').sum()}")
# Salvar comentários enriquecidos
output_file = GOLD_DIR / "comentarios_gold_enriched.parquet"
comentarios_enriched.to_parquet(output_file, index=False)
print(f"\nSalvo: {output_file}")

# ============================================================================
# 3. CRIAR TIMELINE CANDIDATOS (APENAS CANDIDATOS)
# ============================================================================
print("\nCriando timeline de candidatos...")

# Filtrar apenas comentários de CANDIDATOS
df_cand = comentarios_enriched[comentarios_enriched["category"] == "candidato"].copy()

if len(df_cand) > 0:
    df_cand["published_at"] = pd.to_datetime(df_cand["published_at"], utc=True)
    df_cand["data"] = df_cand["published_at"].dt.date
    df_cand["semana"] = df_cand["published_at"].dt.to_period("W")
    df_cand["mes"] = df_cand["published_at"].dt.to_period("M")
    
    # Agregar por candidato/data
    candidatos_timeline = (
        df_cand
        .groupby(["candidato", "data", "semana", "mes"])
        .agg({
            "sentimento": [
                lambda x: (x == "POSITIVO").sum(),
                lambda x: (x == "NEGATIVO").sum(),
                lambda x: (x == "NEUTRO").sum(),
                "count"
            ],
            "score_sentimento": "mean",
            "score_emocao": "mean",
            "emocao": lambda x: (x == "ENTUSIASMO").sum(),
            "like_count": ["sum", "mean"]
        })
        .reset_index()
    )
    
    # Renomear colunas
    candidatos_timeline.columns = [
        "candidato", "data", "semana", "mes",
        "sentimento_positivo", "sentimento_negativo", "sentimento_neutro", "total_comentarios",
        "score_sentimento_medio", "score_emocao_medio",
        "emocao_entusiasmo",
        "likes_total", "likes_media"
    ]
    
    # Calcular percentuais
    candidatos_timeline["sentimento_positivo_pct"] = (
        (candidatos_timeline["sentimento_positivo"] / candidatos_timeline["total_comentarios"] * 100).round(2)
    )
    candidatos_timeline["sentimento_negativo_pct"] = (
        (candidatos_timeline["sentimento_negativo"] / candidatos_timeline["total_comentarios"] * 100).round(2)
    )
    
    # Ordenar
    candidatos_timeline = candidatos_timeline.sort_values(["candidato", "data"], ascending=[True, False])
    
    output_file = GOLD_DIR / "candidatos_timeline.parquet"
    candidatos_timeline.to_parquet(output_file, index=False)
    print(f"Timeline Candidatos: {len(candidatos_timeline)} registros")
    print(f"   - Candidatos: {candidatos_timeline['candidato'].unique().tolist()}")
    print(f"Salvo: {output_file}")
else:
    print(f"Aviso: Nenhum comentário de candidatos encontrado!")

# ============================================================================
# 4. CRIAR TIMELINE CANAIS/MÍDIA (APENAS MÍDIA)
# ============================================================================
print("\nCriando timeline de canais/mídia...")

# Filtrar apenas comentários de MÍDIA
df_media = comentarios_enriched[comentarios_enriched["category"] == "imprensa"].copy()

if len(df_media) > 0:
    df_media["published_at"] = pd.to_datetime(df_media["published_at"], utc=True)
    df_media["data"] = df_media["published_at"].dt.date
    df_media["semana"] = df_media["published_at"].dt.to_period("W")
    df_media["mes"] = df_media["published_at"].dt.to_period("M")
    
    # Agregar por canal/data
    canais_timeline = (
        df_media
        .groupby(["channel_title", "data", "semana", "mes"])
        .agg({
            "sentimento": [
                lambda x: (x == "POSITIVO").sum(),
                lambda x: (x == "NEGATIVO").sum(),
                lambda x: (x == "NEUTRO").sum(),
                "count"
            ],
            "score_sentimento": "mean",
            "score_emocao": "mean",
            "like_count": ["sum", "mean"],
            "video_id": "nunique"
        })
        .reset_index()
    )
    
    # Renomear colunas
    canais_timeline.columns = [
        "tema", "data", "semana", "mes",
        "sentimento_positivo", "sentimento_negativo", "sentimento_neutro", "total_comentarios",
        "score_sentimento_medio", "score_emocao_medio",
        "likes_total", "likes_media",
        "videos_distintos"
    ]
    
    # Calcular percentuais
    canais_timeline["sentimento_positivo_pct"] = (
        (canais_timeline["sentimento_positivo"] / canais_timeline["total_comentarios"] * 100).round(2)
    )
    canais_timeline["sentimento_negativo_pct"] = (
        (canais_timeline["sentimento_negativo"] / canais_timeline["total_comentarios"] * 100).round(2)
    )
    
    # Ordenar
    canais_timeline = canais_timeline.sort_values(["tema", "data"], ascending=[True, False])
    
    output_file = GOLD_DIR / "canais_timeline.parquet"
    canais_timeline.to_parquet(output_file, index=False)
    print(f"Timeline Canais/Mídia: {len(canais_timeline)} registros")
    print(f"   - Canais: {canais_timeline['tema'].unique().tolist()}")
    print(f"Salvo: {output_file}")
else:
    print(f"Aviso: Nenhum comentário de mídia encontrado!")

# ============================================================================
# 5. RESUMO FINAL
# ============================================================================
print("\n" + "="*70)
print("✅ ENRICHMENT CONCLUÍDO COM SUCESSO!")
print("="*70)

print("\n📊 RESUMO:")
print(f"  • comentarios_gold_enriched.parquet: {len(comentarios_enriched)} linhas")
print(f"    - Candidatos únicos: {comentarios_enriched[comentarios_enriched['category'] == 'candidato']['candidato'].nunique()}")
print(f"    - Canais/Mídia únicos: {comentarios_enriched[comentarios_enriched['category'] == 'imprensa']['channel_title'].nunique()}")

if 'candidatos_timeline' in locals():
    print(f"  - candidatos_timeline.parquet: {len(candidatos_timeline)} registros")
    print(f"    - Data range: {candidatos_timeline['data'].min()} a {candidatos_timeline['data'].max()}")

if 'canais_timeline' in locals():
    print(f"  - canais_timeline.parquet: {len(canais_timeline)} registros")
    print(f"    - Data range: {canais_timeline['data'].min()} a {canais_timeline['data'].max()}")

print("\nSEPARAÇÃO CORRETA:")
print(f"  - Candidatos: APENAS {candidatos_oficiais}")
print(f"  - Mídia: APENAS {midia_oficial}")
print(f"  - Mídia NÃO aparecerá como candidato!")

print(f"\nÚltima atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
