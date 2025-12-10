"""
Script principal para processar a base ANVISA (CMED)
Wrapper que chama o pipeline completo em src/processar_dados.py

PIPELINE COMPLETO (12 ETAPAS):
1. Limpeza e padronização inicial
2. Unificação de vigências consecutivas
3. Classificação terapêutica + Grupo anatômico
4. Princípio ativo (normalização + correções)
5. Produto (segmentação + normalização)
6. Apresentação (dosagens + formatação)
7. Tipo de produto (categorização)
8. Dosagem (extração MG/ML/UI/unidades)
9. Laboratório (remoção siglas)
10. Grupo terapêutico (merge base ATC)
11. Finalização (reordenação + limpeza)
12. Exports de referência

Uso:
    python pipelines/anvisa_base/scripts/processar_base_anvisa.py
"""

import sys
import os
from pathlib import Path

# Configurar paths
PROJECT_ROOT = Path(__file__).parents[3]
SRC_PATH = PROJECT_ROOT / 'pipelines' / 'anvisa_base' / 'src'

# Adicionar ao path
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_PATH))

# Importar e executar o pipeline completo
if __name__ == "__main__":
    print("="*70)
    print("🏥 PIPELINE DE PROCESSAMENTO ANVISA (CMED)")
    print("="*70)
    print("\nExecutando pipeline completo de src/processar_dados.py...\n")
    
    # Importar módulo principal
    from processar_dados import main
    
    # Executar pipeline completo
    dfpre = main()
