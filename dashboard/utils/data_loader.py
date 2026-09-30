"""Funções para carregar e processar dados dos arquivos Parquet."""

import pandas as pd
from pathlib import Path
from functools import lru_cache
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CANDIDATOS_FILE, TEMAS_FILE, COMENTARIOS_FILE

# Caminhos das novas tabelas enriquecidas
COMENTARIOS_ENRICHED_FILE = CANDIDATOS_FILE.parent / "comentarios_gold_enriched.parquet"
CANDIDATOS_TIMELINE_FILE = CANDIDATOS_FILE.parent / "candidatos_timeline.parquet"
CANAIS_TIMELINE_FILE = CANDIDATOS_FILE.parent / "canais_timeline.parquet"


@lru_cache(maxsize=3)
def load_candidatos() -> pd.DataFrame:
    """Carrega dados de candidatos manifestações."""
    try:
        df = pd.read_parquet(CANDIDATOS_FILE)
        return df.sort_values("comentarios_total", ascending=False)
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {CANDIDATOS_FILE}")


@lru_cache(maxsize=3)
def load_temas() -> pd.DataFrame:
    """Carrega dados de engajamento por tema."""
    try:
        df = pd.read_parquet(TEMAS_FILE)
        return df.sort_values("comentarios_total", ascending=False)
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {TEMAS_FILE}")


@lru_cache(maxsize=3)
def load_comentarios() -> pd.DataFrame:
    """Carrega dados de comentários com sentimento."""
    try:
        df = pd.read_parquet(COMENTARIOS_FILE)
        # Converter coluna de data se existir
        for date_col in ["date", "published_at", "created_at", "comment_date"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {COMENTARIOS_FILE}")


def get_sentimentos_summary(df: pd.DataFrame) -> dict:
    """Retorna resumo de sentimentos."""
    return {
        "positivo": (df.get("sentimento") == "POSITIVO").sum() if "sentimento" in df.columns else 0,
        "negativo": (df.get("sentimento") == "NEGATIVO").sum() if "sentimento" in df.columns else 0,
        "neutro": (df.get("sentimento") == "NEUTRO").sum() if "sentimento" in df.columns else 0,
    }


def format_number(num: float | int) -> str:
    """Formata número para exibição (ex: 1000 -> 1K)."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(int(num))


@lru_cache(maxsize=3)
def load_candidatos_timeline() -> pd.DataFrame:
    """Carrega timeline de candidatos com série temporal."""
    try:
        df = pd.read_parquet(CANDIDATOS_TIMELINE_FILE)
        df["data"] = pd.to_datetime(df["data"])
        return df.sort_values("data", ascending=False)
    except FileNotFoundError:
        return pd.DataFrame()  # Retornar vazio se não existir


@lru_cache(maxsize=3)
def load_canais_timeline() -> pd.DataFrame:
    """Carrega timeline de canais com série temporal."""
    try:
        df = pd.read_parquet(CANAIS_TIMELINE_FILE)
        df["data"] = pd.to_datetime(df["data"])
        return df.sort_values("data", ascending=False)
    except FileNotFoundError:
        return pd.DataFrame()  # Retornar vazio se não existir


@lru_cache(maxsize=3)
def load_comentarios_enriched() -> pd.DataFrame:
    """Carrega comentários enriquecidos com candidato/canal."""
    try:
        df = pd.read_parquet(COMENTARIOS_ENRICHED_FILE)
        # Converter coluna de data se existir
        for date_col in ["date", "published_at", "created_at", "comment_date"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        return df
    except FileNotFoundError:
        # Fallback: retornar comentários normais se enriquecidos não existem
        return load_comentarios()
