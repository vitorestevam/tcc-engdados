#!/usr/bin/env python3
"""Coleta metadados de videos do YouTube para a camada Bronze."""

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build

COLLECTION_START = datetime(2026, 9, 1, tzinfo=UTC)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHANNELS_FILE = PROJECT_ROOT / "settings"/ "channels.txt"
OUTPUT_DIR = PROJECT_ROOT.parent / "data" / "videos"

def parse_channels(path: Path) -> list[dict[str, str]]:
    channels = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3 or not all(parts):
            raise ValueError(
                f"{path.name}:{line_number} deve usar: nome | categoria | handle ou channelId"
            )
        channels.append({"source": parts[0], "category": parts[1], "identifier": parts[2]})

    if not channels:
        raise ValueError(f"{path.name} nao possui canais configurados")
    return channels


def resolve_channel(client, identifier: str) -> dict[str, str]:
    params = {"part": "id,snippet,contentDetails"}
    if identifier.startswith("UC"):
        params["id"] = identifier
    elif identifier.startswith("@"):
        params["forHandle"] = identifier
    else:
        raise ValueError(f"Identificador invalido: {identifier}. Use @handle ou channelId (UC...).")

    response = client.channels().list(**params).execute()
    if not response["items"]:
        raise ValueError(f"Canal nao encontrado: {identifier}")

    channel = response["items"][0]
    return {
        "channel_id": channel["id"],
        "channel_title": channel["snippet"]["title"],
        "uploads_playlist_id": channel["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def list_video_ids(client, playlist_id: str, collection_end: datetime) -> list[tuple[str, datetime]]:
    video_ids = []
    page_token = None

    while True:
        response = client.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in response["items"]:
            published_at = datetime.fromisoformat(
                item["contentDetails"]["videoPublishedAt"].replace("Z", "+00:00")
            )
            if COLLECTION_START <= published_at <= collection_end:
                video_ids.append((item["contentDetails"]["videoId"], published_at))

        page_token = response.get("nextPageToken")
        if not page_token:
            return video_ids


def fetch_videos(client, video_ids: list[tuple[str, datetime]], channel: dict[str, str], source: dict[str, str]) -> list[dict]:
    videos = []
    published_by_id = dict(video_ids)

    for start in range(0, len(video_ids), 50):
        batch_ids = [video_id for video_id, _ in video_ids[start : start + 50]]
        response = client.videos().list(
            part="id,snippet,statistics,status",
            id=",".join(batch_ids),
            maxResults=50,
        ).execute()

        for video in response["items"]:
            statistics = video.get("statistics", {})
            videos.append(
                {
                    "source": source["source"],
                    "category": source["category"],
                    "channel_id": channel["channel_id"],
                    "channel_title": channel["channel_title"],
                    "video_id": video["id"],
                    "title": video["snippet"]["title"],
                    "published_at": published_by_id[video["id"]].isoformat(),
                    "description": video["snippet"].get("description", ""),
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "comment_count": int(statistics.get("commentCount", 0)),
                    "privacy_status": video["status"]["privacyStatus"],
                }
            )
    return videos


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta videos publicados desde 01/09/2026.")
    parser.add_argument("--channels-file", type=Path, default=CHANNELS_FILE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("Defina YOUTUBE_API_KEY no ambiente ou no arquivo .env do projeto.")

    collection_end = datetime.now(UTC)
    client = build("youtube", "v3", developerKey=api_key)
    videos = []

    for source in parse_channels(args.channels_file):
        channel = resolve_channel(client, source["identifier"])
        video_ids = list_video_ids(client, channel["uploads_playlist_id"], collection_end)
        videos.extend(fetch_videos(client, video_ids, channel, source))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"videos_{collection_end.strftime('%Y%m%dT%H%M%SZ')}.json"
    payload = {
        "collected_at": collection_end.isoformat(),
        "collection_start": COLLECTION_START.isoformat(),
        "collection_end": collection_end.isoformat(),
        "video_count": len(videos),
        "videos": videos,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(videos)} videos salvos em {output_path}")


if __name__ == "__main__":
    main()