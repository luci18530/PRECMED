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

## Modo de Teste (PMC + PMVG 2025)

Nesta fase o pipeline baixa **dois universos** distintos (PMC e PMVG/PF) para 2025, respeitando a organização descrita acima:

1. Cada universo possui um snippet HTML local (`pipelines/anvisa_base/tools/pmc_2025_snippet.html` e `pipelines/anvisa_base/tools/pmvg_2025_snippet.html`).
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
