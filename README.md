# Pipeline de dados - Ceara 2026

## Airflow

A DAG `youtube_pipeline` orquestra as duas etapas ja implementadas. Ela usa `PythonOperator` e chama diretamente as funcoes `collect_videos` e `collect_comments`; os argumentos de linha de comando dos scripts existem apenas para execucao manual e testes.

```mermaid
flowchart LR
    V["collect_videos"] --> C["collect_comments"]
    V --> B[("Bronze: videos.json")]
    C --> BC[("Bronze: comments.json")]
    S["Silver - futuro"] -.-> G["Gold - futuro"]
```

Para iniciar o Airflow, crie `tcc-engdados/.env` com `YOUTUBE_API_KEY=...` e execute:

```bash
docker compose up --build -d
```

Abra `http://localhost:8080` e entre com usuario `airflow` e senha `airflow`. Ative a DAG `youtube_pipeline` e dispare-a manualmente ou aguarde a agenda diaria.

O Compose define uma chave fixa compartilhada entre os componentes do Airflow para que o webserver consiga exibir os logs das tarefas. Apos alterar `docker-compose.yaml`, recrie os containers com `docker compose up -d --force-recreate`.

O servico `airflow-init` cria `data/` e ajusta automaticamente sua permissao para o usuario do Airflow. Nao e necessario executar `mkdir` ou `chmod` manualmente.

Cada execucao escreve artefatos separados em `data/bronze/<YYYY-MM-DDThh:mmTZD>/videos.json` e `comments.json`, por exemplo `data/bronze/2026-09-12T12:56Z/`. O timestamp e UTC e permite multiplas execucoes no mesmo dia.

O fluxo termina na Bronze por enquanto. Silver, Gold, PostgreSQL analitico, MinIO e Superset continuam planejados e nao fazem parte desta composicao.

## Dashboard

Dashboard Streamlit para análise de sentimentos e engajamento em comentários do YouTube. Visualiza dados das camadas Silver e Gold após processamento completo do pipeline.

Para iniciar:

```bash
.venv\Scripts\python -m streamlit run dashboard/streamlit_app.py
```

Acessa `http://localhost:8506`. Exibe:

- **Home**: KPIs gerais (2 candidatos, 42.334 comentários, 1.391 vídeos, 2 canais de mídia)
- **Sentimentos**: Distribuição, timeline e análise de 6 emoções (BERT multilíngue)
- **Candidatos**: Comparação entre Ciro Gomes e Elmano de Freitas com score de sentimento
- **Canais**: Cobertura de Diário do Nordeste e O POVO com engajamento

Todos os comentários exibidos são anonimizados automaticamente (remove URLs, emails, @menções, telefones, CPFs).

Detalhes completos em [docs/guia_dashboard.md](docs/guia_dashboard.md).