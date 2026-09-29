import sys
import os
import pandas as pd

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('='*70)
print('RESULTADO: Comentários com BERT')
print('='*70)
df_comments = pd.read_parquet('data/silver/comments_silver.parquet')
print(f'Total de registros: {len(df_comments)}')
cols_novo = [c for c in df_comments.columns if c.startswith('score_') or c in ['sentimento', 'emocao']]
print(f'Novas colunas BERT: {cols_novo}')
print()
print('Primeiros 3 registros:')
for i, row in df_comments.head(3).iterrows():
    print(f'{i+1}. "{row["text_clean"][:40]}..."')
    print(f'   → Sentimento: {row["sentimento"]} (score: {row["score_sentimento"]:.3f})')
    print(f'   → Emoção: {row["emocao"]} (score: {row["score_emocao"]:.3f})')

print()
print('='*70)
print('TABELA GOLD: Distribuição de Emoções')
print('='*70)
df_emocoes = pd.read_parquet('data/gold/emocoes_distribuicao.parquet')
print(df_emocoes.to_string(index=False))
