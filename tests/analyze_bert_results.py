import sys
import os
import pandas as pd
import numpy as np

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("="*80)
print("ANÁLISE COMPLETA: DISTRIBUIÇÃO DE SENTIMENTOS E EMOÇÕES")
print("="*80)

# Carregar dados processados
df = pd.read_parquet('data/silver/comments_silver.parquet')
df_emocoes = pd.read_parquet('data/gold/emocoes_distribuicao.parquet')

print(f"\n📊 DATASET")
print(f"{'─'*80}")
print(f"Total de comentários: {len(df):,}")
print(f"Colunas: {list(df.columns)}")

# Análise de Sentimentos
print(f"\n📈 DISTRIBUIÇÃO DE SENTIMENTOS")
print(f"{'─'*80}")
sentimentos = df['sentimento'].value_counts()
for sentimento, count in sentimentos.items():
    pct = (count / len(df)) * 100
    print(f"{sentimento:12} : {count:5} ({pct:5.1f}%) │ {'█' * int(pct/2)}")

# Análise de Emoções
print(f"\n🎭 DISTRIBUIÇÃO DE EMOÇÕES")
print(f"{'─'*80}")
emocoes = df['emocao'].value_counts()
for emocao, count in emocoes.items():
    pct = (count / len(df)) * 100
    print(f"{emocao:12} : {count:5} ({pct:5.1f}%) │ {'█' * int(pct/2)}")

# Análise cruzada Sentimento x Emoção
print(f"\n🔀 RELAÇÃO SENTIMENTO × EMOÇÃO")
print(f"{'─'*80}")
cross_tab = pd.crosstab(df['sentimento'], df['emocao'], margins=True)
print(cross_tab)

# Score médio por emoção
print(f"\n⭐ SCORES MÉDIOS POR EMOÇÃO")
print(f"{'─'*80}")
emocoes_score = df.groupby('emocao')[
    ['score_entusiasmo', 'score_esperanca', 'score_raiva', 'score_tristeza', 'score_decepcao']
].mean()
for emocao in emocoes_score.index:
    avg = emocoes_score.loc[emocao].max()
    print(f"{emocao:12} : Confiança média = {avg:.3f}")

# Análise de qualidade
print(f"\n✅ VALIDAÇÃO DE QUALIDADE")
print(f"{'─'*80}")

# Verificar se POSITIVO está associado às emoções positivas
positivos = df[df['sentimento'] == 'POSITIVO']
pos_corretos = len(positivos[positivos['emocao'].isin(['ENTUSIASMO', 'ESPERANCA'])])
print(f"POSITIVO → Emoções esperadas (ENTUSIASMO/ESPERANCA): {pos_corretos}/{len(positivos)} ({100*pos_corretos/len(positivos):.1f}%)")

# Verificar se NEGATIVO está associado às emoções negativas
negativos = df[df['sentimento'] == 'NEGATIVO']
neg_corretos = len(negativos[negativos['emocao'].isin(['RAIVA', 'TRISTEZA', 'DECEPCAO'])])
print(f"NEGATIVO → Emoções esperadas (RAIVA/TRISTEZA/DECEPCAO): {neg_corretos}/{len(negativos)} ({100*neg_corretos/len(negativos):.1f}%)")

# Verificar se NEUTRO está bem classificado
neutros = df[df['sentimento'] == 'NEUTRO']
neutro_corretos = len(neutros[neutros['emocao'] == 'NEUTRO'])
print(f"NEUTRO → Emoção NEUTRO: {neutro_corretos}/{len(neutros)} ({100*neutro_corretos/len(neutros):.1f}%)")

# Score de confiança geral
print(f"\n🎯 CONFIANÇA MÉDIA (Score de Emoção)")
print(f"{'─'*80}")
print(f"Score médio de emoção: {df['score_emocao'].mean():.3f} / 1.000")
print(f"Score mínimo: {df['score_emocao'].min():.3f}")
print(f"Score máximo: {df['score_emocao'].max():.3f}")

# Top comentários por emoção
print(f"\n🔝 EXEMPLOS DE COMENTÁRIOS")
print(f"{'─'*80}")
for emocao in ['ENTUSIASMO', 'RAIVA', 'ESPERANCA', 'TRISTEZA', 'DECEPCAO', 'NEUTRO']:
    exemplos = df[df['emocao'] == emocao]['text_clean'].unique()[:1]
    if len(exemplos) > 0:
        print(f"{emocao:12}: \"{exemplos[0][:60]}...\"")

print(f"\n{'='*80}")
print(f"✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
print(f"{'='*80}\n")
