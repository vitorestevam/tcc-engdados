"""Página: Análise Detalhada de Sentimentos."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_loader import load_comentarios, get_sentimentos_summary
from config import SENTIMENT_COLORS

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
    texto = re.sub(r'\(\d{2}\)\s*\d{4,5}-\d{4}', '[TELEFONE]', texto)
    texto = re.sub(r'\d{2}\s*\d{4,5}-\d{4}', '[TELEFONE]', texto)
    
    # Remover números que parecem CPF
    texto = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', '[CPF]', texto)
    
    return texto

st.set_page_config(page_title="Sentimentos - Dashboard", layout="wide")

st.title("Análise Detalhada de Sentimentos")

# Carregar dados
try:
    comentarios = load_comentarios()
except FileNotFoundError as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Carregar dados resumo
sentimentos = get_sentimentos_summary(comentarios)
sentimentos_total = sum(sentimentos.values())

st.markdown("---")

# Gráfico de Sentimentos
st.subheader("Distribuição de Sentimentos")

percentuais = {
    "Positivo": (sentimentos["positivo"] / sentimentos_total * 100) if sentimentos_total > 0 else 0,
    "Negativo": (sentimentos["negativo"] / sentimentos_total * 100) if sentimentos_total > 0 else 0,
    "Neutro": (sentimentos["neutro"] / sentimentos_total * 100) if sentimentos_total > 0 else 0,
}

sentimentos_labels = ["Positivo", "Negativo", "Neutro"]
sentimentos_valores = [sentimentos["positivo"], sentimentos["negativo"], sentimentos["neutro"]]
sentimentos_pct = [percentuais[label] for label in sentimentos_labels]

# Texto combinado: contagem + percentual
texto_combinado = [
    f"{valor:,.0f}<br>({pct:.1f}%)" 
    for valor, pct in zip(sentimentos_valores, sentimentos_pct)
]

fig_bar = go.Figure(data=[
    go.Bar(x=sentimentos_labels,
           y=sentimentos_valores,
           text=texto_combinado,
           textposition="outside",
           marker=dict(color=[
               SENTIMENT_COLORS["POSITIVO"],
               SENTIMENT_COLORS["NEGATIVO"],
               SENTIMENT_COLORS["NEUTRO"]
           ]))
])
fig_bar.update_layout(
    height=400, 
    xaxis_title="Sentimento", 
    yaxis_title="Contagem",
    showlegend=False
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# Timeline de Sentimentos
st.subheader("Timeline de Sentimentos ao Longo do Tempo")

# Verificar se existe coluna de data
date_cols = [col for col in comentarios.columns if "date" in col.lower() or "time" in col.lower()]

if date_cols:
    date_col = date_cols[0]
    
    # Preparar dados
    df_timeline = comentarios.copy()
    df_timeline[date_col] = pd.to_datetime(df_timeline[date_col], errors="coerce")
    df_timeline = df_timeline.dropna(subset=[date_col])
    
    if not df_timeline.empty:
        df_timeline["data"] = df_timeline[date_col].dt.date
        sentimentos_por_dia = df_timeline.groupby(["data", "sentimento"]).size().unstack(fill_value=0)
        
        fig_timeline = go.Figure()
        for sentimento, cor in SENTIMENT_COLORS.items():
            if sentimento in sentimentos_por_dia.columns:
                fig_timeline.add_trace(go.Scatter(
                    x=sentimentos_por_dia.index,
                    y=sentimentos_por_dia[sentimento],
                    mode="lines+markers",
                    name=sentimento,
                    line=dict(color=cor, width=2)
                ))
        
        fig_timeline.update_layout(
            height=400,
            xaxis_title="Data",
            yaxis_title="Número de Comentários",
            hovermode="x unified"
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("Nenhum dado de data disponível para timeline.")
else:
    st.info("Coluna de data não encontrada nos dados.")

st.markdown("---")

# Gráfico de Sentimentos por Hora do Dia
st.subheader("⏰ Sentimentos por Hora do Dia")

# Verificar se existe coluna de hora
date_cols = [col for col in comentarios.columns if "date" in col.lower() or "time" in col.lower()]

if date_cols:
    date_col = date_cols[0]
    
    # Preparar dados
    df_hora = comentarios.copy()
    df_hora[date_col] = pd.to_datetime(df_hora[date_col], errors="coerce")
    df_hora = df_hora.dropna(subset=[date_col])
    
    if not df_hora.empty:
        df_hora["hora"] = df_hora[date_col].dt.hour
        sentimentos_por_hora = df_hora.groupby(["hora", "sentimento"]).size().unstack(fill_value=0)
        
        fig_hora = go.Figure()
        for sentimento, cor in SENTIMENT_COLORS.items():
            if sentimento in sentimentos_por_hora.columns:
                fig_hora.add_trace(go.Scatter(
                    x=sentimentos_por_hora.index,
                    y=sentimentos_por_hora[sentimento],
                    mode="lines+markers",
                    name=sentimento,
                    line=dict(color=cor, width=2)
                ))
        
        fig_hora.update_layout(
            height=400,
            xaxis_title="Hora do Dia",
            yaxis_title="Número de Comentários",
            hovermode="x unified",
            xaxis=dict(tickmode="linear", tick0=0, dtick=1)
        )
        st.plotly_chart(fig_hora, use_container_width=True)
    else:
        st.info("Nenhum dado de hora disponível.")
else:
    st.info("Coluna de hora não encontrada nos dados.")

st.markdown("---")

# Gráfico: Vídeos com Maior Repercussão (Mais Comentários por Semana)
st.subheader("🎥 Vídeos com Maior Repercussão na Semana")

# Carregar dados de vídeos para obter títulos
try:
    videos_df = pd.read_parquet("data/silver/videos_silver.parquet")
    
    # Merge comentários com vídeos para obter título
    df_videos = comentarios[["video_id", "published_at"]].copy()
    df_videos = df_videos.merge(videos_df[["video_id", "title_clean", "published_at"]], 
                                 on="video_id", 
                                 suffixes=("_comentario", "_video"))
    
    # Usar data do vídeo (published_at_video)
    df_videos["published_at"] = pd.to_datetime(df_videos["published_at_video"], errors="coerce")
    df_videos = df_videos.dropna(subset=["published_at"])
    
    if not df_videos.empty:
        df_videos["semana"] = df_videos["published_at"].dt.to_period("W")
        
        # Contar comentários por vídeo e semana
        videos_engajamento = df_videos.groupby(["semana", "title_clean"]).size().reset_index(name="comentarios")
        videos_engajamento = videos_engajamento.sort_values(["semana", "comentarios"], ascending=[True, False])
        
        # Pegar top 5 vídeos da semana mais recente
        if not videos_engajamento.empty:
            ultima_semana = videos_engajamento["semana"].max()
            top_videos = videos_engajamento[videos_engajamento["semana"] == ultima_semana].head(5)
            
            # Ordenar de forma decrescente para melhor visualização
            top_videos = top_videos.sort_values("comentarios", ascending=True)
            
            fig_videos = go.Figure(data=[
                go.Bar(
                    y=top_videos["title_clean"],
                    x=top_videos["comentarios"],
                    orientation='h',
                    marker=dict(color=SENTIMENT_COLORS["POSITIVO"]),
                    text=top_videos["comentarios"],
                    textposition="outside"
                )
            ])
            
            fig_videos.update_layout(
                title=f"Top 5 Vídeos com Mais Comentários - Semana de {ultima_semana}",
                height=400,
                xaxis_title="Número de Comentários",
                yaxis_title="Vídeo"
            )
            st.plotly_chart(fig_videos, use_container_width=True, key="fig_videos_repercussao")
        else:
            st.info("Sem dados de vídeos para exibição.")
    else:
        st.info("Nenhum dado de data/vídeo disponível.")
except FileNotFoundError:
    st.error("⚠️ Arquivo de vídeos (videos_silver.parquet) não encontrado. Verifique se o pipeline foi executado completamente.")

st.markdown("---")

# Gráfico: Distribuição de Emoções (BERT)
st.subheader("😊😠😢 Distribuição de Emoções Detectadas (BERT)")

if "emocao" in comentarios.columns:
    emocoes_dist = comentarios["emocao"].value_counts()
    
    # Definir cores por emoção
    cores_emocoes = {
        "ENTUSIASMO": "#FFD700",      # Ouro
        "ESPERANCA": "#90EE90",       # Verde claro
        "RAIVA": "#FF4500",           # Vermelho-laranja
        "TRISTEZA": "#4169E1",        # Azul
        "DECEPCAO": "#FF69B4",        # Rosa
        "NEUTRO": "#A9A9A9"           # Cinza
    }
    
    fig_emocoes = go.Figure(data=[
        go.Bar(
            x=emocoes_dist.index,
            y=emocoes_dist.values,
            marker=dict(color=[cores_emocoes.get(e, "#95a5a6") for e in emocoes_dist.index]),
            text=emocoes_dist.values,
            textposition="outside"
        )
    ])
    
    fig_emocoes.update_layout(
        height=400,
        xaxis_title="Emoção",
        yaxis_title="Contagem de Comentários",
        showlegend=False
    )
    st.plotly_chart(fig_emocoes, use_container_width=True)
    
    st.info("**Emoções detectadas pelo BERT:**\n- 🌟 **Entusiasmo**: Comentários animados\n- 🌱 **Esperança**: Comentários otimistas\n- 😠 **Raiva**: Comentários agressivos\n- 😢 **Tristeza**: Comentários melancólicos\n- 😔 **Decepção**: Comentários desapontados\n- 😐 **Neutro**: Comentários sem emoção clara")

st.markdown("---")

st.subheader("📝 Amostra de Comentários por Emoção")

if "emocao" in comentarios.columns:
    # Filtro por emoção
    emocao_filter = st.selectbox(
        "Filtrar por emoção detectada:",
        ["Todos"] + sorted([e for e in comentarios["emocao"].unique() if pd.notna(e)])
    )
    
    if emocao_filter != "Todos":
        df_filtered = comentarios[comentarios["emocao"] == emocao_filter].copy()
    else:
        df_filtered = comentarios.copy()
    
    # Preparar dados para exibição
    df_display = df_filtered.head(15).copy()
    
    # Anonimizar texto
    if "text_clean" in df_display.columns:
        df_display["text_anonimizado"] = df_display["text_clean"].apply(anonimizar_comentario)
    
    # Colunas para mostrar
    cols_display = []
    if "text_anonimizado" in df_display.columns:
        cols_display.append("text_anonimizado")
    if "emocao" in df_display.columns:
        cols_display.append("emocao")
    if "score_emocao" in df_display.columns:
        cols_display.append("score_emocao")
    if "sentimento" in df_display.columns:
        cols_display.append("sentimento")
    if "score_sentimento" in df_display.columns:
        cols_display.append("score_sentimento")
    if "like_count" in df_display.columns:
        cols_display.append("like_count")
    
    # Se nenhuma coluna foi encontrada, mostrar o que temos
    if not cols_display:
        cols_display = list(df_display.columns)[:5]
    
    if cols_display:
        # Renomear colunas para português
        rename_dict = {
            "text_anonimizado": "Comentário (Anonimizado)",
            "text_clean": "Comentário",
            "comment_text": "Comentário",
            "text": "Comentário",
            "channel_title": "Canal",
            "candidato": "Candidato",
            "sentimento": "Sentimento",
            "emocao": "Emoção",
            "score_sentimento": "Score Sentimento",
            "score_emocao": "Score Emoção",
            "like_count": "Likes"
        }
        
        df_display_renamed = df_display[cols_display].rename(columns=rename_dict)
        st.dataframe(df_display_renamed, use_container_width=True, height=300)
        st.caption(f"✓ Comentários anonimizados por privacidade | Mostrando {len(df_display)} de {len(df_filtered)} encontrados")
    else:
        st.info("Nenhuma coluna compatível encontrada.")
else:
    st.info("Coluna de sentimento não encontrada nos dados.")

st.markdown("---")
st.caption("Dados extraídos da camada Gold - Última atualização: Data dos dados processados")
