"""Orquestra a coleta Bronze e as transformacoes Silver do YouTube."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_DIR = "/opt/airflow/project"
DATA_DIR = "/opt/airflow/data"
RUN_ID = "{{ logical_date.in_timezone('UTC').strftime('%Y%m%dT%H%M%SZ') }}"
BRONZE_RUN_DIR = f"{DATA_DIR}/bronze/{RUN_ID}"
SILVER_RUN_DIR = f"{DATA_DIR}/silver/{RUN_ID}"
CONFIG_RUN_DIR = f"{DATA_DIR}/config/{RUN_ID}"
COLLECTION_START = "{{ dag_run.conf.get('start_date', params.start_date) }}T00:00:00+00:00"
COLLECTION_END = "{{ dag_run.conf.get('end_date', params.end_date) }}T23:59:59.999999+00:00"

sys.path.insert(0, f"{PROJECT_DIR}/src")

from collect_comments import collect_comments
from collect_videos import collect_videos
from prepare_run_settings import prepare_run_settings

settings_dir = Path(PROJECT_DIR) / "settings"
if not settings_dir.is_dir():
    settings_dir = Path(__file__).resolve().parents[1] / "settings"
DEFAULT_CHANNELS = json.loads((settings_dir / "channels.json").read_text(encoding="utf-8"))["channels"]
DEFAULT_RELEVANCE_TERMS = json.loads(
    (settings_dir / "relevance_terms.json").read_text(encoding="utf-8")
)["relevance_terms"]

with DAG(
    dag_id="youtube_pipeline",
    description="Coleta dados do YouTube na Bronze e produz a camada Silver.",
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
    tags=["youtube", "bronze", "silver"],
) as dag:
    prepare_run_settings_task = PythonOperator(
        task_id="prepare_run_settings",
        python_callable=prepare_run_settings,
        op_kwargs={"output_dir": CONFIG_RUN_DIR},
    )

    collect_videos_task = PythonOperator(
        task_id="collect_videos",
        python_callable=collect_videos,
        op_kwargs={
            "channels_file": f"{CONFIG_RUN_DIR}/channels.json",
            "output_file": f"{BRONZE_RUN_DIR}/videos.json",
            "collection_start": COLLECTION_START,
            "collection_end": COLLECTION_END,
        },
    )

    collect_comments_task = PythonOperator(
        task_id="collect_comments",
        python_callable=collect_comments,
        op_kwargs={
            "videos_file": f"{BRONZE_RUN_DIR}/videos.json",
            "output_file": f"{BRONZE_RUN_DIR}/comments.json",
        },
    )

    select_relevant_videos_task = BashOperator(
        task_id="select_relevant_videos",
        bash_command=(
            f"python {PROJECT_DIR}/src/select_relevant_videos.py "
            f"--videos-file {BRONZE_RUN_DIR}/videos.json "
            f"--relevance-file {CONFIG_RUN_DIR}/relevance_terms.json "
            f"--output-dir {SILVER_RUN_DIR}"
        ),
    )

    transform_videos_silver_task = BashOperator(
        task_id="transform_videos_silver",
        bash_command=(
            f"python {PROJECT_DIR}/src/transform_videos_silver.py "
            f"--input-file {SILVER_RUN_DIR}/videos_relevantes.parquet "
            f"--relevance-file {CONFIG_RUN_DIR}/relevance_terms.json "
            f"--output-file {SILVER_RUN_DIR}/videos_silver.parquet"
        ),
    )

    transform_comments_silver_task = BashOperator(
        task_id="transform_comments_silver",
        bash_command=(
            f"python {PROJECT_DIR}/src/transform_comments_silver.py "
            f"--comments-file {BRONZE_RUN_DIR}/comments.json "
            f"--videos-silver-file {SILVER_RUN_DIR}/videos_silver.parquet "
            f"--output-file {SILVER_RUN_DIR}/comments_silver.parquet"
        ),
    )

    (
        prepare_run_settings_task
        >> collect_videos_task
        >> collect_comments_task
        >> select_relevant_videos_task
        >> transform_videos_silver_task
        >> transform_comments_silver_task
    )