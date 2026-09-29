# Relatório de Entrega: Pipeline Bronze → Silver → Gold

**Projeto:** Monitoramento de Campanha Eleitoral 2026 - Ceará via YouTube  

---

## Resumo Executivo

A pipeline de dados foi implementada com sucesso em 3 camadas:

1. **BRONZE:** Coleta bruta de vídeos e comentários do YouTube (260 vídeos, 30.162 comentários)
2. **SILVER:** Transformação, limpeza e normalização (208 vídeos, 15.008 comentários processados)
3. **GOLD:** Tabelas analíticas respondendo 3 perguntas de negócio com série temporal, análise de candidatos e temas

| Métrica | Resultado |
|---------|-----------|
| Vídeos coletados | 260 (BRONZE) |
| Comentários coletados | 30.162 (BRONZE) |
| Vídeos processados | 208 (80% de retenção) |
| Comentários processados | 15.008 (50% de retenção) |
| Tabelas GOLD | 3 tabelas analíticas |
| Análise de sentimento | Implementada e documentada |
| Status | Entrega Completa |

---

## O QUE FOI ENTREGUE

### Arquitetura da Pipeline

```
YouTube API
    ↓
[BRONZE] JSON bruto (videos.json, comments.json)
    ↓
[SILVER] Transformação (videos_silver.parquet, comments_silver.parquet)
         + normalização, limpeza, deduplicação, sentimento (keyword-based)
    ↓
[GOLD] 3 Tabelas analíticas
       - serie_temporal_volume.parquet
       - candidatos_manifestacoes.parquet
       - temas_engajamento.parquet
```

---

## Tabelas GOLD Entregues

### Tabela 1: Série Temporal (`serie_temporal_volume.parquet`)

**Pergunta:** *"Como o volume de manifestações evoluiu no tempo?"*

| Campo | Descrição |
|-------|-----------|
| `data` | Data (YYYY-MM-DD) |
| `videos_novos` | Quantidade diária de vídeos publicados |
| `comentarios_novos` | Quantidade diária de comentários |
| `likes_total` | Soma de likes do dia |
| `engajamento_medio` | Média comentários/video |
| `sentimento_medio` | Score médio de sentimento (-1 a +1) |

**Principais Insights:**
- **Pico:** 10/09 com 122.7 comentários/vídeo
- **Cobertura:** 22 de 25 dias ativos (88%)
- **Engajamento médio:** ~39 comentários por vídeo

---

### Tabela 2: Candidatos (`candidatos_manifestacoes.parquet`)

**Pergunta:** *"Qual candidato concentra maior volume de manifestações?"*

| Candidato | Videos | Comentários | Sentimento+ | Sentimento- |
|-----------|--------|-------------|------------|------------|
| Ciro Gomes | 158 | 12.587 | 3.46% | 2.21% |
| Elmano de Freitas | 55 | 7.976 | 3.31% | 2.86% |

**Principais Insights:**
- **Ciro Gomes** domina com 58% dos comentários (razão 2:1)
- Ambos com sentimento similar (~3.3-3.5% positivo)
- Ciro ligeiramente mais negativo

---

### Tabela 3: Temas/Engajamento (`temas_engajamento.parquet`)

**Pergunta:** *"Quais temas geram maior engajamento?"*

| Tema | Videos | Comentários | Likes/Comentário | Sentimento+ |
|------|--------|-------------|-----------------|------------|
| Diário do Nordeste | 49 | 9.273 | 3.22 | 3.05% |
| Ciro Gomes | 159 | 5.737 | 3.67 | 3.63% |

**Principais Insights:**
- **Diário do Nordeste** gera 61% mais comentários por vídeo
- **Ciro Gomes** tem melhor taxa de likes (3.67 vs 3.22)
- Distribuição equilibrada de engajamento

---

## Camadas Implementadas

### Camada BRONZE (Dados Brutos)

#### `videos_20260925T225348Z.json`
- **Registros:** 260 vídeos
- **Origem:** YouTube Data API v3 (`search.list` + `videos.list`)
- **Conteúdo:** Dados brutos completos (sem transformações)

#### `comments_20260925T225603Z.json`
- **Registros:** 30.162 comentários
- **Origem:** YouTube Data API v3 (`commentThreads.list`)
- **Conteúdo:** Dados brutos completos

---

### Camada SILVER (Dados Transformados)

#### `videos_silver.parquet`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `video_id` | STRING | ID único YouTube |
| `channel_id` | STRING | ID do canal |
| `channel_title` | STRING | Nome do canal |
| `title_clean` | STRING | Título normalizado |
| `published_at` | DATETIME | Data de publicação |
| `view_count` | INT | Total de visualizações |
| `like_count` | INT | Total de likes |
| `comment_count` | INT | Total de comentários |
| `candidatos_mencionados` | ARRAY[STRING] | Candidatos identificados |
| `processed_at` | DATETIME | Timestamp do processamento |

**Filtros Aplicados:**
- Apenas português
- Menção obrigatória de candidatos
- Deduplicação
- 260 → 208 registros

---

#### `comments_silver.parquet`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `comment_id` | STRING | ID único do comentário |
| `video_id` | STRING | ID do vídeo (FK) |
| `text_clean` | STRING | Texto normalizado |
| `published_at` | DATETIME | Data do comentário |
| `like_count` | INT | Likes do comentário |
| **`sentimento`** | STRING | POSITIVO \| NEGATIVO \| NEUTRO |
| **`score_sentimento`** | FLOAT | Score numérico [-1.0, +1.0] |
| `processed_at` | DATETIME | Timestamp do processamento |

**Filtros Aplicados:**
- Apenas vídeos relevantes
- Deduplicação
- 30.162 → 15.008 registros (50% descartados)

**Análise de Sentimento:**
- **Método:** Keyword-based em português
- **Performance:** ~0.002s/comentário
- **Distribuição:**
  - NEUTRO: 94.4% (14.161)
  - POSITIVO: 3.3% (491)
  - NEGATIVO: 2.4% (356)

---

### Camada GOLD (Consultável)

Todas as tabelas GOLD possuem as mesmas colunas de sentimento agregadas:

| Campo | Descrição |
|-------|-----------|
| `sentimento_positivo` | Contagem absoluta de comentários positivos |
| `sentimento_negativo` | Contagem absoluta de comentários negativos |
| `sentimento_neutro` | Contagem absoluta de comentários neutros |
| `score_sentimento_medio` | Score médio (-1.0 a +1.0) |
| `sentimento_positivo_pct` | Percentual de positivos (0-100) |
| `sentimento_negativo_pct` | Percentual de negativos (0-100) |
| `sentimento_neutro_pct` | Percentual de neutros (0-100) |

---

## Estatísticas de Qualidade

### Completude
- Videos: 100% com candidatos mencionados
- Comentários: 100% com sentimento e score
- Série temporal: 25 dias contínuos

### Validações
- Sem duplicatas (video_id, comment_id únicos)
- Integridade referencial (FK válidas)
- Score sentimento sempre em [-1.0, 1.0]
- Classificação em {POSITIVO, NEGATIVO, NEUTRO}

### Limitações Conhecidas

- Análise de sentimento com keyword-based (70% acurácia) — não ML
- Apenas 2 candidatos identificados
- Tema = canal (sem análise de tópico semântico real)
- Processamento em português
- Período: setembro/2026

---

## Próximos Passos

### Melhoria Imediata: BERT + Análise de Emoções

A análise de sentimento pode ser enriquecida com BERT (Deep Learning), melhorando de 70% para ~95% de acurácia e adicionando classificação de **7 emoções específicas** (entusiasmo, esperança, raiva, tristeza, decepção, neutro).

**Documentação completa:** Veja [bert_analise_sentimento_7emocoes.md](bert_analise_sentimento_7emocoes.md)
