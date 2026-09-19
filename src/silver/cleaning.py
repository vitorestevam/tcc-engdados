"""Normalizacao de texto e datas para a camada Silver."""

import re
import unicodedata


def clean_text(value: object) -> str:
    """Converte texto para uma forma consistente sem remover acentos."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    return re.sub(r"\s+", " ", text).strip()


def to_utc(value: object):
    """Converte timestamps em texto para objetos pandas UTC."""
    import pandas as pd

    return pd.to_datetime(value, utc=True)