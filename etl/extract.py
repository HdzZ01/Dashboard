"""
Extração — leitura da fonte bruta.

A fonte é um CSV plano (uma linha por evento). Lemos tudo como texto para
manter o controle da conversão de tipos no `transform`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Colunas esperadas na fonte (ordem não importa, presença sim).
COLUNAS_FONTE: tuple[str, ...] = (
    "_id", "sexo", "cidade", "bairro", "dataNascimento", "tipo", "servico",
    "dataEntrada", "dataSaida", "queixa", "diagnostico", "procedimento",
    "descricaoMedicamento",
)


def carregar_csv(caminho: Path) -> pd.DataFrame:
    """Lê o CSV de origem como `str` e valida o conjunto de colunas."""
    if not caminho.exists():
        raise FileNotFoundError(f"Fonte não encontrada: {caminho}")

    df = pd.read_csv(caminho, dtype=str, keep_default_na=True, na_values=[""])

    faltando = set(COLUNAS_FONTE) - set(df.columns)
    if faltando:
        raise ValueError(f"Colunas ausentes na fonte: {sorted(faltando)}")

    logger.info("Fonte lida: %s linhas, %s colunas", f"{len(df):,}", len(df.columns))
    return df
