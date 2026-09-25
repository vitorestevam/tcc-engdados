"""Orquestra a coleta Bronze e as transformacoes Silver do YouTube."""

import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_DIR = "/opt/airflow/project"
DATA_DIR = "/opt/airflow/data"
RUN_ID = "{{ logical_date.in_timezone('UTC').strftime('%Y%m%dT%H%M%SZ') }}"
BRONZE_RUN_DIR = f"{DATA_DIR}/bronze/{RUN_ID}"
SILVER_RUN_DIR = f"{DATA_DIR}/silver/{RUN_ID}"

sys.path.insert(0, f"{PROJECT_DIR}/src")

from collect_comments import collect_comments
from collect_videos import collect_videos

with DAG(
    dag_id="youtube_pipeline",
    description="Coleta dados do YouTube na Bronze e produz a camada Silver.",
    start_date=datetime(2026, 9, 12),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["youtube", "bronze", "silver"],
) as dag:
    collect_videos_task = PythonOperator(
        task_id="collect_videos",
        python_callable=collect_videos,
        op_kwargs={
            "channels_file": f"{PROJECT_DIR}/settings/channels.txt",
            "output_file": f"{BRONZE_RUN_DIR}/videos.json",
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
            f"--output-dir {SILVER_RUN_DIR}"
        ),
    )

    transform_videos_silver_task = BashOperator(
        task_id="transform_videos_silver",
        bash_command=(
            f"python {PROJECT_DIR}/src/transform_videos_silver.py "
            f"--input-file {SILVER_RUN_DIR}/videos_relevantes.parquet "
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
        collect_videos_task
        >> collect_comments_task
        >> select_relevant_videos_task
        >> transform_videos_silver_task
        >> transform_comments_silver_task
    )