#!/usr/bin/env python3
"""Coleta metadados de videos do YouTube para a camada Bronze."""

import argparse
import json
import logging
import os
from datetime import UTC, datetime, time
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHANNELS_FILE = PROJECT_ROOT / "settings" / "channels.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "videos"
LOGGER = logging.getLogger(__name__)


def parse_collection_date(value: str, is_end: bool = False) -> datetime:
    try:
        parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise argparse.ArgumentTypeError("Use a data no formato YYYY-MM-DD.") from error
    return datetime.combine(parsed_date, time.max if is_end else time.min, tzinfo=UTC)


def to_utc_datetime(value: datetime | str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("As datas de coleta devem usar ISO 8601.") from error
    if value.tzinfo is None:
        raise ValueError("As datas de coleta devem incluir fuso horario.")
    return value.astimezone(UTC)


def parse_channels(path: Path | str) -> list[dict[str, str]]:
    path = Path(path)
    try:
        channels = json.loads(path.read_text(encoding="utf-8"))["channels"]
    except (OSError, json.JSONDecodeError, KeyError) as error:
        raise ValueError(f"Nao foi possivel ler canais em {path}.") from error
    if not isinstance(channels, list):
        raise ValueError(f"{path.name} deve conter uma lista na chave 'channels'.")
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


def list_video_ids(
    client, playlist_id: str, collection_start: datetime, collection_end: datetime
) -> list[tuple[str, datetime]]:
    video_ids = []
    page_token = None
    page_count = 0

    while True:
        page_count += 1
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
            if collection_start <= published_at <= collection_end:
                video_ids.append((item["contentDetails"]["videoId"], published_at))

        page_token = response.get("nextPageToken")
        if not page_token:
            LOGGER.info("Playlist processada: %s paginas, %s videos na janela", page_count, len(video_ids))
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


def collect_videos(
    channels_file: Path | str,
    output_file: Path | str,
    collection_start: datetime | str,
    collection_end: datetime | str,
) -> str:
    channels_file = Path(channels_file)
    output_file = Path(output_file)
    collection_start = to_utc_datetime(collection_start)
    collection_end = to_utc_datetime(collection_end)
    if collection_start > collection_end:
        raise ValueError("A data inicial deve ser anterior ou igual a data final.")
    collected_at = datetime.now(UTC)

    LOGGER.info("Iniciando coleta de videos: canais=%s saida=%s", channels_file, output_file)
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        LOGGER.error("YOUTUBE_API_KEY nao foi encontrada no ambiente ou em %s", PROJECT_ROOT / ".env")
        raise RuntimeError("Defina YOUTUBE_API_KEY no ambiente ou no arquivo .env do projeto.")

    LOGGER.info(
        "Criando cliente YouTube para janela %s a %s",
        collection_start.isoformat(),
        collection_end.isoformat(),
    )
    client = build("youtube", "v3", developerKey=api_key)
    videos = []

    for source in parse_channels(channels_file):
        LOGGER.info("Resolvendo canal: fonte=%s identificador=%s", source["source"], source["identifier"])
        channel = resolve_channel(client, source["identifier"])
        LOGGER.info("Canal resolvido: titulo=%s id=%s", channel["channel_title"], channel["channel_id"])
        video_ids = list_video_ids(
            client,
            channel["uploads_playlist_id"],
            collection_start,
            collection_end,
        )
        channel_videos = fetch_videos(client, video_ids, channel, source)
        videos.extend(channel_videos)
        LOGGER.info("Metadados coletados: fonte=%s videos=%s", source["source"], len(channel_videos))

    payload = {
        "collected_at": collected_at.isoformat(),
        "collection_start": collection_start.isoformat(),
        "collection_end": collection_end.isoformat(),
        "video_count": len(videos),
        "videos": videos,
    }
    try:
        LOGGER.info("Preparando diretorio de saida: %s", output_file.parent)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Gravando arquivo de videos: %s", output_file)
        output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as error:
        LOGGER.exception("Falha ao gravar coleta de videos em %s", output_file)
        raise RuntimeError(f"Nao foi possivel gravar o arquivo de videos: {output_file}") from error
    LOGGER.info("Coleta de videos concluida: videos=%s arquivo=%s", len(videos), output_file)
    return str(output_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta videos publicados em uma janela de datas UTC.")
    parser.add_argument("--channels-file", type=Path, default=CHANNELS_FILE)
    parser.add_argument("--start-date", required=True, type=parse_collection_date, help="Data inicial UTC (YYYY-MM-DD)")
    parser.add_argument(
        "--end-date",
        required=True,
        type=lambda value: parse_collection_date(value, is_end=True),
        help="Data final UTC inclusiva (YYYY-MM-DD)",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    output_group.add_argument("--output-file", type=Path, help="Arquivo JSON de saida da execucao")
    args = parser.parse_args()

    output_path = args.output_file or (
        args.output_dir / f"videos_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    print(
        f"Videos salvos em {collect_videos(
            args.channels_file,
            output_path,
            args.start_date,
            args.end_date,
        )}"
    )


if __name__ == "__main__":
    main()