"""Classificacao de sentimento para comentarios da camada Gold."""

import pandas as pd
from textblob import TextBlob


def classify_sentiment(text: str) -> tuple[str, float]:
    score = TextBlob(text or "").sentiment.polarity
    if score > 0:
        return "POSITIVO", score
    if score < 0:
        return "NEGATIVO", score
    return "NEUTRO", score


def add_sentiment_to_comments(comments: pd.DataFrame) -> pd.DataFrame:
    enriched = comments.copy()
    sentiment = enriched["text_clean"].fillna("").map(classify_sentiment)
    enriched["sentimento"] = sentiment.map(lambda value: value[0])
    enriched["score_sentimento"] = sentiment.map(lambda value: value[1])
    return enriched