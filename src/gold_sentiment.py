"""Classificacao de sentimento e emocao para comentarios da camada Gold."""

import os
from dataclasses import asdict, dataclass

import pandas as pd

DEFAULT_MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"
EMOTIONS = (
    "ENTUSIASMO",
    "ESPERANCA",
    "NEUTRO",
    "RAIVA",
    "TRISTEZA",
    "DECEPCAO",
)
EMOTION_KEYWORDS = {
    "ENTUSIASMO": {
        "incrivel", "adorei", "excelente", "maravilhoso", "genial", "fantastico",
        "show", "top", "demais", "otimo", "bom", "melhor",
    },
    "ESPERANCA": {
        "espero", "esperanca", "acredito", "confianca", "vai dar", "vai ser",
        "torco", "acreditar", "vencer", "ganhar", "vai vencer",
    },
    "RAIVA": {
        "odio", "raiva", "odeio", "furioso", "indignado", "revoltado", "agressivo",
        "miseravel", "horrivel", "pessimo", "nojo",
    },
    "TRISTEZA": {
        "triste", "tristeza", "choro", "chorei", "devastado", "deprimido", "infeliz",
        "desanimado", "perdeu", "fracasso", "nao acredito", "nao posso",
    },
    "DECEPCAO": {
        "decepcionado", "decepcao", "esperava", "esperava mais", "frustrado",
        "desapontado", "desiludido",
    },
}


@dataclass(frozen=True)
class SentimentResult:
    sentimento: str
    emocao: str
    score_sentimento: float
    score_emocao: float
    score_entusiasmo: float
    score_esperanca: float
    score_neutro: float
    score_raiva: float
    score_tristeza: float
    score_decepcao: float


class BertSentimentAnalyzer:
    """Classifica sentimento com BERT multilíngue e deriva a emoção dominante."""

    def __init__(self, model_name: str | None = None) -> None:
        try:
            from transformers import pipeline
        except ImportError as error:
            raise RuntimeError(
                "Dependencia ausente: instale transformers e torch para executar a camada Gold."
            ) from error

        self._pipeline = pipeline(
            "sentiment-analysis",
            model=model_name or os.getenv("SENTIMENT_MODEL_NAME", DEFAULT_MODEL_NAME),
            device=-1,
        )

    def analyze_batch(self, texts: list[str], batch_size: int = 32) -> list[SentimentResult]:
        results = [self._neutral_result() for _ in texts]
        positions = [index for index, text in enumerate(texts) if text.strip()]
        if not positions:
            return results

        predictions = self._pipeline(
            [texts[index] for index in positions],
            truncation=True,
            batch_size=batch_size,
        )
        for index, prediction in zip(positions, predictions, strict=True):
            results[index] = self._map_prediction(texts[index], prediction)
        return results

    def _map_prediction(self, text: str, prediction: dict[str, object]) -> SentimentResult:
        label = str(prediction["label"]).lower()
        confidence = float(prediction["score"])
        if "5 star" in label:
            sentiment, stars = "POSITIVO", 5
        elif "4 star" in label:
            sentiment, stars = "POSITIVO", 4
        elif "2 star" in label:
            sentiment, stars = "NEGATIVO", 2
        elif "1 star" in label:
            sentiment, stars = "NEGATIVO", 1
        else:
            sentiment, stars = "NEUTRO", 3

        emotion, scores = self._classify_emotion(text, sentiment, stars)
        sentiment_score = confidence if sentiment == "POSITIVO" else -confidence if sentiment == "NEGATIVO" else 0.0
        return SentimentResult(
            sentimento=sentiment,
            emocao=emotion,
            score_sentimento=sentiment_score,
            score_emocao=scores[emotion],
            score_entusiasmo=scores["ENTUSIASMO"],
            score_esperanca=scores["ESPERANCA"],
            score_neutro=scores["NEUTRO"],
            score_raiva=scores["RAIVA"],
            score_tristeza=scores["TRISTEZA"],
            score_decepcao=scores["DECEPCAO"],
        )

    def _classify_emotion(self, text: str, sentiment: str, stars: int) -> tuple[str, dict[str, float]]:
        if sentiment == "NEUTRO":
            return "NEUTRO", {emotion: float(emotion == "NEUTRO") for emotion in EMOTIONS}

        normalized_text = self._normalize(text)
        scores = {
            emotion: float(sum(keyword in normalized_text for keyword in keywords))
            for emotion, keywords in EMOTION_KEYWORDS.items()
        }
        scores["NEUTRO"] = 0.0

        if not any(scores.values()):
            return self._default_emotion_scores(sentiment, stars)

        allowed = {"ENTUSIASMO", "ESPERANCA"} if sentiment == "POSITIVO" else {"RAIVA", "TRISTEZA", "DECEPCAO"}
        for emotion in set(EMOTIONS) - allowed:
            scores[emotion] = 0.0
        emotion = max(allowed, key=scores.__getitem__)
        maximum = scores[emotion]
        if maximum == 0:
            return self._default_emotion_scores(sentiment, stars)
        return emotion, {name: score / maximum for name, score in scores.items()}

    @staticmethod
    def _default_emotion_scores(sentiment: str, stars: int) -> tuple[str, dict[str, float]]:
        scores = {emotion: 0.0 for emotion in EMOTIONS}
        if sentiment == "POSITIVO":
            emotion = "ENTUSIASMO" if stars == 5 else "ESPERANCA"
            scores.update({"ENTUSIASMO": 0.8 if stars == 5 else 0.3, "ESPERANCA": 0.2 if stars == 5 else 0.7})
        else:
            emotion = "RAIVA" if stars == 1 else "DECEPCAO"
            scores.update(
                {
                    "RAIVA": 0.5 if stars == 1 else 0.2,
                    "TRISTEZA": 0.3,
                    "DECEPCAO": 0.2 if stars == 1 else 0.5,
                }
            )
        return emotion, scores

    @staticmethod
    def _normalize(text: str) -> str:
        return text.lower().translate(str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc"))

    @staticmethod
    def _neutral_result() -> SentimentResult:
        return SentimentResult(
            sentimento="NEUTRO",
            emocao="NEUTRO",
            score_sentimento=0.0,
            score_emocao=1.0,
            score_entusiasmo=0.0,
            score_esperanca=0.0,
            score_neutro=1.0,
            score_raiva=0.0,
            score_tristeza=0.0,
            score_decepcao=0.0,
        )


def add_sentiment_to_comments(comments: pd.DataFrame) -> pd.DataFrame:
    if "text_clean" not in comments:
        raise ValueError("A coluna text_clean e obrigatoria para a analise de sentimento.")

    enriched = comments.copy()
    texts = enriched["text_clean"].fillna("").astype(str).tolist()
    results = BertSentimentAnalyzer().analyze_batch(texts)
    result_frame = pd.DataFrame(
        [asdict(result) for result in results],
        index=enriched.index,
        columns=SentimentResult.__dataclass_fields__,
    )
    return pd.concat([enriched, result_frame], axis=1)