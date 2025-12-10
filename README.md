# PRECMED – Histórico Regulatório de Preços de Medicamentos
Projeto dedicado à construção de uma base histórica completa dos preços regulados de medicamentos no Brasil, abrangendo:

- PF – Preço Fábrica  
- PMVG – Preço Máximo ao Governo  
- PMC – Preço Máximo ao Consumidor  

O objetivo é consolidar, versionar e disponibilizar a evolução temporal desses valores, a partir de dados da CMED/ANVISA e documentos regulatórios relacionados.

Atualmente, os painéis e portais oficiais oferecem apenas recortes limitados (por ano ou por tabela vigente), dificultando análises históricas, auditorias, estudos de mercado e transparência. O PRECMED busca centralizar essas informações em uma estrutura aberta, padronizada e consultável.

---

## Objetivos do Projeto

- Criar uma base temporal de PF, PMC e PMVG, com todas as vigências e alterações ao longo dos anos.
- Desenvolver um pipeline de coleta, extração e padronização de tabelas e portarias da CMED.
- Permitir análises comparativas entre PF, PMVG e PMC.
- Disponibilizar uma API para consulta programática das séries temporais.
- Criar visualizações interativas para análise de tendências, variações e impactos regulatórios.
- Facilitar estudos para governos, pesquisadores, profissionais de saúde e auditorias públicas.

---

## Por que este projeto é importante

Os três tipos de preços representam diferentes níveis da cadeia farmacêutica:

- **PF**: base regulatória inicial, usada para indústria e distribuição.  
- **PMVG**: valor máximo permitido para compras públicas governamentais.  
- **PMC**: teto para o consumidor final na farmácia.  

Analisar o comportamento conjunto desses preços ao longo dos anos permite identificar:

- políticas de reajuste  
- margens entre PF e PMC  
- diferenças de comportamento entre laboratórios  
- distorções em medicamentos de alto impacto  
- efeitos de ICMS e regulamentações estaduais  

---

## Arquitetura do Projeto

### 1. Coleta dos Dados
O pipeline fará extração de:

- Tabelas CMED/ANVISA contendo PF, PMVG e PMC  
- Painéis Power BI oficiais, quando houver endpoint acessível  
- Portarias da CMED (DOU) com reajustes anuais  
- Históricos de tabelas disponibilizados em PDF ou XLS  

### 2. Padronização
Inclui:

- Normalização de nomes de produto  
- Padronização de apresentações  
- Tratamento de estados e ICMS (PMC e PMVG)  
- Deduplicação  
- Conversão de formatos históricos (PDF → tabela)  
- Integração com lista de registros ANVISA  

A base final conterá campos como:
registro_anvisa | produto | apresentacao | data_vigencia | pf | pmvg | pmc | laboratorio | classe | icms | estado | status

### 3. Banco de Dados
A base temporal será armazenada em:

- DuckDB (preferencial) ou SQLite  
- Particionamento por data de vigência  
- Controle de versões das tabelas CMED  

### 4. API (em desenvolvimento)
Endpoints previstos:
/medicamentos/{registro}/historico
/medicamentos?principio_ativo
/comparacao/{registro}/pf-pmvg-pmc
/estados/{uf}


### 5. Dashboard (em desenvolvimento)
Painel contendo:

- Séries temporais de PF, PMC e PMVG  
- Gráficos comparativos por laboratório  
- Impacto do ICMS por estado  
- Margem PMC – PF ao longo do tempo  
- Tendências regulatórias  
- Evolução ajustada por inflação  

---

## Visualizações Planejadas

- Gráficos de linha por tipo de preço  
- Diferença percentual PMC/PF  
- Variação acumulada e anual  
- Rankings por reajuste  
- Mapas por UF (PMC/ICMS)  
- Correlação PF x PMC x PMVG  

---

## Caminho de Desenvolvimento

### Fase 1 – Estrutura Inicial
- Criação do repositório  
- Organização da documentação  
- Definição do esquema de dados  

### Fase 2 – ETL
- Coleta de PF, PMC e PMVG  
- Parser de PDFs e portarias do DOU  
- Normalização e padronização  
- Banco de dados temporal finalizado  

### Fase 3 – API
- Endpoints essenciais  
- Paginação e filtros  
- Documentação via OpenAPI  

### Fase 4 – Dashboard
- Séries temporais  
- Comparações  
- Filtros avançados  

### Fase 5 – Análises Avançadas
- Ajustes inflacionários  
- Clusterização por comportamento de preço  
- Identificação de saltos regulatórios  
- Exportações para CSV, JSON e Excel  

---

## Tecnologias

- Python  
- Pandas / Polars  
- DuckDB ou SQLite  
- FastAPI  
- Streamlit ou Next.js  
- Requests / BeautifulSoup / PyPDF  
- Docker (opcional)  

---

## Guia de Execução

### Pré-requisitos
- Python 3.12+
- Dependências em `requirements.txt`: `pip install -r requirements.txt`

### 1. Download e Processamento da Base ANVISA

#### 1.1 Baixar dados PMC + PMVG (com scraping ao vivo)
```bash
cd C:\Users\luciano\Desktop\Works\PORTIFOLIO\PRECMED
C:\Python312\python.exe download.py
```

**O que acontece:**
- Raspeia a página oficial da ANVISA (ou usa snippets locais como fallback)
- Baixa arquivos XLS/XLSX de PMC (Preço Máximo ao Consumidor) e PMVG (Preço Máximo ao Governo)
- Período padrão: 2020-04 até a data atual (configurável em `pipelines/anvisa_base/config_anvisa.py`)
- Salva dados consolidados em `data/processed/anvisa/`

**Arquivos gerados:**
- `base_anvisa_precos_vigencias.csv` – base consolidada com vigências
- `base_pmc_pmvg_unificada.csv` – fusão PMC + PMVG por período
- `output/anvisa/baseANVISA.csv` – cópia compatível com dashboard

#### 1.2 Configurar período de coleta (opcional)
Edite `pipelines/anvisa_base/config_anvisa.py`:
```python
# Coleta desde 2020-04
ANO_INICIO = 2020
MES_INICIO = 4

# Apenas mês anterior (útil para atualizações incrementais)
USAR_MES_ANTERIOR = False  # Mude para True se quiser atualizar só o último mês
```

#### 1.3 Processar e refinar dados
```bash
C:\Python312\python.exe pipelines/anvisa_base/main.py
```

**O que faz:**
- Aplica limpeza e padronização sobre a base consolidada
- Detecta mudanças de preço e calcula vigências
- Remove duplicatas e normaliza atributos
- Salva resultado final em `data/processed/anvisa/base_anvisa_precos_vigencias.csv`

#### 1.4 Pipeline de preparação avançada (processamento da base unificada)
```bash
cd C:\Users\luciano\Desktop\Works\PORTIFOLIO\PRECMED
C:\Python312\python.exe pipelines/anvisa_base/scripts/processar_base_anvisa.py
```

**Para que serve:**
- Carrega a base já baixada/mesclada (`data/processed/anvisa/base_pmc_pmvg_unificada.csv` — único input)
- Aplica limpeza extra e normalização de apresentações (funções em `pipelines/anvisa_base/src/anvisa_base.py`)
- Calcula vigências e reduz colunas originais redundantes
- Retorna o DataFrame final (`dfpre`) pronto para análises ou integração

**Entrada esperada:**
- `data/processed/anvisa/base_pmc_pmvg_unificada.csv` (gerada pelo passo 1.1/1.3)

**Saídas típicas:**
- Gera `output/anvisa/baseANVISA.csv` como base processada final
- Reutiliza `output/anvisa/baseANVISA_dtypes.json` para tipagem

---

### 2. Montar o Dashboard Streamlit

#### 2.1 Preparar e validar dados
```bash
C:\Python312\python.exe dashboard/preprocess.py
```

**Gera:**
- Parquet otimizado em `data/cache/dashboard/`
- Agregações pré-calculadas
- Índices para busca rápida
- Metadata de períodos e produtos

#### 2.2 Executar dashboard
```bash
C:\Python312\python.exe -m streamlit run dashboard/app.py
```

**Acesso:**
- Abre automaticamente em `http://localhost:8501`
- Ou manualmente: abra navegador e acesse `http://localhost:8501`

**Funcionalidades:**
- Série temporal de preços (PF, PMC, PMVG)
- Busca por produto/princípio ativo
- Análise de vigências
- Comparação de períodos
- Exportação de dados

---

### 3. Pipeline Completo (um comando)

Para executar todo o fluxo de uma vez:
```bash
# 1. Download + processamento
C:\Python312\python.exe download.py

# 2. Prepara dados para dashboard
C:\Python312\python.exe dashboard/preprocess.py

# 3. Inicia dashboard
C:\Python312\python.exe -m streamlit run dashboard/app.py
```

---

## CLI - Menu inicial (rápido)

Para facilitar a execução das etapas, incluímos um `cli.py` na raiz do projeto.
Ele permite executar as etapas do pipeline via menu interativo ou flags:

Exemplos de uso:

```powershell
# Menu interativo
python cli.py

# Só download (PMC + PMVG)
python cli.py --download

# Só processamento (pipeline completo)
python cli.py --process

# Dashboard: preprocess + start Streamlit
python cli.py --dashboard start

# Executa tudo: download -> process -> dashboard preprocess
python cli.py --all
```

O CLI é uma camada de conveniência que invoca os scripts já existentes (download, processar_base_anvisa, dashboard/preprocess) garantindo um fluxo unificado.


## Modo de Teste (PMC + PMVG 2025)

Nesta fase o pipeline baixa **dois universos** distintos (PMC e PMVG/PF) para 2025, respeitando a organização descrita acima:

1. Cada universo possui um snippet HTML local (`pipelines/anvisa_base/tools/snippets/pmc/` e `pipelines/anvisa_base/tools/snippets/pmvg/`).
2. O comando `python download.py` executa os dois ciclos em sequência: baixa PMC, gera um snapshot em `data/processed/pmc/`, depois repete para PMVG e salva em `data/processed/pmvg/`.
3. Ao final o script combina as listas via chave `ANO_REF + MES_REF + REGISTRO + CÓDIGO GGREM`, criando `data/processed/anvisa/base_pmc_pmvg_unificada.csv` com todas as colunas de PF/PMVG/PMC.
4. Os arquivos consolidados individuais continuam disponíveis para inspeção (`data/processed/anvisa/anvisa_pmvg_consolidado_temp.csv` referencia a última execução).

Assim garantimos testes rápidos sem depender da página completa da Anvisa e ainda mantemos os dois recortes sincronizados para análises comparativas.

---

## Estrutura do Repositório (planejada)

- precfmed/
- ├── data/
- │ ├── raw/
- │ ├── processed/
- ├── notebooks/
- │ ├── 01_coleta.ipynb
- │ ├── 02_limpeza.ipynb
- │ ├── 03_analises.ipynb
- ├── src/
- │ ├── scraper.py
- │ ├── cleaner.py
- │ ├── parser.py
- │ ├── database.py
- │ ├── utils.py
- ├── api/
- │ └── main.py
- ├── dashboard/
- │ └── (em desenvolvimento)
- ├── README.md
- └── requirements.txt

> **Status da estrutura**: os diretórios `data/raw`, `data/processed`, `src/`, `api/` e `dashboard/` já estão criados conforme o organograma acima. Os notebooks (`01_coleta.ipynb`, `02_limpeza.ipynb`, `03_analises.ipynb`) ainda são placeholders e serão adicionados quando a fase analítica iniciar.

## Contribuições

Contribuições são bem-vindas para aprimorar o escopo, fontes de dados ou componentes regulatórios adicionais.  
Sugestões, issues e pull requests são incentivados.

---

## Autor

Luciano Pereira  
Ciência da Computação – UFPB  
Análise e Engenharia de Dados • Pipelines Públicos • Farmacoeconomia  
GitHub: https://github.com/luci18530
