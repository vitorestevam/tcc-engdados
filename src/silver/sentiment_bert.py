"""Análise avançada de sentimento e emoções usando BERT."""

import logging
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Resultado da análise de sentimento e emoção."""
    
    sentimento: Literal["POSITIVO", "NEGATIVO", "NEUTRO"]
    emocao: Literal[
        "ENTUSIASMO", "ESPERANCA", "NEUTRO", 
        "RAIVA", "TRISTEZA", "DECEPCAO"
    ]
    score_sentimento: float
    score_emocao: float
    
    # Scores individuais por emoção
    score_entusiasmo: float
    score_esperanca: float
    score_neutro: float
    score_raiva: float
    score_tristeza: float
    score_decepcao: float


class SentimentBERT:
    """Análise de sentimento e emoções usando BERT multilíngue."""
    
    # Mapeamento de emoções para labels BERT
    EMOTION_MAPPING = {
        "ENTUSIASMO": ["positive", "enthusiasm", "joy", "excited"],
        "ESPERANCA": ["positive", "hope", "optimism", "confidence"],
        "NEUTRO": ["neutral", "factual"],
        "RAIVA": ["negative", "anger", "rage", "frustrated"],
        "TRISTEZA": ["negative", "sadness", "sad", "disappointed"],
        "DECEPCAO": ["negative", "disappointment", "letdown"],
    }
    
    def __init__(self, model_name: str = "nlptown/bert-base-multilingual-uncased-sentiment"):
        """
        Inicializa o modelo BERT.
        
        Args:
            model_name: Nome do modelo no Hugging Face Hub
        """
        try:
            from transformers import pipeline
            LOGGER.info(f"Carregando modelo BERT: {model_name}")
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=-1  # CPU; use device=0 para GPU
            )
            self.model_loaded = True
            LOGGER.info("Modelo BERT carregado com sucesso")
        except ImportError:
            LOGGER.error("transformers não instalado. Execute: pip install transformers torch")
            self.model_loaded = False
            self.pipeline = None
    
    def analyze(self, text: str | None) -> SentimentResult:
        """
        Analisa sentimento e emoção de um texto em português.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            SentimentResult com classificação, emoção e scores
        """
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            return self._neutral_result()
        
        if not self.model_loaded:
            LOGGER.warning("Modelo BERT não carregado, usando fallback")
            return self._fallback_sentiment(text)
        
        try:
            # Análise BERT
            result = self.pipeline(text[:512])[0]  # Limitar a 512 tokens (limite do BERT)
            
            # Extrair label e score
            label = result["label"].lower()
            score = result["score"]
            
            # Mapear para sentimento e emoção
            return self._map_bert_result(label, score, text)
            
        except Exception as e:
            LOGGER.warning(f"Erro na análise BERT: {e}. Usando fallback.")
            return self._fallback_sentiment(text)
    
    def _map_bert_result(self, label: str, score: float, text: str) -> SentimentResult:
        """Mapeia resultado BERT para nossa taxonomia de emoções."""
        # O modelo nlptown retorna: {"label": "5 stars/1 star/3 stars", "score": 0.95}
        
        label_clean = label.strip().lower()
        
        # Mapear labels de estrelas para sentimento
        if "5 star" in label_clean:
            sentimento = "POSITIVO"
            estrelas = 5
        elif "4 star" in label_clean:
            sentimento = "POSITIVO"
            estrelas = 4
        elif "3 star" in label_clean:
            sentimento = "NEUTRO"
            estrelas = 3
        elif "2 star" in label_clean:
            sentimento = "NEGATIVO"
            estrelas = 2
        elif "1 star" in label_clean:
            sentimento = "NEGATIVO"
            estrelas = 1
        else:
            sentimento = "NEUTRO"
            estrelas = 3
        
        # Determinar emoção específica baseada em keywords no texto e estrelas
        emocao, emoção_scores = self._classify_emotion(text, sentimento, estrelas)
        
        # Score de sentimento normalizado
        score_sentimento = score if sentimento == "POSITIVO" else (-score if sentimento == "NEGATIVO" else 0.0)
        
        # Retornar resultado com scores normalizados
        return SentimentResult(
            sentimento=sentimento,
            emocao=emocao,
            score_sentimento=float(score_sentimento),
            score_emocao=float(emoção_scores.get(emocao, score)),
            score_entusiasmo=float(emoção_scores.get("ENTUSIASMO", 0.0)),
            score_esperanca=float(emoção_scores.get("ESPERANCA", 0.0)),
            score_neutro=float(emoção_scores.get("NEUTRO", 0.0)),
            score_raiva=float(emoção_scores.get("RAIVA", 0.0)),
            score_tristeza=float(emoção_scores.get("TRISTEZA", 0.0)),
            score_decepcao=float(emoção_scores.get("DECEPCAO", 0.0)),
        )
    
    def _classify_emotion(self, text: str, sentimento: str, estrelas: int = 3) -> tuple[str, dict]:
        """Classifica emoção específica baseada em keywords e estrelas."""
        text_lower = text.lower()
        
        # Dicionário de palavras-chave por emoção (português)
        emotion_keywords = {
            "ENTUSIASMO": {"incrível", "adorei", "excelente", "maravilhoso", "genial", "fantástico", "show", "top", "demais", "ótimo", "bom", "melhor"},
            "ESPERANCA": {"espero", "esperança", "acredito", "confiança", "vai dar", "vai ser", "torço", "acreditar", "vencer", "ganhar", "vai vencer"},
            "RAIVA": {"ódio", "raiva", "odeio", "furioso", "indignado", "revoltado", "agressivo", "miserável", "horrível", "péssimo", "nojo"},
            "TRISTEZA": {"triste", "tristeza", "choro", "chorei", "devastado", "deprimido", "infeliz", "desanimado", "perdeu", "fracasso", "não acredito", "não posso"},
            "DECEPCAO": {"decepcionado", "decepção", "esperava", "esperava mais", "frustrado", "desapontado", "desiludido", "mais dele", "mais dele", "mais que"},
        }
        
        # Se o sentimento é NEUTRO, retornar score máximo para NEUTRO
        if sentimento == "NEUTRO":
            return "NEUTRO", {
                "NEUTRO": 1.0,
                "ENTUSIASMO": 0.0,
                "ESPERANCA": 0.0,
                "RAIVA": 0.0,
                "TRISTEZA": 0.0,
                "DECEPCAO": 0.0,
            }
        
        # Contar correspondências por emoção
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            emotion_scores[emotion] = float(count)
        
        # Se nenhuma keyword encontrada, usar lógica baseada em estrelas
        if max(emotion_scores.values()) == 0:
            if sentimento == "POSITIVO":
                if estrelas == 5:
                    emotion = "ENTUSIASMO"
                    emotion_scores["ENTUSIASMO"] = 0.8
                    emotion_scores["ESPERANCA"] = 0.2
                else:  # 4 stars
                    emotion = "ESPERANCA"
                    emotion_scores["ENTUSIASMO"] = 0.3
                    emotion_scores["ESPERANCA"] = 0.7
                emotion_scores["RAIVA"] = 0.0
                emotion_scores["TRISTEZA"] = 0.0
                emotion_scores["DECEPCAO"] = 0.0
            else:  # NEGATIVO
                if estrelas == 1:
                    emotion = "RAIVA"
                    emotion_scores["RAIVA"] = 0.5
                    emotion_scores["TRISTEZA"] = 0.3
                    emotion_scores["DECEPCAO"] = 0.2
                else:  # 2 stars
                    emotion = "DECEPCAO"
                    emotion_scores["RAIVA"] = 0.2
                    emotion_scores["TRISTEZA"] = 0.3
                    emotion_scores["DECEPCAO"] = 0.5
                emotion_scores["ENTUSIASMO"] = 0.0
                emotion_scores["ESPERANCA"] = 0.0
        else:
            # Emoção com maior score
            emotion = max(emotion_scores, key=emotion_scores.get)
            
            # Filtrar emoções incompatíveis com o sentimento
            if sentimento == "POSITIVO":
                emotion_scores["RAIVA"] = 0.0
                emotion_scores["TRISTEZA"] = 0.0
                emotion_scores["DECEPCAO"] = 0.0
                if emotion not in ["ENTUSIASMO", "ESPERANCA"]:
                    emotion = "ENTUSIASMO"
            else:  # NEGATIVO
                emotion_scores["ENTUSIASMO"] = 0.0
                emotion_scores["ESPERANCA"] = 0.0
                if emotion not in ["RAIVA", "TRISTEZA", "DECEPCAO"]:
                    emotion = "RAIVA"
        
        # Normalizar scores para [0, 1]
        max_score = max(emotion_scores.values(), default=1)
        if max_score > 0:
            emotion_scores = {k: v / max_score for k, v in emotion_scores.items()}
        else:
            emotion_scores = {k: 0.0 for k in emotion_scores}
        
        # Adicionar score de NEUTRO
        emotion_scores["NEUTRO"] = 0.0
        
        return emotion, emotion_scores
    
    def _fallback_sentiment(self, text: str) -> SentimentResult:
        """Fallback para análise simplista quando BERT não está disponível."""
        from .sentiment import analyze_sentiment as simple_analyze
        
        sentimento, score = simple_analyze(text)
        
        # Mapear para emoção usando keywords
        emocao, emoção_scores = self._classify_emotion(text, sentimento, 3)
        
        return SentimentResult(
            sentimento=sentimento,
            emocao=emocao,
            score_sentimento=float(score),
            score_emocao=float(emoção_scores.get(emocao, abs(score))),
            score_entusiasmo=float(emoção_scores.get("ENTUSIASMO", 0.0)),
            score_esperanca=float(emoção_scores.get("ESPERANCA", 0.0)),
            score_neutro=float(emoção_scores.get("NEUTRO", 0.0)),
            score_raiva=float(emoção_scores.get("RAIVA", 0.0)),
            score_tristeza=float(emoção_scores.get("TRISTEZA", 0.0)),
            score_decepcao=float(emoção_scores.get("DECEPCAO", 0.0)),
        )
    
    def _neutral_result(self) -> SentimentResult:
        """Retorna resultado neutro para texto vazio."""
        return SentimentResult(
            sentimento="NEUTRO",
            emocao="NEUTRO",
            score_sentimento=0.0,
            score_emocao=0.0,
            score_entusiasmo=0.0,
            score_esperanca=0.0,
            score_neutro=1.0,
            score_raiva=0.0,
            score_tristeza=0.0,
            score_decepcao=0.0,
        )
    
    def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        """Analisa múltiplos textos.
        
        Args:
            texts: Lista de textos a analisar
            
        Returns:
            Lista de SentimentResult
        """
        LOGGER.info(f"Analisando {len(texts)} textos com BERT...")
        return [self.analyze(text) for text in texts]


def add_sentiment_bert_to_comments(df: pd.DataFrame, use_bert: bool = True) -> pd.DataFrame:
    """
    Adiciona colunas de sentimento BERT a um DataFrame de comentários.
    
    Args:
        df: DataFrame com coluna 'text_clean' contendo os comentários
        use_bert: Se True, usa BERT; se False, usa análise simplista
        
    Returns:
        DataFrame com novas colunas de sentimento e emoção
    """
    LOGGER.info(f"Analisando sentimento de {len(df)} comentários {'com BERT' if use_bert else 'com análise simplista'}...")
    
    analyzer = SentimentBERT() if use_bert else None
    
    if analyzer and analyzer.model_loaded:
        # Usar BERT
        results = df["text_clean"].apply(analyzer.analyze)
    else:
        # Fallback para análise simplista
        LOGGER.info("Usando análise simplista de sentimento (fallback)")
        analyzer = SentimentBERT()
        results = df["text_clean"].apply(analyzer.analyze)
    
    # Desempacotar resultados
    df["sentimento"] = results.apply(lambda x: x.sentimento)
    df["emocao"] = results.apply(lambda x: x.emocao)
    df["score_sentimento"] = results.apply(lambda x: x.score_sentimento)
    df["score_emocao"] = results.apply(lambda x: x.score_emocao)
    df["score_entusiasmo"] = results.apply(lambda x: x.score_entusiasmo)
    df["score_esperanca"] = results.apply(lambda x: x.score_esperanca)
    df["score_neutro"] = results.apply(lambda x: x.score_neutro)
    df["score_raiva"] = results.apply(lambda x: x.score_raiva)
    df["score_tristeza"] = results.apply(lambda x: x.score_tristeza)
    df["score_decepcao"] = results.apply(lambda x: x.score_decepcao)
    
    # Contar distribuição
    sentiment_dist = df["sentimento"].value_counts()
    emotion_dist = df["emocao"].value_counts()
    
    LOGGER.info(f"\nDistribuição de sentimentos:\n{sentiment_dist}")
    LOGGER.info(f"\nDistribuição de emoções:\n{emotion_dist}")
    
    return df
