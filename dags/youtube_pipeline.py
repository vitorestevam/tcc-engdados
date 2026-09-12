"""Orquestra a coleta Bronze de videos e comentarios do YouTube."""

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

PROJECT_DIR = "/opt/airflow/project"
DATA_DIR = "/opt/airflow/data"
RUN_DIR = f"{DATA_DIR}/bronze/{{{{ logical_date.in_timezone('UTC').strftime('%Y-%m-%dT%H:%MZ') }}}}"

sys.path.insert(0, f"{PROJECT_DIR}/src")

from collect_comments import collect_comments
from collect_videos import collect_videos

with DAG(
    dag_id="youtube_pipeline",
    description="Coleta videos e comentarios do YouTube para a camada Bronze.",
    start_date=datetime(2026, 9, 12),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["youtube", "bronze"],
) as dag:
    collect_videos_task = PythonOperator(
        task_id="collect_videos",
        python_callable=collect_videos,
        op_kwargs={
            "channels_file": f"{PROJECT_DIR}/settings/channels.txt",
            "output_file": f"{RUN_DIR}/videos.json",
        },
    )

    collect_comments_task = PythonOperator(
        task_id="collect_comments",
        python_callable=collect_comments,
        op_kwargs={
            "videos_file": f"{RUN_DIR}/videos.json",
            "output_file": f"{RUN_DIR}/comments.json",
        },
    )

    collect_videos_task >> collect_comments_task