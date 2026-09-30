"""Página inicial do Dashboard Streamlit."""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import PAGE_CONFIG, PROJECT_INFO
from utils.data_loader import (
    get_sentimentos_summary,
    load_candidatos,
    load_comentarios_enriched,
    render_run_selector,
)

# Configurar página
st.set_page_config(**PAGE_CONFIG)

# CSS customizado
st.markdown("""
    <style>
    .main {
        padding-top: 0rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Título
st.markdown(f"# {PROJECT_INFO['title']}")
st.markdown(f"*{PROJECT_INFO['subtitle']}*")
st.markdown("---")

# Carregar dados
try:
    run_id = render_run_selector()
    candidatos = load_candidatos(run_id)
    comentarios = load_comentarios_enriched(run_id)
except FileNotFoundError as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Verifique se os arquivos Gold foram gerados corretamente.")
    st.stop()

st.caption(f"Execução selecionada: {run_id}")

# Filtrar apenas dados de mídia para canais
comentarios_midia = comentarios[comentarios["category"] == "imprensa"].copy()

# KPIs principais
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Candidatos", value=len(candidatos))

with col2:
    st.metric(label="Comentários", value=f"{len(comentarios):,.0f}")

with col3:
    videos_total = comentarios["video_id"].nunique()
    st.metric(label="Vídeos", value=f"{videos_total:,.0f}")

with col4:
    canais_midia = comentarios_midia["channel_title"].nunique()
    st.metric(label="Canais de Mídia", value=canais_midia)

with col5:
    likes_total = comentarios["like_count"].sum() if "like_count" in comentarios.columns else 0
    st.metric(label="Likes Total", value=f"{likes_total:,.0f}")

st.markdown("---")

st.markdown("---")

# Seção: Distribuição de Sentimentos
st.subheader("Distribuição de Sentimentos")

sentimentos = get_sentimentos_summary(comentarios)
sentimentos_total = sum(sentimentos.values())

if sentimentos_total > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        pct_pos = (sentimentos["positivo"] / sentimentos_total * 100)
        st.metric("Positivos", f"{sentimentos['positivo']:,.0f}", f"{pct_pos:.1f}%")
    with col2:
        pct_neg = (sentimentos["negativo"] / sentimentos_total * 100)
        st.metric("Negativos", f"{sentimentos['negativo']:,.0f}", f"{pct_neg:.1f}%")
    with col3:
        pct_neu = (sentimentos["neutro"] / sentimentos_total * 100)
        st.metric("Neutros", f"{sentimentos['neutro']:,.0f}", f"{pct_neu:.1f}%")
else:
    st.info("Nenhum dado de sentimento disponível.")

st.markdown("---")

# Seção: Top Candidatos
st.subheader("Top 5 Candidatos por Engajamento")

top_candidatos = candidatos.head(5)[["candidato", "comentarios_total", "score_sentimento_medio"]]
if not top_candidatos.empty:
    st.dataframe(
        top_candidatos.rename(columns={
            "candidato": "Candidato",
            "comentarios_total": "Comentários",
            "score_sentimento_medio": "Score Sentimento Médio"
        }),
        use_container_width=True
    )
else:
    st.info("Nenhum dado de candidatos disponível.")

st.markdown("---")

# Seção: Top Canais de Mídia
st.subheader("Canais de Mídia por Engajamento")

# Calcular resumo por canal de mídia
canais_resumo = (
    comentarios_midia.groupby("channel_title").agg({
        "video_id": "count",  # Contar número de comentários
        "like_count": "sum"
    }).rename(columns={"video_id": "comentarios_total", "like_count": "likes_total"})
).reset_index()

canais_resumo = canais_resumo.sort_values("comentarios_total", ascending=False)

if not canais_resumo.empty:
    st.dataframe(
        canais_resumo.rename(columns={
            "channel_title": "Canal",
            "comentarios_total": "Comentários",
            "likes_total": "Likes Totais"
        }),
        use_container_width=True
    )
else:
    st.info("Nenhum dado de canais de mídia disponível.")

st.markdown("---")

# Navegação e informações
st.info(
    """
    **Use o menu lateral para explorar análises detalhadas:**
    
    1. **Análise de Sentimentos** - Distribuição, timeline e gráficos
    2. **Candidatos** - Ranking e performance por candidato
    3. **Canais de Mídia** - Engajamento por canal
    """
)

# Footer
st.markdown("---")
st.caption(f"Dashboard v{PROJECT_INFO['version']} | Dados extraídos da camada Gold")
