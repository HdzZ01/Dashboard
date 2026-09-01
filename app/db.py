"""
Camada de acesso a dados.

O dashboard fala com o banco só por aqui — nunca monta SQL de coluna crua
nem lê o CSV. Cada função devolve um DataFrame/estrutura pronta para exibir,
lendo as views definidas em `db/views.sql`.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Engine única (pool com pre-ping para conexões ociosas)."""
    return create_engine(
        get_settings().database_url, pool_pre_ping=True, future=True
    )


def _consultar(sql: str, **params) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


# --------------------------------------------------------------------- KPIs
def indicadores() -> dict[str, object]:
    """Números de resumo para os cartões do topo."""
    linha = _consultar(
        """
        SELECT
            (SELECT count(*) FROM atendimento)                          AS registros,
            (SELECT count(*) FROM paciente)                             AS pacientes,
            (SELECT count(*) FROM municipio)                            AS municipios,
            (SELECT round(avg(idade))::int FROM vw_atendimento
                 WHERE idade IS NOT NULL)                               AS idade_media,
            (SELECT min(data_entrada) FROM atendimento)                 AS inicio,
            (SELECT max(data_entrada) FROM atendimento)                 AS fim
        """
    ).iloc[0]
    return linha.to_dict()


# ------------------------------------------------------------------ séries
def volume_mensal() -> pd.DataFrame:
    """Colunas: ano_mes (date), atendimentos (int)."""
    return _consultar("SELECT ano_mes, atendimentos FROM vw_volume_mensal")


def distribuicao_tipo() -> pd.DataFrame:
    """Participação percentual de cada tipo de atendimento."""
    return _consultar(
        """
        SELECT tipo,
               round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS percentual
        FROM atendimento
        GROUP BY tipo
        ORDER BY percentual DESC
        """
    )


def perfil_etario() -> pd.DataFrame:
    """Contagem por ano de idade — o dashboard agrupa nas faixas de settings."""
    return _consultar(
        """
        SELECT idade, count(*) AS atendimentos
        FROM vw_atendimento
        WHERE idade IS NOT NULL
        GROUP BY idade
        ORDER BY idade
        """
    )


# ----------------------------------------------------------- recursos / serviço
def top_medicamentos(limite: int) -> pd.DataFrame:
    return _consultar(
        """
        SELECT m.descricao AS medicamento, count(*) AS prescricoes
        FROM atendimento a
        JOIN medicamento m ON m.id = a.medicamento_id
        GROUP BY m.descricao
        ORDER BY prescricoes DESC
        LIMIT :limite
        """,
        limite=limite,
    )


def proporcao_servico(limite: int) -> pd.DataFrame:
    return _consultar(
        """
        SELECT s.nome AS servico, count(*) AS atendimentos
        FROM atendimento a
        JOIN servico s ON s.id = a.servico_id
        GROUP BY s.nome
        ORDER BY atendimentos DESC
        LIMIT :limite
        """,
        limite=limite,
    )


# ---------------------------------------------------------------- território
def top_bairros(limite: int) -> pd.DataFrame:
    return _consultar(
        """
        SELECT bairro, count(*) AS atendimentos
        FROM vw_atendimento
        WHERE bairro IS NOT NULL
        GROUP BY bairro
        ORDER BY atendimentos DESC
        LIMIT :limite
        """,
        limite=limite,
    )


def demanda_municipio() -> pd.DataFrame:
    """Atendimentos por município de origem do paciente."""
    return _consultar(
        """
        SELECT municipio, atendimentos
        FROM vw_demanda_municipio
        ORDER BY atendimentos DESC
        """
    )


# ------------------------------------------------------------- texto clínico
def texto_clinico(campo: str) -> pd.Series:
    """Texto livre de `queixa` ou `diagnostico` para a nuvem de palavras."""
    if campo not in {"queixa", "diagnostico"}:
        raise ValueError("campo deve ser 'queixa' ou 'diagnostico'")
    df = _consultar(
        f"SELECT {campo} AS texto FROM atendimento WHERE {campo} IS NOT NULL"
    )
    return df["texto"]
