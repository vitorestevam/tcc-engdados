"""Carregamento dos artefatos Gold e Silver de uma execução da DAG."""

from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit as st

from config import GOLD_ROOT, SILVER_ROOT

REQUIRED_GOLD_FILES = (
    "comments_with_sentiment.parquet",
    "candidatos_manifestacoes.parquet",
    "temas_engajamento.parquet",
    "comentarios_gold_enriched.parquet",
    "candidatos_timeline.parquet",
    "canais_timeline.parquet",
)


def get_available_run_ids() -> list[str]:
    if not GOLD_ROOT.is_dir() or not SILVER_ROOT.is_dir():
        return []
    return sorted(
        path.name
        for path in GOLD_ROOT.iterdir()
        if path.is_dir()
        and (SILVER_ROOT / path.name).is_dir()
        and all((path / filename).is_file() for filename in REQUIRED_GOLD_FILES)
    )


def render_run_selector() -> str:
    run_ids = get_available_run_ids()
    if not run_ids:
        raise FileNotFoundError(
            "Nenhuma execução completa foi encontrada. Execute a DAG com a etapa gold_enrich_datasets."
        )

    default_run_id = run_ids[-1]
    if st.session_state.get("dashboard_run_id") not in run_ids:
        st.session_state["dashboard_run_id"] = default_run_id
    return st.sidebar.selectbox(
        "Execução da DAG",
        options=list(reversed(run_ids)),
        key="dashboard_run_id",
        help="Cada execução usa os próprios artefatos Bronze, Silver e Gold.",
    )


def get_selected_run_id() -> str:
    run_ids = get_available_run_ids()
    if not run_ids:
        raise FileNotFoundError(
            "Nenhuma execução completa foi encontrada. Execute a DAG com a etapa gold_enrich_datasets."
        )
    return st.session_state.get("dashboard_run_id", run_ids[-1])


def _run_file(run_id: str, filename: str, layer: str = "gold") -> Path:
    root = GOLD_ROOT if layer == "gold" else SILVER_ROOT
    path = root / run_id / filename
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado para a execução {run_id}: {path}")
    return path


def _read_comments(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    for date_column in ("published_at", "updated_at"):
        if date_column in frame.columns:
            frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce", utc=True)
    return frame


@lru_cache(maxsize=8)
def load_candidatos(run_id: str | None = None) -> pd.DataFrame:
    selected_run_id = run_id or get_selected_run_id()
    return pd.read_parquet(_run_file(selected_run_id, "candidatos_manifestacoes.parquet")).sort_values(
        "comentarios_total", ascending=False
    )


@lru_cache(maxsize=8)
def load_temas(run_id: str | None = None) -> pd.DataFrame:
    selected_run_id = run_id or get_selected_run_id()
    return pd.read_parquet(_run_file(selected_run_id, "temas_engajamento.parquet")).sort_values(
        "comentarios_total", ascending=False
    )


@lru_cache(maxsize=8)
def load_comentarios(run_id: str | None = None) -> pd.DataFrame:
    selected_run_id = run_id or get_selected_run_id()
    return _read_comments(_run_file(selected_run_id, "comments_with_sentiment.parquet"))


@lru_cache(maxsize=8)
def load_comentarios_enriched(run_id: str | None = None) -> pd.DataFrame:
    selected_run_id = run_id or get_selected_run_id()
    return _read_comments(_run_file(selected_run_id, "comentarios_gold_enriched.parquet"))


@lru_cache(maxsize=8)
def load_candidatos_timeline(run_id: str | None = None) -> pd.DataFrame:
    selected_run_id = run_id or get_selected_run_id()
    frame = pd.read_parquet(_run_file(selected_run_id, "candidatos_timeline.parquet"))
    frame["data"] = pd.to_datetime(frame["data"])
    return frame.sort_values("data")


@lru_cache(maxsize=8)
def load_canais_timeline(run_id: str | None = None) -> pd.DataFrame:
    selected_run_id = run_id or get_selected_run_id()
    frame = pd.read_parquet(_run_file(selected_run_id, "canais_timeline.parquet"))
    frame["data"] = pd.to_datetime(frame["data"])
    return frame.sort_values("data")


@lru_cache(maxsize=8)
def load_videos(run_id: str | None = None) -> pd.DataFrame:
    selected_run_id = run_id or get_selected_run_id()
    return pd.read_parquet(_run_file(selected_run_id, "videos_silver.parquet", layer="silver"))


def get_sentimentos_summary(frame: pd.DataFrame) -> dict[str, int]:
    return {
        "positivo": int((frame.get("sentimento") == "POSITIVO").sum()),
        "negativo": int((frame.get("sentimento") == "NEGATIVO").sum()),
        "neutro": int((frame.get("sentimento") == "NEUTRO").sum()),
    }


def format_number(number: float | int) -> str:
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    return str(int(number))