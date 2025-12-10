"""
Dashboard Streamlit para visualização de dados ANVISA

Fonte: output/anvisa/baseANVISA.csv

Páginas:
1. Visão Geral - KPIs e tendências
2. Explorador de Produtos - Busca e filtros
3. Análise Temporal - Evolução de preços
4. Comparativos - Entre períodos e produtos
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import json
import sys

# Adicionar pasta pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.data_layer import get_data_manager, get_aggregation_engine
from dashboard.config import CACHE_DIR

# Configuração da página
st.set_page_config(
    page_title="Dashboard ANVISA - Preços de Medicamentos",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Instâncias
dm = get_data_manager()
agg = get_aggregation_engine()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

@st.cache_data(ttl=3600)
def carregar_metadados():
    """Carrega metadados do dataset."""
    meta_file = CACHE_DIR / "metadata.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


@st.cache_data(ttl=3600)
def carregar_estatisticas_preco():
    """Carrega estatísticas de preço pré-computadas."""
    agg_path = CACHE_DIR / "aggregations" / "estatisticas_preco_temporal.parquet"
    if agg_path.exists():
        df = pd.read_parquet(agg_path)
        df["data"] = pd.to_datetime(df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2) + "-01")
        return df.sort_values("data")
    return None


@st.cache_data(ttl=3600)
def carregar_indice_produtos():
    """Carrega índice de produtos."""
    index_path = CACHE_DIR / "indices" / "produtos_index.parquet"
    if index_path.exists():
        return pd.read_parquet(index_path)
    return None


def formatar_moeda(valor):
    """Formata valor como moeda brasileira."""
    if pd.isna(valor):
        return "N/A"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("💊 ANVISA Dashboard")
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "Navegação",
    ["📊 Visão Geral", "🔍 Explorador", "📈 Análise Temporal", "⚖️ Comparativos"]
)

# Metadados
meta = carregar_metadados()
if meta:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Dataset")
    st.sidebar.write(f"**Registros:** {meta.get('total_registros', 'N/A'):,}")
    st.sidebar.write(f"**Produtos:** {meta.get('total_produtos_unicos', 'N/A'):,}")
    st.sidebar.write(f"**Períodos:** {meta.get('total_periodos', 'N/A')}")
    st.sidebar.write(f"**De:** {meta.get('periodo_inicio', 'N/A')}")
    st.sidebar.write(f"**Até:** {meta.get('periodo_fim', 'N/A')}")


# ============================================================
# PÁGINA: VISÃO GERAL
# ============================================================

if pagina == "📊 Visão Geral":
    st.title("📊 Visão Geral - Medicamentos ANVISA")
    
    stats = carregar_estatisticas_preco()
    
    if stats is not None and not stats.empty:
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        ultimo = stats.iloc[-1]
        anterior = stats.iloc[-2] if len(stats) > 1 else ultimo
        
        with col1:
            st.metric(
                "Total de Produtos",
                f"{int(ultimo['total_produtos']):,}",
                delta=f"{int(ultimo['total_produtos'] - anterior['total_produtos']):+,}" if len(stats) > 1 else None
            )
        
        with col2:
            variacao_preco = ((ultimo['preco_medio'] / anterior['preco_medio']) - 1) * 100 if len(stats) > 1 and anterior['preco_medio'] > 0 else 0
            st.metric(
                "Preço Médio (PF 0%)",
                formatar_moeda(ultimo['preco_medio']),
                delta=f"{variacao_preco:+.1f}%" if len(stats) > 1 else None
            )
        
        with col3:
            st.metric(
                "Preço Mediano",
                formatar_moeda(ultimo['preco_mediano'])
            )
        
        with col4:
            st.metric(
                "Período Atual",
                f"{int(ultimo['mes']):02d}/{int(ultimo['ano'])}"
            )
        
        st.markdown("---")
        
        # Gráfico de evolução
        st.subheader("📈 Evolução do Preço Médio")
        
        fig = px.line(
            stats,
            x="data",
            y="preco_medio",
            title="Preço Médio (PF 0%) ao Longo do Tempo",
            labels={"data": "Data", "preco_medio": "Preço Médio (R$)"}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráficos secundários
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📦 Total de Produtos por Mês")
            fig2 = px.bar(
                stats,
                x="data",
                y="total_produtos",
                labels={"data": "Data", "total_produtos": "Produtos"}
            )
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            st.subheader("📊 Faixa de Preços (escala log)")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=stats["data"], y=stats["preco_max"],
                mode="lines", name="Máximo", line=dict(color="red", dash="dash")
            ))
            fig3.add_trace(go.Scatter(
                x=stats["data"], y=stats["preco_medio"],
                mode="lines", name="Médio", line=dict(color="blue")
            ))
            fig3.add_trace(go.Scatter(
                x=stats["data"], y=stats["preco_min"],
                mode="lines", name="Mínimo", line=dict(color="green", dash="dash")
            ))
            fig3.update_layout(height=300, yaxis_type="log")
            st.plotly_chart(fig3, use_container_width=True)
    
    else:
        st.warning("⚠️ Dados não disponíveis. Execute `python dashboard/preprocess.py` primeiro.")


# ============================================================
# PÁGINA: EXPLORADOR
# ============================================================

elif pagina == "🔍 Explorador":
    st.title("🔍 Explorador de Produtos")
    
    produtos = carregar_indice_produtos()
    
    if produtos is not None:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            busca = st.text_input("🔎 Buscar produto", placeholder="Digite nome, substância ou laboratório...")
        
        with col2:
            if "LABORATORIO" in produtos.columns:
                labs = ["Todos"] + sorted(produtos["LABORATORIO"].dropna().unique().tolist())[:100]
                lab_selecionado = st.selectbox("🏭 Laboratório", labs)
            else:
                lab_selecionado = "Todos"
        
        with col3:
            if "GRUPO TERAPEUTICO" in produtos.columns:
                grupos = ["Todos"] + sorted(produtos["GRUPO TERAPEUTICO"].dropna().unique().tolist())
                grupo_selecionado = st.selectbox("💊 Grupo Terapêutico", grupos)
            else:
                grupo_selecionado = "Todos"
        
        # Aplicar filtros
        df_filtrado = produtos.copy()
        
        if busca and "busca" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["busca"].str.contains(busca.upper(), na=False)]
        
        if lab_selecionado != "Todos" and "LABORATORIO" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["LABORATORIO"] == lab_selecionado]
        
        if grupo_selecionado != "Todos" and "GRUPO TERAPEUTICO" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["GRUPO TERAPEUTICO"] == grupo_selecionado]
        
        # Resultados
        st.markdown(f"**{len(df_filtrado):,} produtos encontrados**")
        
        # Paginação
        itens_por_pagina = 25
        total_paginas = max(1, (len(df_filtrado) + itens_por_pagina - 1) // itens_por_pagina)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pagina_atual = st.number_input("Página", min_value=1, max_value=total_paginas, value=1)
        
        inicio = (pagina_atual - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
        
        # Exibir tabela
        colunas_exibir = ["ID_PRODUTO", "PRODUTO", "PRINCIPIO ATIVO", "LABORATORIO", "GRUPO TERAPEUTICO", "STATUS"]
        colunas_disponiveis = [c for c in colunas_exibir if c in df_filtrado.columns]
        
        st.dataframe(
            df_filtrado[colunas_disponiveis].iloc[inicio:fim],
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Página {pagina_atual} de {total_paginas}")
    
    else:
        st.warning("⚠️ Índice não disponível. Execute `python dashboard/preprocess.py` primeiro.")


# ============================================================
# PÁGINA: ANÁLISE TEMPORAL
# ============================================================

elif pagina == "📈 Análise Temporal":
    st.title("📈 Análise Temporal de Preços")
    
    produtos = carregar_indice_produtos()
    
    if produtos is not None:
        # Seleção de produto
        busca = st.text_input("🔎 Buscar produto para análise", placeholder="Digite nome do produto...")
        
        if busca and "busca" in produtos.columns:
            resultados = produtos[produtos["busca"].str.contains(busca.upper(), na=False)].head(10)
            
            if not resultados.empty:
                opcoes = []
                for _, r in resultados.iterrows():
                    produto_nome = str(r.get('PRODUTO', ''))[:50]
                    lab_nome = str(r.get('LABORATORIO', ''))[:30]
                    id_prod = str(r.get('ID_PRODUTO', ''))
                    opcoes.append(f"{id_prod} - {produto_nome}... ({lab_nome})")
                
                selecionado = st.selectbox("Selecione o produto", opcoes)
                
                if selecionado:
                    id_produto = selecionado.split(" - ")[0]
                    
                    # Buscar evolução
                    with st.spinner("Carregando histórico de preços..."):
                        evolucao = agg.evolucao_preco_produto(id_produto, "PF 0%")
                    
                    if not evolucao.empty:
                        nome_produto = evolucao['produto'].iloc[0] if 'produto' in evolucao.columns else id_produto
                        st.subheader(f"📊 Evolução de Preço: {nome_produto}")
                        
                        # Gráfico
                        fig = px.line(
                            evolucao,
                            x="data",
                            y="preco",
                            title="Preço Fábrica (PF 0%) ao Longo do Tempo",
                            markers=True
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Estatísticas
                        col1, col2, col3, col4 = st.columns(4)
                        
                        preco_atual = evolucao["preco"].iloc[-1]
                        preco_primeiro = evolucao["preco"].iloc[0]
                        
                        with col1:
                            st.metric("Preço Atual", formatar_moeda(preco_atual))
                        
                        with col2:
                            if pd.notna(preco_primeiro) and pd.notna(preco_atual) and preco_primeiro > 0:
                                variacao = ((preco_atual / preco_primeiro) - 1) * 100
                                st.metric("Variação Total", f"{variacao:+.1f}%")
                            else:
                                st.metric("Variação Total", "N/A")
                        
                        with col3:
                            st.metric("Preço Mínimo", formatar_moeda(evolucao["preco"].min()))
                        
                        with col4:
                            st.metric("Preço Máximo", formatar_moeda(evolucao["preco"].max()))
                        
                        # Tabela de dados
                        with st.expander("📋 Ver dados completos"):
                            df_exibir = evolucao[["data", "preco"]].copy()
                            df_exibir["preco_formatado"] = df_exibir["preco"].apply(formatar_moeda)
                            st.dataframe(df_exibir[["data", "preco_formatado"]], use_container_width=True)
                    
                    else:
                        st.warning("Histórico não encontrado para este produto.")
            else:
                st.info("Nenhum produto encontrado com esse termo.")
    else:
        st.warning("⚠️ Índice não disponível. Execute `python dashboard/preprocess.py` primeiro.")


# ============================================================
# PÁGINA: COMPARATIVOS
# ============================================================

elif pagina == "⚖️ Comparativos":
    st.title("⚖️ Comparativo de Preços")
    
    periodos = dm.get_periodos_disponiveis()
    
    if periodos:
        st.subheader("Compare preços entre dois períodos")
        
        col1, col2 = st.columns(2)
        
        opcoes_periodo = [f"{p['ano']}-{p['mes']:02d}" for p in periodos]
        
        with col1:
            p1 = st.selectbox("Período 1 (anterior)", opcoes_periodo, index=0)
        
        with col2:
            p2 = st.selectbox("Período 2 (atual)", opcoes_periodo, index=len(opcoes_periodo)-1)
        
        # Busca de produto
        produtos = carregar_indice_produtos()
        
        if produtos is not None:
            busca = st.text_input("🔎 Buscar produto para comparar")
            
            if busca and "busca" in produtos.columns:
                resultados = produtos[produtos["busca"].str.contains(busca.upper(), na=False)].head(10)
                
                if not resultados.empty:
                    opcoes = []
                    for _, r in resultados.iterrows():
                        produto_nome = str(r.get('PRODUTO', ''))[:50]
                        id_prod = str(r.get('ID_PRODUTO', ''))
                        opcoes.append(f"{id_prod} - {produto_nome}...")
                    
                    selecionado = st.selectbox("Selecione o produto", opcoes)
                    
                    if selecionado and st.button("🔄 Comparar"):
                        id_produto = selecionado.split(" - ")[0]
                        ano1, mes1 = map(int, p1.split("-"))
                        ano2, mes2 = map(int, p2.split("-"))
                        
                        resultado = agg.comparativo_periodos(
                            id_produto,
                            (ano1, mes1),
                            (ano2, mes2)
                        )
                        
                        if resultado.get("encontrado_p1") and resultado.get("encontrado_p2"):
                            st.success("✅ Comparativo gerado!")
                            
                            for col_preco in ["PF 0%", "PMVG 0%", "PMC 0%"]:
                                if f"{col_preco}_variacao" in resultado:
                                    st.markdown(f"### {col_preco}")
                                    c1, c2, c3 = st.columns(3)
                                    with c1:
                                        st.metric(f"Período 1 ({p1})", formatar_moeda(resultado.get(f"{col_preco}_p1")))
                                    with c2:
                                        st.metric(f"Período 2 ({p2})", formatar_moeda(resultado.get(f"{col_preco}_p2")))
                                    with c3:
                                        var = resultado.get(f"{col_preco}_variacao", 0)
                                        st.metric("Variação", f"{var:+.2f}%")
                        else:
                            msg = ""
                            if not resultado.get("encontrado_p1"):
                                msg += f"Produto não encontrado no período {p1}. "
                            if not resultado.get("encontrado_p2"):
                                msg += f"Produto não encontrado no período {p2}."
                            st.warning(msg)
    else:
        st.warning("⚠️ Nenhum período disponível.")


# ============================================================
# FOOTER
# ============================================================

st.sidebar.markdown("---")
st.sidebar.caption("Dashboard ANVISA v1.0")
st.sidebar.caption(f"Fonte: baseANVISA.csv")
st.sidebar.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y')}")
