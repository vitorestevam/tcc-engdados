#!/usr/bin/env python3
"""Gera artefatos Gold adicionais para as visualizacoes do dashboard."""

import argparse
from pathlib import Path

import pandas as pd


def _candidate_for_comment(comment: pd.Series) -> str:
    if comment["category"] == "candidato":
        return str(comment["source"])

    candidates = comment["candidatos_mencionados"]
    if isinstance(candidates, (list, tuple, set)) and candidates:
        return str(candidates[0])
    return "Não Mencionado"


def _aggregate_timeline(grouped_comments: pd.DataFrame, group_column: str) -> pd.DataFrame:
    if grouped_comments.empty:
        return pd.DataFrame()

    timeline = (
        grouped_comments.assign(data=pd.to_datetime(grouped_comments["published_at"], utc=True).dt.date)
        .groupby([group_column, "data"], as_index=False)
        .agg(
            sentimento_positivo=("sentimento", lambda values: (values == "POSITIVO").sum()),
            sentimento_negativo=("sentimento", lambda values: (values == "NEGATIVO").sum()),
            sentimento_neutro=("sentimento", lambda values: (values == "NEUTRO").sum()),
            total_comentarios=("comment_id", "count"),
            score_sentimento_medio=("score_sentimento", "mean"),
            score_emocao_medio=("score_emocao", "mean"),
            likes_total=("like_count", "sum"),
            likes_media=("like_count", "mean"),
        )
        .sort_values([group_column, "data"])
        .reset_index(drop=True)
    )
    timeline["sentimento_positivo_pct"] = (
        timeline["sentimento_positivo"].div(timeline["total_comentarios"]).mul(100).round(2)
    )
    timeline["sentimento_negativo_pct"] = (
        timeline["sentimento_negativo"].div(timeline["total_comentarios"]).mul(100).round(2)
    )
    return timeline


def enrich_gold_datasets(
    videos_file: Path | str,
    comments_file: Path | str,
    enriched_comments_output_file: Path | str,
    candidates_timeline_output_file: Path | str,
    channels_timeline_output_file: Path | str,
) -> None:
    """Enriquece comentários Gold e cria séries temporais por candidato e canal."""
    videos = pd.read_parquet(videos_file)
    comments = pd.read_parquet(comments_file)

    videos_context = videos[[
        "video_id", "channel_title", "source", "category", "candidatos_mencionados",
    ]]
    enriched_comments = comments.drop(columns=["source", "category"], errors="ignore").merge(
        videos_context,
        on="video_id",
        how="left",
        validate="many_to_one",
    )
    enriched_comments["candidato"] = enriched_comments.apply(_candidate_for_comment, axis=1)

    candidates_timeline = _aggregate_timeline(
        enriched_comments[enriched_comments["category"] == "candidato"],
        "candidato",
    )
    channels_timeline = _aggregate_timeline(
        enriched_comments[enriched_comments["category"] == "imprensa"].rename(
            columns={"channel_title": "tema"}
        ),
        "tema",
    )

    outputs = (
        (enriched_comments, Path(enriched_comments_output_file)),
        (candidates_timeline, Path(candidates_timeline_output_file)),
        (channels_timeline, Path(channels_timeline_output_file)),
    )
    for frame, output_file in outputs:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(output_file, index=False)

    print(f"{len(enriched_comments)} comentarios enriquecidos gravados em {outputs[0][1]}")
    print(f"{len(candidates_timeline)} registros de candidatos gravados em {outputs[1][1]}")
    print(f"{len(channels_timeline)} registros de canais gravados em {outputs[2][1]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera artefatos Gold adicionais para o dashboard.")
    parser.add_argument("--videos-file", type=Path, required=True)
    parser.add_argument("--comments-file", type=Path, required=True)
    parser.add_argument("--enriched-comments-output-file", type=Path, required=True)
    parser.add_argument("--candidates-timeline-output-file", type=Path, required=True)
    parser.add_argument("--channels-timeline-output-file", type=Path, required=True)
    args = parser.parse_args()
    enrich_gold_datasets(
        args.videos_file,
        args.comments_file,
        args.enriched_comments_output_file,
        args.candidates_timeline_output_file,
        args.channels_timeline_output_file,
    )


if __name__ == "__main__":
    main()