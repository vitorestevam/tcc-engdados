"""Análise de sentimento para comentários."""

import logging
from typing import Literal

import pandas as pd

LOGGER = logging.getLogger(__name__)


def analyze_sentiment(text: str | None) -> tuple[Literal["POSITIVO", "NEGATIVO", "NEUTRO"], float]:
    """
    Classifica sentimento de um texto em português.
    
    Args:
        text: Texto a ser analisado
        
    Returns:
        Tupla (classificação, score) onde:
        - classificação: "POSITIVO", "NEGATIVO" ou "NEUTRO"
        - score: valor entre -1 (muito negativo) e +1 (muito positivo)
    """
    if not text or not isinstance(text, str) or len(text.strip()) == 0:
        return "NEUTRO", 0.0
    
    try:
        from textblob import TextBlob
    except ImportError:
        LOGGER.warning("TextBlob não instalado, usando análise simplista")
        return _analyze_sentiment_simple(text)
    
    try:
        # TextBlob com suporte a português
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 a +1
        
        if polarity > 0.1:
            return "POSITIVO", float(polarity)
        elif polarity < -0.1:
            return "NEGATIVO", float(polarity)
        else:
            return "NEUTRO", float(polarity)
    except Exception as e:
        LOGGER.warning(f"Erro ao analisar sentimento: {e}")
        return _analyze_sentiment_simple(text)


def _analyze_sentiment_simple(text: str) -> tuple[Literal["POSITIVO", "NEGATIVO", "NEUTRO"], float]:
    """Análise simplista baseada em palavras-chave em português."""
    text_lower = text.lower()
    
    # Palavras positivas
    positive_words = {
        "ótimo", "excelente", "maravilhoso", "incrível", "adorei", "perfeito",
        "bom", "legal", "bacana", "show", "demais", "top", "sensacional",
        "fantástico", "genial", "espetacular", "brilhante", "formidável"
    }
    
    # Palavras negativas
    negative_words = {
        "péssimo", "horrível", "terrível", "ruim", "detestei", "desgosto",
        "mal", "chato", "decepcionante", "fraco", "desagradável", "nojento",
        "repugnante", "detestável", "miserável", "patético", "ridículo"
    }
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    score = (positive_count - negative_count) / max(positive_count + negative_count, 1)
    
    if positive_count > negative_count:
        return "POSITIVO", min(score, 1.0)
    elif negative_count > positive_count:
        return "NEGATIVO", max(score, -1.0)
    else:
        return "NEUTRO", 0.0


def add_sentiment_to_comments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona colunas de sentimento a um DataFrame de comentários.
    
    Args:
        df: DataFrame com coluna 'text_clean' contendo os comentários
        
    Returns:
        DataFrame com novas colunas:
        - sentimento: classificação (POSITIVO, NEGATIVO, NEUTRO)
        - score_sentimento: score de -1 a +1
    """
    LOGGER.info("Analisando sentimento de comentários...")
    
    # Aplicar análise para cada comentário
    results = df["text_clean"].apply(analyze_sentiment)
    
    # Desempacotar resultados
    df["sentimento"] = results.apply(lambda x: x[0])
    df["score_sentimento"] = results.apply(lambda x: x[1])
    
    # Contar distribuição
    dist = df["sentimento"].value_counts()
    LOGGER.info(f"Distribuição de sentimento:\n{dist}")
    
    return df
