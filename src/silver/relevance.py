"""Leitura e aplicacao das regras de relevancia eleitoral."""

import unicodedata
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RELEVANCE_FILE = PROJECT_ROOT / "settings" / "relevancia_eleicao.txt"


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def parse_relevance_terms(path: Path) -> list[dict[str, str]]:
    terms = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3 or not parts[0] or not parts[2]:
            raise ValueError(f"{path.name}:{line_number} deve usar: tipo|rotulo|termo")
        terms.append({"tipo": parts[0], "rotulo": parts[1], "termo": normalize_text(parts[2])})
    if not terms:
        raise ValueError(f"{path.name} nao possui termos de relevancia configurados")
    return terms


def is_relevant(title: str, description: str, terms: list[dict[str, str]]) -> tuple[bool, list[str]]:
    searchable_text = normalize_text(f"{title or ''} {description or ''}")
    matched_terms = [term["termo"] for term in terms if term["termo"] in searchable_text]
    return bool(matched_terms), matched_terms