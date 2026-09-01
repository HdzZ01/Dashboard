"""
Orquestrador do ETL.

    python -m etl.run_etl

Fluxo: extract -> transform -> load -> validate.
Sai com código 1 se qualquer validação obrigatória falhar.
"""

from __future__ import annotations

import logging
import sys
import time

from app.settings import get_settings
from etl.extract import carregar_csv
from etl.load import carregar, criar_engine
from etl.transform import transformar
from etl.validate import validar


def _configurar_logs() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(name)-16s %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    _configurar_logs()
    log = logging.getLogger("etl")
    cfg = get_settings()
    inicio = time.perf_counter()

    log.info("Fonte:  %s", cfg.csv_path)
    log.info("Destino: %s", cfg.database_url.split("@")[-1])

    bruto = carregar_csv(cfg.csv_path)
    resultado = transformar(bruto)
    carregar(resultado)

    engine = criar_engine()
    validacao = validar(engine, resultado.relatorio)
    engine.dispose()

    _imprimir_resumo(log, resultado.relatorio, validacao)
    log.info("Concluído em %.1fs", time.perf_counter() - inicio)

    if not validacao.ok:
        log.error("Validação falhou — ETL NÃO concluído.")
        return 1
    log.info("Todas as validações passaram.")
    return 0


def _imprimir_resumo(log: logging.Logger, transform, validacao) -> None:
    log.info("-" * 60)
    log.info("RESUMO DO TRANSFORM")
    log.info("  linhas lidas ............... %s", f"{transform.linhas_lidas:,}")
    log.info("  rejeitadas (nascimento) .... %s", f"{transform.linhas_rejeitadas_nascimento:,}")
    log.info("  linhas aceitas ............. %s", f"{transform.linhas_aceitas:,}")
    log.info("  entradas fora de faixa ..... %s  (-> NULL)", f"{transform.entradas_fora_de_faixa:,}")
    log.info("  saídas < entrada ........... %s  (-> NULL)", f"{transform.saidas_anuladas:,}")
    log.info("  pacientes / municípios ..... %s / %s", f"{transform.pacientes:,}", transform.municipios)
    log.info("  bairros / serviços / medic.. %s / %s / %s",
             f"{transform.bairros:,}", transform.servicos, transform.medicamentos)
    log.info("-" * 60)
    log.info("VALIDAÇÕES")
    for c in validacao.checagens:
        marca = "OK " if c.ok else "FALHA"
        extra = f"  ({c.detalhe})" if c.detalhe and not c.ok else ""
        log.info("  [%s] %s%s", marca, c.nome, extra)
    log.info("-" * 60)


if __name__ == "__main__":
    sys.exit(main())
