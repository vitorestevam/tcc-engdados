#!/usr/bin/env python3
"""Coleta comentarios e respostas para os videos extraidos na etapa 1."""

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT.parent / "data" / "comments"


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

    while True:
        response = client.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100,
            pageToken=page_token,
        ).execute()
        replies.extend(comment_record(item, video, parent_id) for item in response["items"])
        page_token = response.get("nextPageToken")
        if not page_token:
            return replies


def collect_video_comments(client, video: dict) -> list[dict]:
    comments = []
    page_token = None

    while True:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta comentarios dos videos da etapa 1.")
    parser.add_argument("--videos-file", type=Path, required=True, help="JSON gerado por 1-collect.py")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Defina YOUTUBE_API_KEY no ambiente ou no arquivo .env do projeto.")

    client = build("youtube", "v3", developerKey=api_key)
    videos = load_videos(args.videos_file)
    collected_at = datetime.now(UTC)
    comments = []
    video_status = []

    for video in videos:
        try:
            video_comments = collect_video_comments(client, video)
            comments.extend(video_comments)
            video_status.append(
                {"video_id": video["video_id"], "status": "completed", "comment_count": len(video_comments)}
            )
        except HttpError as error:
            video_status.append(
                {"video_id": video["video_id"], "status": "error", "reason": error_reason(error)}
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"comments_{collected_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    payload = {
        "collected_at": collected_at.isoformat(),
        "source_videos_file": str(args.videos_file),
        "video_count": len(videos),
        "comment_count": len(comments),
        "video_status": video_status,
        "comments": comments,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(comments)} comentarios salvos em {output_path}")


if __name__ == "__main__":
    main()