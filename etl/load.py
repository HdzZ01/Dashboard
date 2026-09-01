"""
Carga — cria o schema e grava os dados normalizados no PostgreSQL.

Ordem de dependência:
    municipio -> bairro -> servico -> medicamento -> paciente -> atendimento

O DDL fica em `db/` (schema.sql, views.sql). O schema é recriado a cada
execução (idempotente). Dimensões e `paciente` entram via `to_sql`;
`atendimento` (grande) via `COPY ... FROM STDIN`.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.settings import get_settings
from etl.transform import ResultadoTransform

logger = logging.getLogger(__name__)

# DDL versionado, fora do pacote etl
_SQL_DIR = Path(__file__).resolve().parent.parent / "db"


def criar_engine() -> Engine:
    return create_engine(get_settings().database_url, future=True)


def _dividir_statements(sql: str) -> list[str]:
    """Remove comentários `--` e separa o arquivo em comandos por `;`."""
    linhas = [ln.split("--", 1)[0] for ln in sql.splitlines()]
    corpo = "\n".join(linhas)
    return [cmd.strip() for cmd in corpo.split(";") if cmd.strip()]


def _executar_arquivo_sql(engine: Engine, nome: str) -> None:
    caminho = _SQL_DIR / nome
    for comando in _dividir_statements(caminho.read_text(encoding="utf-8")):
        with engine.begin() as conn:
            conn.execute(text(comando))
    logger.info("Executado %s", nome)


def _copy_from_dataframe(
    engine: Engine, tabela: str, colunas: list[str], df: pd.DataFrame
) -> None:
    """Carga em massa via `COPY <tabela> FROM STDIN` (CSV), com NULL vazio."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, na_rep="")
    buffer.seek(0)

    lista_cols = ", ".join(colunas)
    sql = f"COPY {tabela} ({lista_cols}) FROM STDIN WITH (FORMAT csv, NULL '')"

    bruto = engine.raw_connection()
    try:
        cursor = bruto.cursor()
        cursor.execute(sql, stream=buffer)   # pg8000: parâmetro `stream`
        bruto.commit()
    finally:
        bruto.close()


def carregar(resultado: ResultadoTransform) -> None:
    engine = criar_engine()

    # 1. schema limpo
    _executar_arquivo_sql(engine, "schema.sql")

    # 2. dimensões independentes
    resultado.municipios.to_sql("municipio", engine, if_exists="append", index=False)
    resultado.servicos.to_sql("servico", engine, if_exists="append", index=False)
    resultado.medicamentos.to_sql("medicamento", engine, if_exists="append", index=False)
    logger.info(
        "Dimensões: %s municípios, %s serviços, %s medicamentos",
        len(resultado.municipios), len(resultado.servicos), len(resultado.medicamentos),
    )

    # 3. mapas nome -> id
    mun_id = _mapa_id(engine, "SELECT id, nome FROM municipio")
    srv_id = _mapa_id(engine, "SELECT id, nome FROM servico")
    med_id = _mapa_id(engine, "SELECT id, descricao FROM medicamento")

    # 4. bairro (depende de municipio)
    bairros = resultado.bairros.assign(
        municipio_id=lambda d: d["municipio_nome"].map(mun_id)
    )[["nome", "municipio_id"]]
    bairros.to_sql("bairro", engine, if_exists="append", index=False)
    logger.info("Bairros: %s", len(bairros))

    with engine.connect() as conn:
        bairro_id = {
            (nome, mid): bid
            for bid, nome, mid in conn.execute(
                text("SELECT id, nome, municipio_id FROM bairro")
            )
        }

    # 5. paciente (depende de bairro)
    pacientes = resultado.pacientes.assign(
        bairro_id=lambda d: pd.array(
            [
                bairro_id.get((b, m))
                for b, m in zip(d["bairro_nome"], d["municipio_nome"].map(mun_id))
            ],
            dtype="Int64",
        ),
    )[["id", "sexo", "data_nascimento", "bairro_id"]]
    pacientes.to_sql("paciente", engine, if_exists="append", index=False)
    logger.info("Pacientes: %s", len(pacientes))

    # 6. atendimento (grande) — carga via COPY FROM STDIN (rápido).
    #    map() com nulos faz o pandas subir int->float; Int64 mantém inteiro anulável.
    colunas = [
        "paciente_id", "tipo", "servico_id", "data_entrada", "data_saida",
        "queixa", "diagnostico", "procedimento", "medicamento_id",
    ]
    atend = resultado.atendimentos.assign(
        servico_id=lambda d: d["servico_nome"].map(srv_id).astype("Int64"),
        medicamento_id=lambda d: d["medicamento_descricao"].map(med_id).astype("Int64"),
    )[colunas]

    _copy_from_dataframe(engine, "atendimento", colunas, atend)
    logger.info("Atendimentos: %s", f"{len(atend):,}")

    # 7. views
    _executar_arquivo_sql(engine, "views.sql")
    engine.dispose()


def _mapa_id(engine: Engine, consulta: str) -> dict[str, int]:
    with engine.connect() as conn:
        return {nome: pk for pk, nome in conn.execute(text(consulta))}
