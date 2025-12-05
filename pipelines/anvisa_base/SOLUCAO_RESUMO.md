# 🚀 Scraper Dinâmico ANVISA - Resumo Executivo

## O Problema
Atualmente, o sistema depende de **snippets HTML estáticos** que precisam ser atualizados manualmente:
```
tools/snippets/
├── pmc/
│   ├── 2022.html  ⚠️ Manual
│   ├── 2023.html  ⚠️ Manual
│   ├── 2024.html  ⚠️ Manual
│   └── 2025.html  ⚠️ Manual
```

**Problemas:**
- ❌ Manutenção manual trabalhosa
- ❌ Escalabilidade limitada
- ❌ Atrasos na atualização
- ❌ Difícil detectar períodos faltantes

## A Solução

### ✨ Scraper Dinâmico Inteligente

```python
from src.dynamic_scraper import AnvisaDynamicScraper

scraper = AnvisaDynamicScraper(
    base_url="https://www.gov.br/anvisa/...",
    cache_dir="data/cache/scraper"
)

# Descobre AUTOMATICAMENTE todos os arquivos
df = scraper.scrape_available_files(tipo_lista='PMC')
# ✅ 145 arquivos encontrados (2020-2025)

# Detecta NOVOS arquivos desde última execução
novos = scraper.get_new_files_since_last_run('PMC')
# 🆕 3 novos arquivos detectados!

# Identifica GAPS automaticamente
gaps = scraper.find_missing_periods('PMC')
# ⚠️ 2 períodos faltantes: [(2024, 3), (2024, 7)]
```

## Comparação

| Aspecto | Snippets (Antes) | Scraper Dinâmico (Depois) |
|---------|------------------|---------------------------|
| **Atualização** | ❌ Manual | ✅ Automática |
| **Detecção de novos** | ❌ Impossível | ✅ Automática |
| **Identificação de gaps** | ❌ Manual | ✅ Automática |
| **Manutenção** | ⚠️ Alta | ✅ Mínima |
| **Escalabilidade** | ❌ Limitada | ✅ Ilimitada |
| **Cache** | ❌ Não | ✅ Sim (JSON) |
| **Histórico** | ⚠️ Fixo | ✅ Completo |

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                   FONTE HÍBRIDA                         │
│  (Transição gradual: Snippets → Scraper Dinâmico)      │
└─────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
        ▼                                  ▼
┌──────────────┐                  ┌──────────────────┐
│   SNIPPETS   │                  │     SCRAPER      │
│   (Legado)   │                  │    DINÂMICO      │
│              │                  │                  │
│ • 2020-2024  │                  │ • 2025+          │
│ • Estático   │                  │ • Automático     │
│ • Manual     │                  │ • Cache          │
└──────────────┘                  └──────────────────┘
```

## Casos de Uso

### 1️⃣ Atualização Automática Diária
```python
# Cron job executado todo dia às 6h
scraper = AnvisaDynamicScraper(...)
novos = scraper.get_new_files_since_last_run('PMC')

if novos:
    # Disparar pipeline de download
    pipeline.download(novos)
    notificar_equipe(f"{len(novos)} novos arquivos!")
```

### 2️⃣ Monitoramento de Qualidade
```python
# Script semanal de validação
hybrid = HybridAnvisaSource(...)
relatorio = hybrid.validate_and_report_gaps('PMC')

if relatorio['cobertura_percentual'] < 95:
    alertar_equipe(f"Cobertura baixa: {relatorio['gaps']}")
```

### 3️⃣ Migração Gradual
```python
# Fase 1: Híbrido (snippets + scraper)
df = hybrid.get_links('PMC')  # Usa ambos

# Fase 2: Apenas scraper (futuro)
df = scraper.scrape_available_files('PMC')  # Só scraper
```

## Benefícios Imediatos

✅ **Zero Manutenção Manual**
- Nunca mais atualizar snippets HTML manualmente
- Sistema 100% autônomo

✅ **Detecção Automática**
- Novos arquivos detectados automaticamente
- Alertas quando ANVISA publica novos dados

✅ **Qualidade Garantida**
- Gaps identificados automaticamente
- Relatórios de cobertura em tempo real

✅ **Escalabilidade Infinita**
- Suporta qualquer volume de dados
- Funciona para qualquer período (passado ou futuro)

✅ **Cache Inteligente**
- Evita re-downloads desnecessários
- Performance otimizada

## Como Ativar

### Opção 1: Gradual (Recomendado)
```python
# config_anvisa.py
USE_DYNAMIC_SCRAPER = True
SCRAPER_CUTOFF_YEAR = 2025  # Snippets até 2024, scraper para 2025+
```

### Opção 2: Completo (Futuro)
```python
# config_anvisa.py
USE_DYNAMIC_SCRAPER = True
SCRAPER_CUTOFF_YEAR = 2020  # Scraper para tudo
```

## Próximos Passos

### Curto Prazo (1 mês)
- [x] Implementar scraper dinâmico
- [x] Criar fonte híbrida
- [ ] Validar em produção (2025)
- [ ] Monitorar performance

### Médio Prazo (3 meses)
- [ ] Expandir cutoff_year para 2024
- [ ] Validar 100% cobertura 2023-2024
- [ ] Depreciar snippets gradualmente

### Longo Prazo (6 meses)
- [ ] Migração completa para scraper
- [ ] Remover código legado de snippets
- [ ] Adicionar suporte a PF (Preço Fábrica)

## Executar Demonstração

```bash
# Executar exemplos práticos
python -m pipelines.anvisa_base.tools.exemplo_scraper_dinamico

# Validar híbrido vs snippets
python -m pipelines.anvisa_base.src.hybrid_source

# Testar scraper puro
python -m pipelines.anvisa_base.src.dynamic_scraper
```

## Documentação Completa

📚 Ver: [`SCRAPER_DINAMICO.md`](SCRAPER_DINAMICO.md)

## Suporte

- **Autor:** Luciano
- **Data:** Novembro 2025
- **Versão:** 1.0.0

---

**🎉 Com esta solução, o sistema está preparado para o futuro e não depende mais de manutenção manual!**
