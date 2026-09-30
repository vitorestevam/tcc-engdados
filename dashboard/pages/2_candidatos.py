"""Página: Análise por Candidato."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import load_candidatos, load_candidatos_timeline, load_comentarios_enriched
from config import SENTIMENT_COLORS, CANDIDATE_COLORS

# Função para anonimizar comentários
def anonimizar_comentario(texto):
    """Remove informações pessoais do comentário para privacidade."""
    if not isinstance(texto, str):
        return ""
    
    # Remover URLs
    texto = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', texto)
    
    # Remover emails
    texto = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', texto)
    
    # Remover @menções (nomes de usuário)
    texto = re.sub(r'@[a-zA-Z0-9_]+', '[MENÇÃO]', texto)
    
    # Remover números de telefone (padrão brasileiro)
    texto = re.sub(r'\(?(?:\d{2})?\s?9?\d{4}-?\d{4}', '[TELEFONE]', texto)
    
    return texto

st.set_page_config(page_title="Candidatos - Dashboard", layout="wide")

st.title("Análise por Candidato")

# Carregar dados
try:
    candidatos = load_candidatos()
    comentarios = load_comentarios_enriched()
except FileNotFoundError as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Resumo geral
st.subheader(f"Total de Candidatos Analisados: {len(candidatos)}")

st.markdown("---")

# Gráfico 1: Top 5 Candidatos por Engajamento com Distribuição de Sentimentos
st.subheader("Top 5 Candidatos por Engajamento (Distribuição de Sentimento)")

top_candidatos = candidatos.head(5)

fig_top = go.Figure()

for sentimento in ["sentimento_positivo", "sentimento_negativo", "sentimento_neutro"]:
    if sentimento in top_candidatos.columns:
        label = sentimento.replace("sentimento_", "").capitalize()
        cor = SENTIMENT_COLORS.get(label.upper(), "#95a5a6")
        fig_top.add_trace(go.Bar(
            name=label,
            x=top_candidatos["candidato"],
            y=top_candidatos[sentimento],
            marker_color=cor
        ))

fig_top.update_layout(
    barmode="group",
    height=400,
    xaxis_title="Candidato",
    yaxis_title="Número de Comentários",
    xaxis_tickangle=-45
)
st.plotly_chart(fig_top, use_container_width=True, key="fig_top_5_candidatos_engajamento")

st.markdown("---")

# Timeline de Sentimentos dos Candidatos
st.subheader("Evolução Temporal de Sentimentos - Candidatos")

candidatos_timeline = load_candidatos_timeline()

if not candidatos_timeline.empty:
    # Dropdown para selecionar candidato
    candidatos_unicos_lista = ["Todos os Candidatos"] + sorted(candidatos_timeline["candidato"].unique().tolist())
    candidato_selecionado_timeline = st.selectbox(
        "Filtrar por candidato:",
        candidatos_unicos_lista,
        key="candidato_timeline_filter"
    )
    
    # Criar gráfico de linha mostrando score_sentimento_medio ao longo do tempo
    fig_timeline = go.Figure()
    
    if candidato_selecionado_timeline == "Todos os Candidatos":
        # Mostrar todos os candidatos
        for candidato in sorted(candidatos_timeline["candidato"].unique()):
            df_cand = candidatos_timeline[candidatos_timeline["candidato"] == candidato].sort_values("data")
            
            # Obter cor do candidato, ou usar cor padrão se não existir mapeamento
            cor_candidato = CANDIDATE_COLORS.get(candidato, "#1f77b4")
            
            fig_timeline.add_trace(go.Scatter(
                x=df_cand["data"],
                y=df_cand["score_sentimento_medio"],
                mode="lines+markers",
                name=candidato,
                line=dict(width=2, color=cor_candidato)
            ))
    else:
        # Mostrar apenas o candidato selecionado
        df_cand = candidatos_timeline[candidatos_timeline["candidato"] == candidato_selecionado_timeline].sort_values("data")
        
        # Obter cor do candidato, ou usar cor padrão se não existir mapeamento
        cor_candidato = CANDIDATE_COLORS.get(candidato_selecionado_timeline, "#1f77b4")
        
        fig_timeline.add_trace(go.Scatter(
            x=df_cand["data"],
            y=df_cand["score_sentimento_medio"],
            mode="lines+markers",
            name=candidato_selecionado_timeline,
            line=dict(width=2, color=cor_candidato)
        ))
    
    # Adicionar linha de referência no 0
    fig_timeline.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig_timeline.update_layout(
        height=400,
        xaxis_title="Data",
        yaxis_title="Score Sentimento (-1 a +1)",
        hovermode="x unified",
        title=""
    )
    st.plotly_chart(fig_timeline, use_container_width=True, key="fig_timeline_candidatos_evolucao")
    
    # Legenda de cores dos candidatos
    st.markdown("**Legenda de Cores por Candidato:**")
    cols = st.columns(len(CANDIDATE_COLORS))
    for idx, (candidato, cor) in enumerate(CANDIDATE_COLORS.items()):
        with cols[idx]:
            st.markdown(f"<div style='display: flex; align-items: center;'><span style='display: inline-block; width: 20px; height: 20px; background-color: {cor}; margin-right: 10px; border-radius: 3px;'></span>{candidato}</div>", unsafe_allow_html=True)
    
    # Info box explicando o score
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("Score Sentimento: Varia de -1 (totalmente negativo) a +1 (totalmente positivo). 0 = balanceado")
else:
    st.info("Timeline de candidatos não disponível. Execute: python src/gold_enrich_datasets.py")

st.markdown("---")

# Seletor para colunas exibidas
default_cols = ["candidato", "videos_total", "comentarios_total", "score_sentimento_medio"]
available_cols = [col for col in default_cols if col in candidatos.columns]

df_display = candidatos[available_cols].copy()
df_display.columns = [col.replace("_", " ").title() for col in df_display.columns]

st.dataframe(df_display, use_container_width=True)

st.markdown("---")

# Detalhes por Candidato
st.subheader("Detalhes de um Candidato Específico")

candidato_selecionado = st.selectbox(
    "Escolha um candidato:",
    candidatos["candidato"].values,
    key="candidato_select"
)

if candidato_selecionado:
    dados_candidato = candidatos[candidatos["candidato"] == candidato_selecionado].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vídeos", int(dados_candidato.get("videos_total", 0)))
    with col2:
        st.metric("Comentários", int(dados_candidato.get("comentarios_total", 0)))
    with col3:
        st.metric("Score Sentimento", f"{dados_candidato.get('score_sentimento_medio', 0):.2f}")
    
    # Resumo de sentimentos
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Positivos", int(dados_candidato.get("sentimento_positivo", 0)))
    with col2:
        st.metric("Negativos", int(dados_candidato.get("sentimento_negativo", 0)))
    with col3:
        st.metric("Neutros", int(dados_candidato.get("sentimento_neutro", 0)))

st.markdown("---")

# Amostra de Comentários
st.subheader("Amostra de Comentários")

# Filtros
col1, col2, col3 = st.columns(3)

with col1:
    candidato_filtro = st.selectbox(
        "Filtrar por candidato:",
        ["Todos"] + sorted([c for c in comentarios["candidato"].unique() if c != "Não Mencionado"]),
        key="comentarios_candidato_filter"
    )

with col2:
    sentimento_filtro = st.selectbox(
        "Filtrar por sentimento:",
        ["Todos", "POSITIVO", "NEGATIVO", "NEUTRO"],
        key="comentarios_sentimento_filter"
    )

with col3:
    quantidade = st.number_input(
        "Número de comentários:",
        min_value=5,
        max_value=100,
        value=10,
        step=5,
        key="comentarios_quantidade"
    )

# Carregar comentários
try:
    df_comentarios_amostra = comentarios.copy()
    
    # Aplicar filtros
    if candidato_filtro != "Todos":
        df_comentarios_amostra = df_comentarios_amostra[df_comentarios_amostra["candidato"] == candidato_filtro]
    
    if sentimento_filtro != "Todos":
        df_comentarios_amostra = df_comentarios_amostra[df_comentarios_amostra["sentimento"] == sentimento_filtro]
    
    # Pegar amostra
    if len(df_comentarios_amostra) > 0:
        df_amostra = df_comentarios_amostra.sample(min(quantidade, len(df_comentarios_amostra)), random_state=42)
        
        # Criar coluna anonimizada
        colunas_texto = ["text_clean", "text", "comment_text"]
        col_texto = None
        for col in colunas_texto:
            if col in df_amostra.columns:
                col_texto = col
                break
        
        if col_texto:
            df_amostra = df_amostra.copy()
            df_amostra["text_anonimizado"] = df_amostra[col_texto].apply(anonimizar_comentario)
        
        # Definir colunas para exibição
        cols_exibir = []
        if "text_anonimizado" in df_amostra.columns:
            cols_exibir.append("text_anonimizado")
        if "author" in df_amostra.columns:
            cols_exibir.append("author")
        if "candidato" in df_amostra.columns:
            cols_exibir.append("candidato")
        if "sentimento" in df_amostra.columns:
            cols_exibir.append("sentimento")
        if "channel_title" in df_amostra.columns:
            cols_exibir.append("channel_title")
        
        if cols_exibir:
            # Renomear colunas
            renomeacao = {
                "text_anonimizado": "Comentário (Anonimizado)",
                "author": "Autor",
                "candidato": "Candidato",
                "sentimento": "Sentimento",
                "channel_title": "Canal"
            }
            
            df_exibir = df_amostra[cols_exibir].copy()
            df_exibir.columns = [renomeacao.get(col, col) for col in df_exibir.columns]
            
            st.dataframe(df_exibir, use_container_width=True, height=300)
            st.caption(f"Comentários anonimizados por privacidade | Mostrando {len(df_amostra)} de {len(df_comentarios_amostra)} comentários filtrados")
        else:
            st.info("Nenhuma coluna compatível encontrada para exibição.")
    else:
        st.info(f"Nenhum comentário encontrado com os filtros selecionados.")
        
except Exception as e:
    st.error(f"Erro ao carregar comentários: {e}")
    st.info("Certifique-se de que o arquivo comentarios_gold_enriched.parquet foi gerado executando: python src/gold_enrich_datasets.py")

st.markdown("---")
