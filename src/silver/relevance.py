"""Leitura e aplicacao das regras de relevancia eleitoral."""

import json
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RELEVANCE_FILE = PROJECT_ROOT / "settings" / "relevance_terms.json"


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def parse_relevance_terms(path: Path | str) -> list[dict[str, str]]:
    path = Path(path)
    try:
        terms = json.loads(path.read_text(encoding="utf-8"))["relevance_terms"]
    except (OSError, json.JSONDecodeError, KeyError) as error:
        raise ValueError(f"Nao foi possivel ler termos de relevancia em {path}.") from error
    if not isinstance(terms, list):
        raise ValueError(f"{path.name} deve conter uma lista na chave 'relevance_terms'.")
    return [
        {
            "tipo": term["type"],
            "rotulo": term["label"],
            "termo": normalize_text(term["term"]),
        }
        for term in terms
    ]


def is_relevant(title: str, description: str, terms: list[dict[str, str]]) -> tuple[bool, list[str]]:
    searchable_text = normalize_text(f"{title or ''} {description or ''}")
    matched_terms = [term["termo"] for term in terms if term["termo"] in searchable_text]
    return bool(matched_terms), matched_terms