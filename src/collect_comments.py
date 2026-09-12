#!/usr/bin/env python3
"""Coleta comentarios e respostas para os videos extraidos na etapa 1."""

import argparse
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT.parent / "data" / "comments"
LOGGER = logging.getLogger(__name__)


def comment_record(item: dict, video: dict, parent_id: str | None) -> dict:
    snippet = item["snippet"]
    return {
        "comment_id": item["id"],
        "video_id": video["video_id"],
        "source": video["source"],
        "category": video["category"],
        "parent_id": parent_id,
        "published_at": snippet["publishedAt"],
        "updated_at": snippet["updatedAt"],
        "text": snippet["textDisplay"],
        "like_count": int(snippet.get("likeCount", 0)),
    }


def list_replies(client, parent_id: str, video: dict) -> list[dict]:
    replies = []
    page_token = None
    page_count = 0

    while True:
        page_count += 1
        response = client.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100,
            pageToken=page_token,
        ).execute()
        replies.extend(comment_record(item, video, parent_id) for item in response["items"])
        page_token = response.get("nextPageToken")
        if not page_token:
            LOGGER.info("Respostas coletadas: video=%s comentario=%s paginas=%s respostas=%s", video["video_id"], parent_id, page_count, len(replies))
            return replies


def collect_video_comments(client, video: dict) -> list[dict]:
    comments = []
    page_token = None
    page_count = 0

    while True:
        page_count += 1
        response = client.commentThreads().list(
            part="snippet",
            videoId=video["video_id"],
            maxResults=100,
            textFormat="plainText",
            pageToken=page_token,
        ).execute()

        for thread in response["items"]:
            top_level = thread["snippet"]["topLevelComment"]
            comments.append(comment_record(top_level, video, None))
            if thread["snippet"].get("totalReplyCount", 0) > 0:
                comments.extend(list_replies(client, top_level["id"], video))

        page_token = response.get("nextPageToken")
        if not page_token:
            unique_comments = {comment["comment_id"]: comment for comment in comments}
            LOGGER.info("Comentarios coletados: video=%s paginas=%s comentarios=%s", video["video_id"], page_count, len(unique_comments))
            return list(unique_comments.values())


def error_reason(error: HttpError) -> str:
    try:
        return error.error_details[0]["reason"]
    except (AttributeError, IndexError, KeyError):
        return f"http_{error.resp.status}"


def load_videos(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    videos = payload.get("videos")
    if not isinstance(videos, list):
        raise ValueError(f"{path.name} nao possui uma lista 'videos' valida")
    return videos


def collect_comments(videos_file: Path | str, output_file: Path | str) -> str:
    videos_file = Path(videos_file)
    output_file = Path(output_file)
    LOGGER.info("Iniciando coleta de comentarios: videos=%s saida=%s", videos_file, output_file)
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        LOGGER.error("YOUTUBE_API_KEY nao foi encontrada no ambiente ou em %s", PROJECT_ROOT / ".env")
        raise RuntimeError("Defina YOUTUBE_API_KEY no ambiente ou no arquivo .env do projeto.")

    LOGGER.info("Criando cliente YouTube")
    client = build("youtube", "v3", developerKey=api_key)
    videos = load_videos(videos_file)
    LOGGER.info("Arquivo de videos carregado: videos=%s", len(videos))
    collected_at = datetime.now(UTC)
    comments = []
    video_status = []

    for video in videos:
        try:
            LOGGER.info("Coletando comentarios: video=%s", video["video_id"])
            video_comments = collect_video_comments(client, video)
            comments.extend(video_comments)
            video_status.append(
                {"video_id": video["video_id"], "status": "completed", "comment_count": len(video_comments)}
            )
        except HttpError as error:
            LOGGER.warning("Falha na coleta de comentarios: video=%s motivo=%s", video["video_id"], error_reason(error))
            video_status.append(
                {"video_id": video["video_id"], "status": "error", "reason": error_reason(error)}
            )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "collected_at": collected_at.isoformat(),
        "source_videos_file": str(videos_file),
        "video_count": len(videos),
        "comment_count": len(comments),
        "video_status": video_status,
        "comments": comments,
    }
    output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    LOGGER.info("Coleta de comentarios concluida: comentarios=%s arquivo=%s", len(comments), output_file)
    return str(output_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta comentarios dos videos da etapa 1.")
    parser.add_argument("--videos-file", type=Path, required=True, help="JSON gerado por collect_videos.py")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    output_group.add_argument("--output-file", type=Path, help="Arquivo JSON de saida da execucao")
    args = parser.parse_args()

    output_path = args.output_file or (
        args.output_dir / f"comments_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    print(f"Comentarios salvos em {collect_comments(args.videos_file, output_path)}")


if __name__ == "__main__":
    main()