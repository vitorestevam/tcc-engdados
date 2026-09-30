# Guia de Visualização do Dashboard

## Acesso Rápido

### 1. Iniciar com Docker Compose
```bash
docker compose up --build
```

O dashboard estará disponível em: **http://localhost:8501**.

### 2. Iniciar localmente
```bash
.venv/bin/python -m streamlit run dashboard/streamlit_app.py --server.port 8506
```

O dashboard abrirá automaticamente em: **http://localhost:8506**

(Porta padrão 8506; se ocupada, Streamlit escolhe automaticamente a próxima disponível)

---

## Estrutura do Dashboard

O dashboard possui **4 páginas principais**, acessíveis pelo menu lateral esquerdo:

### Home (Página Inicial)
**Propósito**: Visão geral dos dados e KPIs principais

**O que você vê:**
- **5 Métricas no topo**:
  - **Candidatos**: 2 (Ciro Gomes e Elmano de Freitas)
  - **Comentários**: 42.334 total coletados
  - **Vídeos**: 1.391 vídeos relevantes analisados
  - **Canais de Mídia**: 2 (Diário do Nordeste e O POVO)
  - **Likes Total**: 124.007 reações positivas

- **Distribuição Geral de Sentimentos**:
  - 3 cards mostrando percentual de: Positivos, Negativos, Neutros
  - Rápido diagnóstico do clima geral nos comentários

- **Top 5 Candidatos por Engajamento**:
  - Ranking dos 2 candidatos com mais comentários
  - Mostra: Candidato | Comentários | Score Sentimento Médio

- **Canais de Mídia por Engajamento**:
  - Tabela com os 2 canais de mídia
  - Mostra: Canal | Comentários | Likes Totais

---

### Sentimentos (Página 1_sentimentos.py)
**Propósito**: Análise detalhada de sentimentos e emoções dos comentários

**Seções:**

1. **Gráficos de Distribuição de Sentimentos**
   - Coluna esquerda: Gráfico de barras com contagem absoluta
   - Coluna direita: Gráfico de barras com percentuais
   - Ambos destacam as 3 categorias: Positivo (verde), Negativo (vermelho), Neutro (cinza)

2. **Timeline de Sentimentos**
   - Gráfico de linhas mostrando evolução temporal
   - 3 linhas: uma para cada sentimento
   - Eixo X: Data | Eixo Y: Número de comentários

3. **Sentimentos por Hora do Dia**
   - Gráfico de linhas similar à timeline
   - Eixo X: Hora (0-23) | Eixo Y: Número de comentários
   - Identifica horários de pico de engajamento

4. **Vídeos com Maior Repercussão na Semana**
   - **Barras horizontais** com os 5 vídeos mais comentados
   - Eixo Y: Título do vídeo (completo)
   - Eixo X: Número de comentários
   - Ordenação: Decrescente (maior repercussão no topo)

5. **Distribuição de Emoções (BERT)**
   - Gráfico de pizza mostrando as 6 emoções detectadas:
     - Entusiasmo
     - Esperança
     - Raiva
     - Tristeza
     - Decepção
     - Neutro
   - Análise realizada com modelo BERT multilíngue

6. **Filtro de Emoções com Amostra de Comentários**
   - Dropdown para selecionar uma emoção específica
   - Exibe comentários anônimos que expressam essa emoção
   - **Anonimização**: Remove automaticamente URLs, emails, @menções, telefones, CPFs para privacidade

---

### Candidatos (Página 2_candidatos.py)
**Propósito**: Análise comparativa entre os 2 candidatos

**Seções:**

1. **Top 5 Candidatos por Engajamento**
   - Gráfico de barras agrupadas mostrando candidatos
   - Permite comparação visual de comentários

2. **Evolução Temporal de Sentimentos - Candidatos**
   - **Gráfico de linhas** com cores distintas por candidato:
     - Azul: Ciro Gomes
     - Laranja: Elmano de Freitas
   - Eixo X: Data | Eixo Y: Número de comentários
   - Dropdown para filtrar visualização
   - Legenda clara com cores

3. **Tabela Completa de Candidatos**
   - Colunas: Candidato | Vídeos Total | Comentários Total | Score Sentimento
   - Ordenação: Por número de comentários (decrescente)

4. **Detalhes de um Candidato Específico**
   - Dropdown para selecionar candidato
   - 3 métricas: Vídeos Publicados | Comentários Recebidos | Likes Totais
   - Gráfico temporal específico do candidato
   - Subdivisão de sentimentos (Positivos, Negativos, Neutros)

5. **Amostra de Comentários por Candidato**
   - Filtros: Candidato + Sentimento + Quantidade de comentários
   - Comentários exibidos com anonimização automática
   - Útil para análise qualitativa

---

### Canais/Mídia (Página 3_canais.py)
**Propósito**: Análise de cobertura e engajamento dos canais de mídia

**Seções:**

1. **Relação: Vídeos Publicados vs Comentários Recebidos**
   - Gráfico scatter plot (dispersão)
   - Eixo X: Número de vídeos publicados
   - Eixo Y: Número de comentários recebidos
   - Bolhas representam canais (tamanho = volume de comentários)
   - Canais analisados:
     - Diário do Nordeste: 59 vídeos, 9.553 comentários
     - O POVO: 892 vídeos, 17.387 comentários

2. **Distribuição de Sentimentos por Canal**
   - Gráfico stacked (barras empilhadas)
   - Cada canal tem uma barra dividida em 3 cores:
     - Verde: Sentimentos Positivos
     - Vermelho: Sentimentos Negativos
     - Cinza: Sentimentos Neutros
   - Mostra composição de sentimentos por canal

3. **Evolução Temporal de Sentimentos - Canais**
   - Gráfico de linhas com seletor de canal
   - Dropdown para escolher canal específico
   - 2 linhas: Positivos (linha sólida) e Negativos (linha tracejada)
   - Eixo X: Data | Eixo Y: Número de comentários
   - Legenda clara e colorida

4. **Tabela Completa de Canais de Mídia**
   - Colunas: Canal | Vídeos Total | Comentários Total | Likes Total | Positivos | Negativos | Neutros
   - Dados dos 2 canais de mídia

5. **Detalhes de um Canal Específico**
   - Dropdown para selecionar canal
   - Métricas: Vídeos Publicados | Comentários Recebidos | Likes Totais
   - Sentimentos: Positivos | Negativos | Neutros
   - Visualização completa do canal selecionado

---

## Dados Representados

### Origem dos Dados
- **Fonte**: YouTube Data API v3
- **Período**: Setembro 2026 (01/09 a 30/09)
- **Fontes de Dados** (4 canais):
  - **Candidatos** (2): Ciro Gomes | Elmano de Freitas
  - **Mídia** (2): Diário do Nordeste | O POVO
- **Atualização**: Manual (executar scripts de coleta)

### Estatísticas Gerais
- **Vídeos Relevantes**: 1.391 (após filtro por palavras-chave de eleição)
- **Comentários Coletados**: 42.334 (após processamento)
- **Período Coberto**: 01 a 30 de Setembro de 2026
- **Análise de Sentimento**: BERT multilíngue (modelo: nlptown/bert-base-multilingual-uncased-sentiment)

### Pipeline de Processamento
1. **Bronze**: Coleta bruta de vídeos e comentários (JSON)
2. **Silver**: Limpeza, padronização e filtro por relevância (Parquet)
   - Filtro: Keywords de eleição (45+ termos)
   - Processamento: Limpeza de texto, deduplicação
3. **Gold**: Enriquecimento com:
   - Análise de sentimento BERT (score -1 a +1)
   - Detecção de 6 emoções (Entusiasmo, Esperança, Raiva, Tristeza, Decepção, Neutro)
   - Categorização por tipo (candidato vs. mídia)
   - Agregações temporais (diárias, semanais)
   - Campo 'candidato' para relacionar comentários de mídia aos candidatos mencionados

### Arquivos de Dados Utilizados
- `data/gold/<run_id>/comentarios_gold_enriched.parquet` - comentários com sentimento, emoções, canal e candidato
- `data/gold/<run_id>/candidatos_timeline.parquet` - série temporal de comentários dos canais de candidatos
- `data/gold/<run_id>/canais_timeline.parquet` - série temporal de comentários dos canais de imprensa
- `data/silver/<run_id>/videos_silver.parquet` - vídeos relevantes com metadados
- `settings/channels.json` - Configuração dos 4 canais (categoria, identificador)
- `settings/relevance_terms.json` - 45+ termos de filtro por relevância

---

## Como Interpretar os Gráficos

### Score Sentimento
- **-1**: Totalmente negativo
- **0**: Balanceado (neutro)
- **+1**: Totalmente positivo
- Exemplo: -0.05 = levemente negativo | +0.15 = levemente positivo
- Calculado por modelo BERT multilíngue

### Percentuais
- Calculados sobre o total de comentários analisados
- Representam distribuição de sentimentos
- Somam 100% (Positivos + Negativos + Neutros)

### Emoções (BERT)
- Detectadas por modelo de análise de sentimento multilíngue
- Cada comentário pode expressar múltiplas emoções
- Percentual baseado em frequência de detecção
- 6 categorias: Entusiasmo, Esperança, Raiva, Tristeza, Decepção, Neutro

### Anonimização de Comentários
- **Automática** quando comentários são exibidos
- Remove: URLs, emails, @menções, telefones, CPFs
- Mantém: Contexto e significado do comentário
- Propósito: Garantir privacidade dos usuários

---

## Troubleshooting

### Dashboard não abre
```bash
# Reiniciar na porta padrão
.venv\Scripts\python -m streamlit run dashboard/streamlit_app.py
```

### Dados desatualizados
```bash
# Reexecutar pipeline completo (quando novos dados forem coletados)
.venv\Scripts\python src/silver_select_relevant_videos.py
.venv\Scripts\python src/silver_transform_comments.py
.venv\Scripts\python src/gold_add_sentiment.py --input-file "data/silver/comments_silver.parquet"
.venv\Scripts\python src/gold_enrich_datasets.py
```

### Arquivo não encontrado
Certifique-se de que todos os arquivos Gold foram gerados em `data/gold/`:
- comentarios_gold_enriched.parquet
- candidatos_timeline.parquet
- canais_timeline.parquet

---

## Dicas de Uso

1. **Passe o mouse sobre gráficos** para ver valores exatos e detalhes
2. **Use filtros (dropdowns)** para análises específicas de candidatos ou canais
3. **Compare linhas no gráfico temporal** para ver evolução relativa
4. **Clique nos itens de legenda** em gráficos Plotly para mostrar/ocultar séries
5. **Redimensione a janela** para melhor visualização em telas menores
6. **Copie comentários** da amostra para análise qualitativa (já anonimizados)
7. **Combine filtros** de emoção e sentimento para análises avançadas

---

## Arquitetura do Dashboard

### Estrutura de Arquivos
```
dashboard/
├── streamlit_app.py           # Home page com KPIs
├── config.py                   # Configurações, cores, caminhos
├── utils/
│   └── data_loader.py          # Funções de carregamento de dados
└── pages/
    ├── 1_sentimentos.py        # Análise de sentimentos e emoções
    ├── 2_candidatos.py         # Análise de candidatos
    └── 3_canais.py             # Análise de canais de mídia
```

### Fluxo de Dados
1. Scripts de coleta → Dados brutos (Bronze)
2. Scripts de transformação → Dados limpos (Silver)
3. Scripts de enriquecimento → Dados análise-ready (Gold)
4. Dashboard → Visualização e filtros

