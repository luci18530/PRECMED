# Dashboard ANVISA - Preços de Medicamentos

Dashboard interativo para visualização e análise temporal de preços de medicamentos regulados pela ANVISA.

## 🚀 Início Rápido

### 1. Instalar dependências

```bash
pip install streamlit pandas plotly fastapi uvicorn pyarrow
```

### 2. Pré-processar dados (otimização)

Antes de iniciar o dashboard, execute o pré-processamento para converter os dados CSV para Parquet e criar agregações:

```bash
cd dashboard
python preprocess.py
```

Isso vai:
- ✅ Converter CSVs para Parquet (compressão ~60-70%)
- ✅ Criar agregações temporais pré-computadas
- ✅ Gerar índices para busca rápida
- ✅ Calcular metadados do dataset

### 3. Iniciar o Dashboard (Streamlit)

```bash
streamlit run app.py
```

Acesse: http://localhost:8501

### 4. Iniciar a API (opcional)

```bash
uvicorn api:app --reload --port 8000
```

Acesse: http://localhost:8000/docs

## 📊 Funcionalidades

### Visão Geral
- KPIs: total de produtos, preço médio, variação
- Gráfico de evolução temporal do preço médio
- Distribuição de produtos por mês
- Faixa de preços (mín/méd/máx)

### Explorador de Produtos
- Busca por texto (produto, substância, laboratório)
- Filtros por laboratório e classe terapêutica
- Paginação para navegação eficiente
- Exportação de resultados

### Análise Temporal
- Seleção de produto específico
- Gráfico de evolução de preço
- Estatísticas: preço atual, variação total, min/max
- Tabela de dados históricos

### Comparativos
- Comparação entre dois períodos
- Variação percentual de preços
- Suporte a PF e PMVG

## 🏗️ Arquitetura

```
dashboard/
├── config.py          # Configurações e constantes
├── data_layer.py      # Camada de dados com cache
├── preprocess.py      # Script de pré-processamento
├── api.py             # API FastAPI
├── app.py             # Dashboard Streamlit
└── README.md          # Esta documentação
```

### Estratégias de Otimização

1. **Parquet**: Formato colunar comprimido, ~70% menor que CSV
2. **Cache LRU**: Dados frequentes em memória
3. **Agregações pré-computadas**: Estatísticas prontas para exibição
4. **Índices de busca**: Lookup tables para filtros
5. **Lazy loading**: Carrega apenas períodos necessários
6. **Paginação**: Limita dados transferidos

## 📁 Estrutura de Cache

```
data/cache/dashboard/
├── parquet/           # CSVs convertidos
├── aggregations/      # Agregações pré-computadas
├── indices/           # Índices de busca
└── metadata.json      # Metadados do dataset
```

## 🔌 API Endpoints

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/metadata` | Metadados do dataset |
| `GET /api/periodos` | Períodos disponíveis |
| `GET /api/filtros` | Valores para filtros |
| `GET /api/produtos` | Lista produtos (paginado) |
| `GET /api/produtos/{codigo}` | Detalhe do produto |
| `GET /api/produtos/{codigo}/evolucao` | Histórico de preços |
| `GET /api/agregacoes/classe-terapeutica` | Agregação por classe |
| `GET /api/agregacoes/laboratorio` | Agregação por laboratório |
| `GET /api/comparativo` | Comparar períodos |

## 📝 Notas

- Dados originais: ANVISA (Portal de Dados Abertos)
- Atualização: mensal
- Período coberto: abril/2020 - outubro/2025
