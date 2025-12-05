# 🚀 Quick Start - Scraper Dinâmico ANVISA

## Instalação Rápida

```bash
# Já está instalado! Apenas certifique-se de ter as dependências:
pip install requests beautifulsoup4 pandas
```

## Uso em 30 Segundos

### 1. Descobrir todos os arquivos disponíveis

```python
from pathlib import Path
from pipelines.anvisa_base.src.dynamic_scraper import AnvisaDynamicScraper

scraper = AnvisaDynamicScraper(
    base_url="https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores",
    cache_dir=Path("data/cache/scraper")
)

# Obter todos os arquivos PMC
df = scraper.scrape_available_files(tipo_lista='PMC')
print(df.head())
```

**Resultado:**
```
   ano  mes mes_nome tipo                                       url                    data_coleta
0  2023    1  janeiro  PMC  https://www.gov.br/anvisa/.../20230103...  2025-11-28T10:30:15.123456
1  2023    2 fevereiro PMC  https://www.gov.br/anvisa/.../20230207...  2025-11-28T10:30:15.123456
...
```

### 2. Detectar arquivos novos

```python
# Primeira vez: descobre tudo
df_all = scraper.scrape_available_files('PMC')  # 145 arquivos

# Segunda vez: apenas novos
novos = scraper.get_new_files_since_last_run('PMC')  # 0 novos (nada mudou)

# Simular nova publicação da ANVISA...
# Terceira vez:
novos = scraper.get_new_files_since_last_run('PMC')  # 1 novo arquivo!
```

### 3. Identificar períodos faltantes

```python
gaps = scraper.find_missing_periods('PMC', start_year=2023, start_month=1)
print(f"Períodos faltantes: {gaps}")
# [(2024, 3), (2024, 7)]  # Março e julho de 2024 não disponíveis
```

## Executar Exemplos Prontos

```bash
# Rodar demonstração completa
cd pipelines/anvisa_base
python tools/exemplo_scraper_dinamico.py
```

## Integrar com Pipeline Existente

### Editar `config_anvisa.py`:

```python
# Ativar scraper dinâmico
USE_DYNAMIC_SCRAPER = True
SCRAPER_CUTOFF_YEAR = 2025
```

### Pronto! O sistema agora usa scraper automaticamente.

## Comandos Úteis

```bash
# Validar híbrido vs snippets
python -m pipelines.anvisa_base.src.hybrid_source

# Exportar catálogo completo
python -c "from pipelines.anvisa_base.src.dynamic_scraper import AnvisaDynamicScraper; \
scraper = AnvisaDynamicScraper('https://www.gov.br/anvisa/...', 'data/cache/scraper'); \
scraper.export_links_catalog('catalogo.csv')"

# Rodar testes
pytest pipelines/anvisa_base/tests/test_dynamic_scraper.py -v
```

## FAQ Rápido

**P: O scraper substitui completamente os snippets?**
R: Não imediatamente. Use modo híbrido para transição gradual.

**P: Como limpar o cache?**
R: Delete `data/cache/scraper/known_links.json`

**P: Funciona offline?**
R: Não, precisa acessar o site da ANVISA.

**P: E se o site mudar?**
R: Ajuste os padrões em `dynamic_scraper.py` → `TIPO_PATTERNS`

**P: Performance?**
R: ~2-3 segundos para descobrir todos os arquivos (2020-2025)

## Próximo Passo

📖 Leia a documentação completa: [`SCRAPER_DINAMICO.md`](SCRAPER_DINAMICO.md)

---

**Pronto para usar! 🎉**
