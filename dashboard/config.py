"""Configurações globais do dashboard Streamlit."""

import os
from pathlib import Path

# Diretórios
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
GOLD_DIR = DATA_DIR / "gold"

# Caminhos dos arquivos Parquet
CANDIDATOS_FILE = GOLD_DIR / "candidatos_manifestacoes.parquet"
TEMAS_FILE = GOLD_DIR / "temas_engajamento.parquet"
COMENTARIOS_FILE = GOLD_DIR / "comments_with_sentiment.parquet"

# Configuração Streamlit
PAGE_CONFIG = {
    "page_title": "Dashboard - Engajamento Ceará 2026",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Cores/Temas
SENTIMENT_COLORS = {
    "POSITIVO": "#2ecc71",    # Verde
    "NEGATIVO": "#e74c3c",    # Vermelho
    "NEUTRO": "#95a5a6",      # Cinza
}

CANDIDATE_COLORS = {
    "Ciro Gomes": "#0066cc",      # Azul
    "Elmano de Freitas": "#ff6600", # Laranja
}

# Informações do projeto
PROJECT_INFO = {
    "title": "Dashboard - Engajamento Digital Eleições Ceará 2026",
    "subtitle": "Análise de Sentimentos e Engajamento no YouTube",
    "version": "1.0.0",
}
