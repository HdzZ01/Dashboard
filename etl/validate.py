"""
Validação pós-carga.

Roda um conjunto de checagens contra o banco recém-populado. Se qualquer
checagem obrigatória falhar, o ETL não pode ser declarado concluído.

Regras: .context/plan/data/data_model.md (seção 6.9).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.settings import get_settings
from etl.transform import RelatorioTransform

logger = logging.getLogger(__name__)

_TABELAS = ("municipio", "bairro", "servico", "medicamento", "paciente", "atendimento")
_VIEWS = ("vw_atendimento", "vw_volume_mensal", "vw_demanda_municipio")


@dataclass(slots=True)
class Checagem:
    nome: str
    ok: bool
    detalhe: str = ""


@dataclass(slots=True)
class RelatorioValidacao:
    checagens: list[Checagem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checagens)

    def add(self, nome: str, ok: bool, detalhe: str = "") -> None:
        self.checagens.append(Checagem(nome, ok, detalhe))


def _escalar(engine: Engine, sql: str):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def validar(engine: Engine, transform: RelatorioTransform) -> RelatorioValidacao:
    cfg = get_settings()
    rel = RelatorioValidacao()

    # estrutura
    tabelas = {
        r[0]
        for r in _consulta(
            engine,
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'",
        )
    }
    rel.add("6 tabelas criadas", set(_TABELAS) <= tabelas,
            f"faltando: {sorted(set(_TABELAS) - tabelas)}")
    rel.add("3 views criadas", set(_VIEWS) <= tabelas,
            f"faltando: {sorted(set(_VIEWS) - tabelas)}")
    rel.add(
        "ENUM tipo_atendimento existe",
        bool(_escalar(engine, "SELECT 1 FROM pg_type WHERE typname = 'tipo_atendimento'")),
    )

    # contagens
    n_atend = _escalar(engine, "SELECT count(*) FROM atendimento")
    rel.add("count(atendimento) == linhas aceitas", n_atend == transform.linhas_aceitas,
            f"banco={n_atend:,} vs transform={transform.linhas_aceitas:,}")

    n_pac = _escalar(engine, "SELECT count(*) FROM paciente")
    rel.add("count(paciente) == pacientes do transform", n_pac == transform.pacientes,
            f"banco={n_pac:,} vs transform={transform.pacientes:,}")

    # integridade referencial
    orfaos = _escalar(engine, """
        SELECT
          (SELECT count(*) FROM paciente p
             LEFT JOIN bairro b ON b.id = p.bairro_id
             WHERE p.bairro_id IS NOT NULL AND b.id IS NULL)
        + (SELECT count(*) FROM atendimento a
             LEFT JOIN paciente p ON p.id = a.paciente_id
             WHERE p.id IS NULL)
        + (SELECT count(*) FROM atendimento a
             LEFT JOIN servico s ON s.id = a.servico_id
             WHERE a.servico_id IS NOT NULL AND s.id IS NULL)
        + (SELECT count(*) FROM atendimento a
             LEFT JOIN medicamento m ON m.id = a.medicamento_id
             WHERE a.medicamento_id IS NOT NULL AND m.id IS NULL)
    """)
    rel.add("0 órfãos de chave estrangeira", orfaos == 0, f"órfãos={orfaos}")

    # bug da v1: data de entrada fora de faixa
    min_entrada = _escalar(engine, "SELECT min(data_entrada) FROM atendimento")
    ok_data = min_entrada is None or min_entrada.year >= cfg.min_ano_atendimento
    rel.add(f"min(data_entrada) >= {cfg.min_ano_atendimento}", ok_data, f"min={min_entrada}")

    # tipos dentro do domínio
    tipos = {r[0] for r in _consulta(engine, "SELECT DISTINCT tipo::text FROM atendimento")}
    rel.add("tipos dentro do domínio", tipos <= set(cfg.tipos_atendimento),
            f"inesperados: {sorted(tipos - set(cfg.tipos_atendimento))}")

    # view retorna linhas
    n_view = _escalar(engine, "SELECT count(*) FROM vw_atendimento")
    rel.add("vw_atendimento retorna linhas", (n_view or 0) > 0, f"linhas={n_view:,}")

    return rel


def _consulta(engine: Engine, sql: str):
    with engine.connect() as conn:
        return list(conn.execute(text(sql)))
