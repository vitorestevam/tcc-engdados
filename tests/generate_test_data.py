import sys
import os
import pandas as pd
import numpy as np
import random

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Lista de comentários realistas sobre eleição/políticos no Ceará
comentarios_positivos = [
    "Ciro é incrível!",
    "Adorei a campanha do Camilo",
    "Muito bom mesmo!",
    "Espero que vença",
    "Excelente proposta",
    "Que candidato bom!",
    "Voto com certeza",
    "Amei!",
    "Fantástico!",
    "Melhor opção",
    "Vai dar certo",
    "Confiança total",
    "Ótimo governo",
    "Perfeito!",
    "Maravilhoso",
]

comentarios_negativos = [
    "Que governo horrível",
    "Péssimo!",
    "Não acredito que perdeu",
    "Que decepção",
    "Horrível",
    "Que vexame",
    "Terrível",
    "Ódio!",
    "Não voto mais",
    "Que desastre",
    "Frustrante",
    "Muito ruim",
    "Decepcionante",
    "Que tristeza",
    "Fracasso total",
]

comentarios_neutros = [
    "O candidato recebeu 500 votos",
    "A eleição acontece em 2026",
    "Ceará tem 9 milhões de habitantes",
    "A campanha começou em janeiro",
    "O debate foi na TV",
    "Votei no candidato X",
    "Fiz meu voto hoje",
    "A votação termina às 17h",
    "Existe uma urna eletrônica",
    "O resultado sai hoje à noite",
    "Ceará é o estado",
    "Voto é importante",
    "Democracia é assim",
    "A eleição é importante",
    "Votação aconteceu",
]

# Gerar 1000 comentários aleatórios para teste
np.random.seed(42)
random.seed(42)

num_comentarios = 1000
comentarios = []

for i in range(num_comentarios):
    tipo = np.random.choice(['positivo', 'negativo', 'neutro'], p=[0.4, 0.35, 0.25])
    
    if tipo == 'positivo':
        texto = random.choice(comentarios_positivos)
    elif tipo == 'negativo':
        texto = random.choice(comentarios_negativos)
    else:
        texto = random.choice(comentarios_neutros)
    
    comentarios.append({
        'id_comentario': i + 1,
        'texto': texto,
        'text_clean': texto,
        'data_coleta': pd.Timestamp('2026-09-29') + pd.Timedelta(minutes=np.random.randint(0, 1440))
    })

df = pd.DataFrame(comentarios)
df.to_parquet('data/silver/comments_silver.parquet', index=False)

print(f'✓ Dataset gerado com {len(df)} comentários')
print(f'\nDistribuição esperada:')
print(f'  - Positivos (40%): {int(len(df) * 0.4)} comentários')
print(f'  - Negativos (35%): {int(len(df) * 0.35)} comentários')
print(f'  - Neutros (25%): {int(len(df) * 0.25)} comentários')
