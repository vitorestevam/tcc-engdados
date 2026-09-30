"""Página: Análise por Canal."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import load_comentarios_enriched, load_canais_timeline
from config import SENTIMENT_COLORS

st.set_page_config(page_title="Canais - Dashboard", layout="wide")

st.title("Análise por Canal de Mídia")

# Carregar dados
try:
    comentarios = load_comentarios_enriched()
    canais_timeline = load_canais_timeline()
except FileNotFoundError as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Filtrar apenas comentários de mídia (imprensa)
comentarios_midia = comentarios[comentarios["category"] == "imprensa"].copy()

# Calcular resumo por canal - fazendo agregações separadas
canais_resumo = comentarios_midia.groupby("channel_title").agg({
    "video_id": "nunique",
    "comment_id": "count",
    "like_count": "sum"
}).reset_index()

canais_resumo.columns = ["canal", "videos_total", "comentarios_total", "likes_total"]

# Calcular sentimentos por canal
sentimentos_por_canal = []
for canal in comentarios_midia["channel_title"].unique():
    canal_data = comentarios_midia[comentarios_midia["channel_title"] == canal]
    sentimentos_por_canal.append({
        "canal": canal,
        "sentimento_positivo": (canal_data["sentimento"] == "POSITIVO").sum(),
        "sentimento_negativo": (canal_data["sentimento"] == "NEGATIVO").sum(),
        "sentimento_neutro": (canal_data["sentimento"] == "NEUTRO").sum()
    })

sentimentos_df = pd.DataFrame(sentimentos_por_canal)

# Fazer merge
canais_resumo = canais_resumo.merge(sentimentos_df, on="canal", how="left")

# Ordenar por engajamento
canais_resumo = canais_resumo.sort_values("comentarios_total", ascending=False)

# Resumo geral
st.subheader(f"Total de Canais de Mídia Analisados: {len(canais_resumo)}")

st.markdown("---")

# Gráfico 1: Vídeos vs Comentários
st.subheader("Relação: Vídeos Publicados vs Comentários Recebidos")

if not canais_resumo.empty:
    fig_scatter = px.scatter(
        canais_resumo,
        x="videos_total",
        y="comentarios_total",
        size="comentarios_total",
        hover_name="canal",
        labels={"videos_total": "Vídeos Publicados", "comentarios_total": "Comentários", "canal": "Canal"},
        size_max=60
    )
    fig_scatter.update_layout(height=450)
    st.plotly_chart(fig_scatter, use_container_width=True, key="fig_scatter_videos_comentarios")
else:
    st.info("Nenhum dado de mídia disponível.")

st.markdown("---")

# Gráfico 3: Distribuição de Sentimentos por Canal
st.subheader("Distribuição de Sentimentos por Canal")

if not canais_resumo.empty:
    fig_sent = go.Figure()
    
    for sentimento in ["sentimento_positivo", "sentimento_negativo", "sentimento_neutro"]:
        if sentimento in canais_resumo.columns:
            label = sentimento.replace("sentimento_", "").upper()
            cor = SENTIMENT_COLORS.get(label, "#95a5a6")
            fig_sent.add_trace(go.Bar(
                name=label,
                x=canais_resumo["canal"],
                y=canais_resumo[sentimento],
                marker_color=cor
            ))
    
    fig_sent.update_layout(
        barmode="stack",
        height=400,
        xaxis_title="Canal",
        yaxis_title="Número de Comentários",
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_sent, use_container_width=True, key="fig_sentimentos_canais")

st.markdown("---")

# Gráfico 3: Timeline de Sentimentos por Canal
st.subheader("Evolução Temporal de Sentimentos por Canal")

if not canais_timeline.empty:
    # Dropdown para selecionar canal (sem "Todos os Canais" para manter legenda clara)
    canais_unicos = sorted(canais_timeline["tema"].unique().tolist())
    canal_selecionado = st.selectbox(
        "Filtrar por canal:",
        canais_unicos,
        key="canal_timeline_filter"
    )
    
    # Criar gráfico de linha
    fig_timeline = go.Figure()
    
    df_canal = canais_timeline[canais_timeline["tema"] == canal_selecionado].sort_values("data")
    
    fig_timeline.add_trace(go.Scatter(
        x=df_canal["data"],
        y=df_canal["sentimento_positivo"],
        mode="lines+markers",
        name=f"{canal_selecionado} (Positivos)",
        line=dict(color=SENTIMENT_COLORS["POSITIVO"], width=2)
    ))
    
    fig_timeline.add_trace(go.Scatter(
        x=df_canal["data"],
        y=df_canal["sentimento_negativo"],
        mode="lines+markers",
        name=f"{canal_selecionado} (Negativos)",
        line=dict(color=SENTIMENT_COLORS["NEGATIVO"], width=2, dash="dash")
    ))
    
    fig_timeline.update_layout(
        height=400,
        xaxis_title="Data",
        yaxis_title="Comentários",
        hovermode="x unified"
    )
    st.plotly_chart(fig_timeline, use_container_width=True, key="fig_timeline_canais")
else:
    st.info("Timeline não disponível.")

st.markdown("---")

# Tabela Completa de Canais
st.subheader("Tabela Completa de Canais de Mídia")

if not canais_resumo.empty:
    cols_display = ["canal", "videos_total", "comentarios_total", "likes_total", "sentimento_positivo", "sentimento_negativo", "sentimento_neutro"]
    cols_display = [col for col in cols_display if col in canais_resumo.columns]
    
    df_display = canais_resumo[cols_display].copy()
    df_display.columns = ["Canal", "Vídeos", "Comentários", "Likes Total", "Positivos", "Negativos", "Neutros"]
    
    st.dataframe(df_display, use_container_width=True)

st.markdown("---")

# Detalhes de um Canal
st.subheader("Detalhes de um Canal Específico")

if not canais_resumo.empty:
    canal_selecionado = st.selectbox(
        "Escolha um canal:",
        canais_resumo["canal"].values,
        key="canal_details_select"
    )
    
    if canal_selecionado:
        dados_canal = canais_resumo[canais_resumo["canal"] == canal_selecionado].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Vídeos Publicados", int(dados_canal["videos_total"]))
        with col2:
            st.metric("Comentários Recebidos", int(dados_canal["comentarios_total"]))
        with col3:
            st.metric("Likes Totais", int(dados_canal["likes_total"]))
        
        # Sentimentos
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Positivos", int(dados_canal["sentimento_positivo"]))
        with col2:
            st.metric("Negativos", int(dados_canal["sentimento_negativo"]))
        with col3:
            st.metric("Neutros", int(dados_canal["sentimento_neutro"]))

st.markdown("---")
st.caption("Dashboard de análise por canal de mídia | Dados da camada Gold")
