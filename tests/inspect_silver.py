#!/usr/bin/env python3
"""Inspeciona dados de Silver para entender estrutura."""

import pandas as pd
from pathlib import Path

silver_dir = Path('data/silver')

# Inspecionar videos_silver
v = pd.read_parquet(silver_dir / 'videos_silver.parquet')
print('=== VIDEOS SILVER ===')
print(f'Shape: {v.shape}')
print(f'Colunas: {list(v.columns)}')
print(f'Datas (sample):')
print(v[['video_id', 'published_at', 'view_count', 'like_count', 'comment_count']].head())
print(f'Range de datas: {v["published_at"].min()} até {v["published_at"].max()}')
print()

# Inspecionar comments_silver
c = pd.read_parquet(silver_dir / 'comments_silver.parquet')
print('=== COMMENTS SILVER ===')
print(f'Shape: {c.shape}')
print(f'Colunas: {list(c.columns)}')
print(f'Datas (sample):')
print(c[['comment_id', 'video_id', 'published_at', 'like_count']].head())
print(f'Range de datas: {c["published_at"].min()} até {c["published_at"].max()}')
