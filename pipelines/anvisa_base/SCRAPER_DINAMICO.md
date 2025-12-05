# Scraper Dinâmico ANVISA - Arquitetura Sustentável

## 📋 Visão Geral

Este módulo implementa uma solução **sustentável e escalável** para coleta automática de dados da ANVISA, substituindo gradualmente os snippets HTML estáticos por um scraper inteligente.

### Problemas Resolvidos

✅ **Manutenção manual de snippets** - Não é mais necessário atualizar manualmente arquivos HTML  
✅ **Escalabilidade** - Detecta automaticamente novos arquivos disponíveis  
✅ **Detecção de gaps** - Identifica períodos faltantes automaticamente  
✅ **Cache inteligente** - Evita re-downloads desnecessários  
✅ **Transição gradual** - Convive com sistema legado durante migração  

---

## 🏗️ Arquitetura

```
pipelines/anvisa_base/
├── src/
│   ├── dynamic_scraper.py      # ⭐ Scraper dinâmico (núcleo)
│   ├── hybrid_source.py         # 🔄 Fonte híbrida (transição)
│   └── anvisa_base.py          # Sistema legado
├── tools/
│   └── snippets/               # 📦 Snippets HTML (legado, até 2024)
│       ├── pmc/
│       │   ├── 2022.html
│       │   ├── 2023.html
│       │   ├── 2024.html
│       │   └── 2025.html
│       └── pmvg/
│           └── ...
├── scripts/
│   └── baixar.py               # Pipeline de download
└── config_anvisa.py            # Configurações centralizadas
```

### Componentes Principais

#### 1. **AnvisaDynamicScraper** (`dynamic_scraper.py`)

Scraper inteligente e autônomo:

- **Detecção automática** de arquivos disponíveis no site ANVISA
- **Cache persistente** de links já conhecidos (`data/cache/scraper/known_links.json`)
- **Identificação de novos períodos** desde última execução
- **Extração robusta de datas** usando múltiplos padrões regex
- **Detecção de tipo** (PMC/PMVG/PF) por contexto semântico
- **Validação de links** (ignora resoluções, foca em conformidade)

#### 2. **HybridAnvisaSource** (`hybrid_source.py`)

Camada de transição que combina snippets e scraper:

- **Estratégia híbrida**: Snippets até 2024, Scraper para 2025+
- **Validação cruzada** entre fontes
- **Detecção de inconsistências**
- **Relatórios de cobertura**

---

## 🚀 Como Usar

### Uso Básico - Scraper Puro

```python
from pathlib import Path
from src.dynamic_scraper import AnvisaDynamicScraper

# Inicializar
scraper = AnvisaDynamicScraper(
    base_url="https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores",
    cache_dir=Path("data/cache/scraper")
)

# 1. Obter TODOS os arquivos disponíveis
df_all = scraper.scrape_available_files()
print(df_all)
# Colunas: ano, mes, mes_nome, tipo, url, data_coleta

# 2. Filtrar por tipo específico
df_pmc = scraper.scrape_available_files(tipo_lista='PMC')
df_pmvg = scraper.scrape_available_files(tipo_lista='PMVG')

# 3. Detectar NOVOS arquivos desde última execução
df_novos = scraper.get_new_files_since_last_run('PMC')
if not df_novos.empty:
    print(f"🆕 {len(df_novos)} novos arquivos detectados!")

# 4. Identificar períodos FALTANTES
missing = scraper.find_missing_periods('PMC', start_year=2023, start_month=1)
if missing:
    print(f"⚠️ Períodos faltantes: {missing}")

# 5. Exportar catálogo completo
scraper.export_links_catalog(Path("data/catalog_anvisa.csv"))
```

### Uso Avançado - Fonte Híbrida

```python
from pathlib import Path
from src.hybrid_source import HybridAnvisaSource

# Inicializar fonte híbrida
hybrid = HybridAnvisaSource(
    base_url="https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores",
    cache_dir=Path("data/cache/scraper"),
    snippets_dir=Path("tools/snippets"),
    cutoff_year=2025  # Usar scraper apenas para 2025+
)

# Obter links (híbrido automático)
df = hybrid.get_links(
    tipo_lista='PMC',
    ano_inicio=2023,
    mes_inicio=1
)
# Usa snippets para 2023-2024, scraper para 2025+

# Forçar uso apenas de scraper (ignorar snippets)
df_scraper_only = hybrid.get_links(
    tipo_lista='PMC',
    ano_inicio=2023,
    mes_inicio=1,
    prefer_dynamic=True  # ⚠️ Ignora snippets
)

# Validar cobertura e gerar relatório
relatorio = hybrid.validate_and_report_gaps('PMC', ano_inicio=2023)
print(f"Cobertura: {relatorio['cobertura_percentual']}%")
print(f"Gaps: {relatorio['gaps']}")
```

---

## 🔧 Integração com Pipeline Existente

### Modificar `config_anvisa.py`

```python
# Adicionar flag para escolher estratégia
USE_DYNAMIC_SCRAPER = True  # False = snippets, True = scraper
SCRAPER_CUTOFF_YEAR = 2025  # Ano a partir do qual usa scraper
```

### Modificar `scripts/baixar.py`

```python
def scrape_anvisa_links(html_content: str | bytes | None = None):
    """Raspa a página da Anvisa usando estratégia configurada."""
    
    if cfg.USE_DYNAMIC_SCRAPER:
        # Nova abordagem: Scraper dinâmico
        from src.hybrid_source import HybridAnvisaSource
        
        hybrid = HybridAnvisaSource(
            base_url=cfg.URL_ANVISA,
            cache_dir=Path(cfg.PASTA_ARQUIVOS_LIMPOS).parent / "cache" / "scraper",
            snippets_dir=cfg.LOCAL_HTML_SNIPPETS.get(cfg.TIPO_LISTA),
            cutoff_year=cfg.SCRAPER_CUTOFF_YEAR
        )
        
        df_links = hybrid.get_links(
            tipo_lista=cfg.TIPO_LISTA,
            ano_inicio=cfg.ANO_INICIO,
            mes_inicio=cfg.MES_INICIO,
            ano_fim=cfg.ANO_FIM,
            mes_fim=cfg.MES_FIM
        )
        
        return df_links
    
    else:
        # Abordagem legada: HTML local ou scraping manual
        # ... código existente ...
```

---

## 📊 Funcionalidades Avançadas

### 1. Detecção Automática de Atualizações

```python
# Executar periodicamente (ex: cron job diário)
from src.dynamic_scraper import AnvisaDynamicScraper
import logging

scraper = AnvisaDynamicScraper(...)

for tipo in ['PMC', 'PMVG']:
    novos = scraper.get_new_files_since_last_run(tipo)
    
    if not novos.empty:
        logging.info(f"🔔 Novos arquivos {tipo} disponíveis!")
        # Disparar pipeline de download
        # pipeline.download(novos)
```

### 2. Monitoramento de Qualidade

```python
from src.hybrid_source import HybridAnvisaSource

hybrid = HybridAnvisaSource(...)

# Verificar cobertura mensal
relatorio = hybrid.validate_and_report_gaps('PMC', ano_inicio=2020)

if relatorio['cobertura_percentual'] < 95:
    logging.warning(f"⚠️ Cobertura baixa: {relatorio['cobertura_percentual']}%")
    logging.warning(f"Gaps: {relatorio['gaps']}")
```

### 3. Comparação Snippet vs Scraper

```python
# Validar consistência (útil durante migração)
df_snippet = hybrid.get_links('PMC', ..., prefer_dynamic=False)
df_scraper = hybrid.get_links('PMC', ..., prefer_dynamic=True)

# Comparar
diff = set(df_snippet['url']) - set(df_scraper['url'])
if diff:
    print(f"⚠️ Divergências encontradas: {len(diff)} URLs")
```

---

## 🧪 Testes e Validação

### Executar Script de Validação

```bash
cd pipelines/anvisa_base/src
python hybrid_source.py
```

**Saída esperada:**
```
================================================================================
VALIDAÇÃO: SNIPPETS vs SCRAPER DINÂMICO
================================================================================

>>> PMC

--- 2024 (Snippets) ---
Encontrados: 12 meses
 ano  mes    fonte
2024    1  snippet
2024    2  snippet
...

--- 2025 (Scraper Dinâmico) ---
Encontrados: 11 meses
 ano  mes    fonte
2025    1  scraper
2025    2  scraper
...

--- Validação 2024 (Scraper) ---
✓ Contagem consistente entre snippet e scraper

--- Cobertura Completa (2023-2025) ---
Cobertura: 97.5%
Fontes: {'snippet': 24, 'scraper': 11}
Gaps detectados: [(2025, 12)]
```

---

## 📈 Roadmap de Migração

### Fase 1: Convivência (ATUAL)
- ✅ Snippets para períodos históricos (2022-2024)
- ✅ Scraper para período atual (2025+)
- ✅ Validação cruzada

### Fase 2: Transição (Q1 2026)
- ⏳ Validar 100% cobertura do scraper para 2023-2024
- ⏳ Depreciar snippets gradualmente
- ⏳ Migrar configuração padrão para `USE_DYNAMIC_SCRAPER=True`

### Fase 3: Consolidação (Q2 2026)
- ⏳ Remover dependência de snippets
- ⏳ Scraper como única fonte de dados
- ⏳ Limpeza de código legado

---

## 🐛 Troubleshooting

### Problema: Scraper não encontra links novos

**Solução:**
```python
# Forçar limpeza de cache
scraper = AnvisaDynamicScraper(...)
scraper._known_links.clear()
scraper._save_cache()

# Re-executar
df = scraper.scrape_available_files(force_refresh=True)
```

### Problema: Divergência entre snippet e scraper

**Diagnóstico:**
```python
# Comparar ano específico
from src.hybrid_source import migrate_to_dynamic_scraper
migrate_to_dynamic_scraper()  # Gera relatório detalhado
```

### Problema: Site ANVISA mudou estrutura

**Adaptação:**
```python
# Ajustar padrões em dynamic_scraper.py:
AnvisaDynamicScraper.TIPO_PATTERNS = {
    'PMC': ['novo_padrao_pmc', ...],
    ...
}
```

---

## 📝 Logs e Monitoramento

O scraper gera logs estruturados:

```
2025-11-28 10:30:15 - INFO - Iniciando raspagem do site ANVISA: https://...
2025-11-28 10:30:16 - DEBUG - Contexto detectado: PMC
2025-11-28 10:30:18 - INFO - Raspagem concluída: 145 arquivos encontrados
2025-11-28 10:30:18 - INFO - Cache carregado: 130 links conhecidos
2025-11-28 10:30:18 - INFO - Encontrados 15 novos arquivos para PMC
```

---

## 🤝 Contribuindo

Para adicionar novos tipos de lista ou padrões:

1. Editar `dynamic_scraper.py`:
```python
TIPO_PATTERNS = {
    'PMC': [...],
    'PMVG': [...],
    'NOVO_TIPO': ['padrao1', 'padrao2'],  # ⬅️ Adicionar aqui
}
```

2. Testar detecção:
```python
scraper = AnvisaDynamicScraper(...)
df = scraper.scrape_available_files(tipo_lista='NOVO_TIPO')
```

---

## 📚 Referências

- **Site ANVISA**: https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos
- **Documentação BeautifulSoup**: https://www.crummy.com/software/BeautifulSoup/
- **Padrões de scraping ético**: https://www.scrapehero.com/how-to-prevent-getting-blacklisted-while-scraping/

---

## 📄 Licença

Este módulo segue a mesma licença do projeto PRECMED.

**Autor:** Luciano  
**Data:** Novembro 2025  
**Versão:** 1.0.0
