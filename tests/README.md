# 🧪 Tests - BERT Sentiment Analysis

Pasta contendo scripts de teste, validação e análise para o módulo BERT de análise de sentimentos.

---

## � Importante: Desenvolvimento vs Produção

Esta pasta contém **scripts de desenvolvimento** para validar o módulo BERT. 

**Pipeline de PRODUÇÃO:**
1. `apply_sentiment_bert.py` → Aplica BERT aos dados reais ✅ **PRODUÇÃO**
2. Airflow DAG → Orquestra a pipeline
3. Superset → Exibe gráficos e análises finais

**Scripts de DESENVOLVIMENTO** (nesta pasta):
- `test_sentiment_bert.py` → Valida se o módulo funciona
- `analyze_bert_results.py` → Análise exploratória (para dev verificar resultados)
- `verify_results.py` → Verificação rápida

Estes scripts não fazem parte da execução automática. São para o desenvolvedor entender e validar os dados durante desenvolvimento.

---

## �📋 Arquivos

### `test_sentiment_bert.py` ⭐ **Principal**
**Teste unitário do módulo BERT**

Valida a classificação correta em 6 casos de teste com exemplos em português:
- ✓ Detecção de ENTUSIASMO
- ✓ Detecção de ESPERANCA
- ✓ Detecção de RAIVA
- ✓ Detecção de TRISTEZA
- ⚠ Edge case: DECEPCAO
- ⚠ Edge case: NEUTRO (frases factuais)

**Como executar:**
```bash
python tests/test_sentiment_bert.py
```

**Resultado esperado:** 4/6 testes passando (67% acurácia em edge cases)

---

### `analyze_bert_results.py` 🔧 **Desenvolvimento**
**Análise detalhada dos resultados (opcional)**

Script para o dev analisar e validar distribuição de emoções após rodar BERT:
- 📊 Distribuição de sentimentos
- 🎭 Distribuição de emoções
- 🔗 Matriz de correlação sentimento × emoção
- 📈 Score médio por emoção
- 🎯 Validação de qualidade

**Como executar:**
```bash
python tests/analyze_bert_results.py
```

**Pré-requisito:** Ter já processado dados com BERT

**Nota:** Este é um script de **desenvolvimento/análise**. Não faz parte da pipeline de produção. A visualização final será feita no Superset (dashboard).

---

### `verify_results.py` 🔧 **Desenvolvimento**
**Verificação rápida dos dados processados (opcional)**

Script rápido para validar se BERT foi executado corretamente:
- Total de registros
- Colunas presentes
- Primeiros registros como amostra

**Como executar:**
```bash
python tests/verify_results.py
```

---

## 🚀 Fluxo de Teste Recomendado

### 1. Validar implementação BERT
```bash
python tests/test_sentiment_bert.py
```
↓ Valida 6 casos de teste em português

### 2. Processar dados reais com BERT
```bash
python apply_sentiment_bert.py
```
↓ Aplica análise BERT aos 15.008 comentários reais em `data/silver/comments_silver.parquet`

### 3. Analisar resultados
```bash
python tests/final_analysis_bert.py
```
↓ Mostra distribuição de sentimentos/emoções e acurácia

---

## ✅ Checklist de Validação

- [ ] `test_sentiment_bert.py` executa com 4/6 testes passando
- [ ] `apply_sentiment_bert.py` processa 15.008 comentários sem erros
- [ ] (Opcional) `analyze_bert_results.py` mostra distribuição esperada
- [ ] `data/gold/emocoes_distribuicao.parquet` foi criado
- [ ] Emoções estão bem distribuídas

---

## 📊 Métricas Esperadas (15.008 comentários reais)

| Métrica | Valor |
|---------|-------|
| Tempo processamento | ~8-10 minutos |
| Velocidade | ~28ms/comentário |
| POSITIVO | ~50-60% |
| NEGATIVO | ~30-40% |
| NEUTRO | ~5-10% |

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'src'"
Execute os testes do diretório raiz (onde está `src/`):
```bash
cd /path/to/tcc-engdados
python tests/test_sentiment_bert.py
```

### "File not found: data/silver/comments_silver.parquet"
Este arquivo contém os dados reais do YouTube. Se não existir, execute a pipeline completa:
```bash
python src/collect_videos.py
python src/collect_comments.py
python src/transform_comments_silver.py
```

### "FileNotFoundError: Model not found"
O modelo BERT será baixado automaticamente na primeira execução (~669MB). Aguarde.

---

**Última atualização:** 29/09/2026
