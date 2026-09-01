"""
Transformação — limpeza e padronização da fonte.

Entrada: DataFrame cru (tudo `str`) vindo do `extract`.
Saída: um `ResultadoTransform` com DataFrames já normalizados (um por tabela
do modelo), prontos para o `load`, mais um relatório do que foi ajustado.

Regras: .context/plan/data/data_model.md (seção 6).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from app.settings import get_settings
from etl.geo import coordenadas

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RelatorioTransform:
    linhas_lidas: int
    linhas_rejeitadas_nascimento: int
    linhas_aceitas: int
    saidas_anuladas: int
    entradas_fora_de_faixa: int
    pacientes: int
    municipios: int
    bairros: int
    servicos: int
    medicamentos: int


@dataclass(slots=True)
class ResultadoTransform:
    municipios: pd.DataFrame     # nome, uf, latitude, longitude
    bairros: pd.DataFrame        # nome, municipio_nome
    servicos: pd.DataFrame       # nome
    medicamentos: pd.DataFrame   # descricao
    pacientes: pd.DataFrame      # id, sexo, data_nascimento, bairro_nome, municipio_nome
    atendimentos: pd.DataFrame   # paciente_id, tipo, servico_nome, datas, textos, medicamento_descricao
    relatorio: RelatorioTransform


def _padronizar_texto(serie: pd.Series) -> pd.Series:
    """strip + colapsa espaços internos + UPPER; vazio vira NA."""
    limpo = (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.upper()
    )
    return limpo.replace("", pd.NA)


def _apenas_strip(serie: pd.Series) -> pd.Series:
    """Texto livre (queixa/diagnóstico/procedimento): só apara; vazio vira NA."""
    limpo = serie.astype("string").str.strip()
    return limpo.replace("", pd.NA)


def transformar(bruto: pd.DataFrame) -> ResultadoTransform:
    cfg = get_settings()
    ano_atual = pd.Timestamp.now().year
    df = bruto.copy()
    linhas_lidas = len(df)

    # --- 6.1 texto categórico ---------------------------------------------
    for col in ("cidade", "bairro", "servico", "descricaoMedicamento"):
        df[col] = _padronizar_texto(df[col])
    for col in ("queixa", "diagnostico", "procedimento"):
        df[col] = _apenas_strip(df[col])

    # --- 6.2 sexo --------------------------------------------------------
    df["sexo"] = df["sexo"].astype("string").str.strip().str.upper()
    invalidos = df.loc[~df["sexo"].isin(cfg.sexos_validos), "sexo"].dropna().unique()
    if len(invalidos):
        raise ValueError(f"Valores de sexo fora do domínio {cfg.sexos_validos}: {list(invalidos)}")

    # --- tipo ----------------------------------------------------------
    df["tipo"] = df["tipo"].astype("string").str.strip().str.upper()
    tipos_invalidos = df.loc[~df["tipo"].isin(cfg.tipos_atendimento), "tipo"].dropna().unique()
    if len(tipos_invalidos):
        raise ValueError(f"Tipos fora do domínio {cfg.tipos_atendimento}: {list(tipos_invalidos)}")

    # --- 6.3 data de nascimento (rejeita linha se inválida) --------------
    nascimento = pd.to_datetime(df["dataNascimento"], errors="coerce")
    nascimento_ok = nascimento.notna() & nascimento.dt.year.between(1900, ano_atual)
    rejeitadas_nascimento = int((~nascimento_ok).sum())
    df = df.loc[nascimento_ok].copy()
    df["data_nascimento"] = nascimento.loc[nascimento_ok].dt.date

    # --- 6.4 datas de entrada / saída ----------------------------------
    entrada = pd.to_datetime(df["dataEntrada"], errors="coerce")
    fora_faixa = entrada.notna() & ~entrada.dt.year.between(cfg.min_ano_atendimento, ano_atual)
    entradas_fora = int(fora_faixa.sum())
    entrada = entrada.mask(fora_faixa)

    saida = pd.to_datetime(df["dataSaida"], errors="coerce")
    saida_invalida = entrada.notna() & saida.notna() & (saida < entrada)
    saidas_anuladas = int(saida_invalida.sum())
    saida = saida.mask(saida_invalida)

    df["data_entrada"] = entrada
    df["data_saida"] = saida

    linhas_aceitas = len(df)

    # --- 6.6 pacientes (dedupe por _id) --------------------------------
    def _primeiro_valido(s: pd.Series):
        s = s.dropna()
        return s.iloc[0] if len(s) else pd.NA

    pacientes = (
        df.groupby("_id", as_index=False)
        .agg(
            sexo=("sexo", _primeiro_valido),
            data_nascimento=("data_nascimento", _primeiro_valido),
            bairro_nome=("bairro", _primeiro_valido),
            municipio_nome=("cidade", _primeiro_valido),
        )
        .rename(columns={"_id": "id"})
    )

    # --- 6.7 dimensões ------------------------------------------------
    municipios = (
        pacientes[["municipio_nome"]]
        .dropna()
        .drop_duplicates()
        .rename(columns={"municipio_nome": "nome"})
        .assign(uf="SP")
    )
    coords = municipios["nome"].map(coordenadas)
    municipios["latitude"] = coords.map(lambda t: t[0])
    municipios["longitude"] = coords.map(lambda t: t[1])

    bairros = (
        pacientes[["bairro_nome", "municipio_nome"]]
        .dropna(subset=["bairro_nome", "municipio_nome"])
        .drop_duplicates()
        .rename(columns={"bairro_nome": "nome"})
    )

    servicos = (
        df[["servico"]].dropna().drop_duplicates()
        .rename(columns={"servico": "nome"}).sort_values("nome")
    )
    medicamentos = (
        df[["descricaoMedicamento"]].dropna().drop_duplicates()
        .rename(columns={"descricaoMedicamento": "descricao"}).sort_values("descricao")
    )

    # --- atendimentos (um por linha aceita) ---------------------------
    atendimentos = df[[
        "_id", "tipo", "servico", "data_entrada", "data_saida",
        "queixa", "diagnostico", "procedimento", "descricaoMedicamento",
    ]].rename(columns={
        "_id": "paciente_id",
        "servico": "servico_nome",
        "descricaoMedicamento": "medicamento_descricao",
    })

    relatorio = RelatorioTransform(
        linhas_lidas=linhas_lidas,
        linhas_rejeitadas_nascimento=rejeitadas_nascimento,
        linhas_aceitas=linhas_aceitas,
        saidas_anuladas=saidas_anuladas,
        entradas_fora_de_faixa=entradas_fora,
        pacientes=len(pacientes),
        municipios=len(municipios),
        bairros=len(bairros),
        servicos=len(servicos),
        medicamentos=len(medicamentos),
    )
    logger.info(
        "Transform: %s lidas -> %s aceitas (%s rejeitadas por nascimento); "
        "%s entradas fora de faixa -> NULL; %s saídas < entrada -> NULL",
        f"{linhas_lidas:,}", f"{linhas_aceitas:,}",
        rejeitadas_nascimento, entradas_fora, saidas_anuladas,
    )
    return ResultadoTransform(
        municipios=municipios,
        bairros=bairros,
        servicos=servicos,
        medicamentos=medicamentos,
        pacientes=pacientes,
        atendimentos=atendimentos,
        relatorio=relatorio,
    )
