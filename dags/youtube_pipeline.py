"""Orquestra a coleta Bronze e as transformacoes Silver do YouTube."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator

PROJECT_DIR = "/opt/airflow/project"
DATA_DIR = "/opt/airflow/data"
RUN_ID = "{{ logical_date.in_timezone('UTC').strftime('%Y%m%dT%H%M%SZ') }}"
BRONZE_RUN_DIR = f"{DATA_DIR}/bronze/{RUN_ID}"
SILVER_RUN_DIR = f"{DATA_DIR}/silver/{RUN_ID}"
GOLD_RUN_DIR = f"{DATA_DIR}/gold/{RUN_ID}"
CONFIG_RUN_DIR = f"{DATA_DIR}/config/{RUN_ID}"
COLLECTION_START = "{{ dag_run.conf.get('start_date', params.start_date) }}T00:00:00+00:00"
COLLECTION_END = "{{ dag_run.conf.get('end_date', params.end_date) }}T23:59:59.999999+00:00"

sys.path.insert(0, f"{PROJECT_DIR}/src")

from bronze_collect_comments import collect_comments
from bronze_collect_videos import collect_videos
from gold_add_sentiment import add_sentiment
from gold_create_aggregations import create_gold_aggregations
from gold_create_temporal_series import create_temporal_series
from prepare_run_settings import prepare_run_settings
from silver_select_relevant_videos import select_relevant_videos
from silver_transform_comments import transform_comments_silver
from silver_transform_videos import transform_videos_silver

settings_dir = Path(PROJECT_DIR) / "settings"
if not settings_dir.is_dir():
    settings_dir = Path(__file__).resolve().parents[1] / "settings"
DEFAULT_CHANNELS = json.loads((settings_dir / "channels.json").read_text(encoding="utf-8"))["channels"]
DEFAULT_RELEVANCE_TERMS = json.loads(
    (settings_dir / "relevance_terms.json").read_text(encoding="utf-8")
)["relevance_terms"]

with DAG(
    dag_id="youtube_pipeline",
    description="Coleta dados do YouTube e produz as camadas Bronze, Silver e Gold.",
    start_date=datetime(2026, 9, 12),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    params={
        "start_date": Param(
            default="2026-09-01",
            type="string",
            format="date",
            title="Data inicial",
            description="Inicio da janela de coleta em UTC.",
        ),
        "end_date": Param(
            default="2026-09-20",
            type="string",
            format="date",
            title="Data final",
            description="Fim da janela de coleta em UTC, inclusivo.",
        ),
        "channels": Param(
            default=DEFAULT_CHANNELS,
            type="array",
            items={"type": "object"},
            title="Canais",
            description="Lista de objetos com source, category e identifier.",
        ),
        "relevance_terms": Param(
            default=DEFAULT_RELEVANCE_TERMS,
            type="array",
            items={"type": "object"},
            title="Termos de relevancia",
            description="Lista de objetos com type, label e term.",
        ),
    },
    tags=["youtube", "bronze", "silver", "gold"],
) as dag:
    prepare_run_settings_task = PythonOperator(
        task_id="config_prepare_run_settings",
        python_callable=prepare_run_settings,
        op_kwargs={"output_dir": CONFIG_RUN_DIR},
    )

    collect_videos_task = PythonOperator(
        task_id="bronze_collect_videos",
        python_callable=collect_videos,
        op_kwargs={
            "channels_file": f"{CONFIG_RUN_DIR}/channels.json",
            "output_file": f"{BRONZE_RUN_DIR}/videos.json",
            "collection_start": COLLECTION_START,
            "collection_end": COLLECTION_END,
        },
    )

    collect_comments_task = PythonOperator(
        task_id="bronze_collect_comments",
        python_callable=collect_comments,
        op_kwargs={
            "videos_file": f"{BRONZE_RUN_DIR}/videos.json",
            "output_file": f"{BRONZE_RUN_DIR}/comments.json",
        },
    )

    select_relevant_videos_task = PythonOperator(
        task_id="silver_select_relevant_videos",
        python_callable=select_relevant_videos,
        op_kwargs={
            "videos_file": f"{BRONZE_RUN_DIR}/videos.json",
            "relevance_file": f"{CONFIG_RUN_DIR}/relevance_terms.json",
            "output_dir": SILVER_RUN_DIR,
        },
    )

    transform_videos_silver_task = PythonOperator(
        task_id="silver_transform_videos",
        python_callable=transform_videos_silver,
        op_kwargs={
            "input_file": f"{SILVER_RUN_DIR}/videos_relevantes.parquet",
            "relevance_file": f"{CONFIG_RUN_DIR}/relevance_terms.json",
            "output_file": f"{SILVER_RUN_DIR}/videos_silver.parquet",
        },
    )

    transform_comments_silver_task = PythonOperator(
        task_id="silver_transform_comments",
        python_callable=transform_comments_silver,
        op_kwargs={
            "comments_file": f"{BRONZE_RUN_DIR}/comments.json",
            "videos_silver_file": f"{SILVER_RUN_DIR}/videos_silver.parquet",
            "output_file": f"{SILVER_RUN_DIR}/comments_silver.parquet",
        },
    )

    add_sentiment_task = PythonOperator(
        task_id="gold_add_sentiment",
        python_callable=add_sentiment,
        op_kwargs={
            "input_file": f"{SILVER_RUN_DIR}/comments_silver.parquet",
            "output_file": f"{GOLD_RUN_DIR}/comments_with_sentiment.parquet",
        },
    )

    create_temporal_series_task = PythonOperator(
        task_id="gold_create_temporal_series",
        python_callable=create_temporal_series,
        op_kwargs={
            "videos_file": f"{SILVER_RUN_DIR}/videos_silver.parquet",
            "comments_file": f"{GOLD_RUN_DIR}/comments_with_sentiment.parquet",
            "output_file": f"{GOLD_RUN_DIR}/serie_temporal_volume.parquet",
        },
    )

    create_aggregations_task = PythonOperator(
        task_id="gold_create_aggregations",
        python_callable=create_gold_aggregations,
        op_kwargs={
            "videos_file": f"{SILVER_RUN_DIR}/videos_silver.parquet",
            "comments_file": f"{GOLD_RUN_DIR}/comments_with_sentiment.parquet",
            "candidates_output_file": f"{GOLD_RUN_DIR}/candidatos_manifestacoes.parquet",
            "themes_output_file": f"{GOLD_RUN_DIR}/temas_engajamento.parquet",
        },
    )

    (
        prepare_run_settings_task
        >> collect_videos_task
        >> collect_comments_task
        >> select_relevant_videos_task
        >> transform_videos_silver_task
        >> transform_comments_silver_task
        >> add_sentiment_task
        >> create_temporal_series_task
        >> create_aggregations_task
    )