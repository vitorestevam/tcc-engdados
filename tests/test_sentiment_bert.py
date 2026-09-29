#!/usr/bin/env python
"""Script de teste para validar análise BERT de sentimento."""

import sys
import os
import time

# Adicionar diretório raiz ao path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.silver.sentiment_bert import SentimentBERT

# Exemplos de teste
TEST_TEXTS = [
    ("Ciro é incrível!", "POSITIVO", "ENTUSIASMO"),
    ("Espero que vença", "POSITIVO", "ESPERANCA"),
    ("Que governo horrível", "NEGATIVO", "RAIVA"),
    ("Não acredito que perdeu", "NEGATIVO", "TRISTEZA"),
    ("Esperava mais dele", "NEGATIVO", "DECEPCAO"),
    ("O candidato recebeu 500 votos", "NEUTRO", "NEUTRO"),
]


def test_sentiment_bert():
    """Testa a análise de sentimento BERT."""
    print("=" * 70)
    print("TESTE: Análise de Sentimento com BERT")
    print("=" * 70)
    
    # Inicializar analisador
    print("\n1. Carregando modelo BERT...")
    start = time.time()
    analyzer = SentimentBERT()
    elapsed = time.time() - start
    print(f"   ✓ Modelo carregado em {elapsed:.2f}s")
    
    if not analyzer.model_loaded:
        print("   ✗ Modelo não carregou. Instale as dependências:")
        print("     pip install transformers torch")
        return False
    
    # Testar análise
    print("\n2. Analisando textos de teste...")
    print("-" * 70)
    
    all_correct = True
    total_time = 0
    
    for text, expected_sentiment, expected_emotion in TEST_TEXTS:
        start = time.time()
        result = analyzer.analyze(text)
        elapsed = time.time() - start
        total_time += elapsed
        
        # Verificar resultado
        sentiment_ok = result.sentimento == expected_sentiment
        emotion_ok = result.emocao == expected_emotion
        
        status = "✓" if (sentiment_ok and emotion_ok) else "✗"
        all_correct = all_correct and sentiment_ok and emotion_ok
        
        print(f"\n{status} Texto: {text}")
        print(f"  Sentimento: {result.sentimento} (esperado: {expected_sentiment})")
        print(f"  Emoção: {result.emocao} (esperado: {expected_emotion})")
        print(f"  Score sentimento: {result.score_sentimento:.3f}")
        print(f"  Score emoção: {result.score_emocao:.3f}")
        print(f"  Tempo: {elapsed*1000:.1f}ms")
    
    print("\n" + "-" * 70)
    print(f"Tempo total: {total_time:.2f}s ({total_time*1000/len(TEST_TEXTS):.1f}ms/texto)")
    
    # Relatório final
    print("\n3. Relatório Final")
    print("-" * 70)
    if all_correct:
        print("✓ Todos os testes passaram!")
        return True
    else:
        print("✗ Alguns testes falharam. Verifique a lógica de classificação.")
        return False


def test_batch_analysis():
    """Testa análise em batch."""
    print("\n\n" + "=" * 70)
    print("TESTE: Análise em Batch")
    print("=" * 70)
    
    analyzer = SentimentBERT()
    
    batch = [text for text, _, _ in TEST_TEXTS]
    
    print(f"\nAnalisando batch de {len(batch)} textos...")
    start = time.time()
    results = analyzer.analyze_batch(batch)
    elapsed = time.time() - start
    
    print(f"✓ Batch analisado em {elapsed:.2f}s ({elapsed/len(batch):.3f}s/texto)")
    
    for i, (text, result) in enumerate(zip(batch, results), 1):
        print(f"\n{i}. {text}")
        print(f"   {result.sentimento} / {result.emocao} (score: {result.score_sentimento:.3f})")
    
    return True


if __name__ == "__main__":
    try:
        success = test_sentiment_bert()
        if success:
            test_batch_analysis()
            print("\n✓ Todos os testes completados com sucesso!")
            sys.exit(0)
        else:
            print("\n✗ Alguns testes falharam")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
