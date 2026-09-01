"""
Configuração central do projeto.

Tudo que na v1 estava espalhado como literal no código (caminhos, parâmetros
de análise, faixas etárias) vive aqui, alimentado por variáveis de ambiente
com valores padrão sensatos. Carregado uma vez e reutilizado.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Raiz do repositório (…/hospital-data-analytics)
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _env(chave: str, padrao: str) -> str:
    return os.environ.get(chave, padrao)


def _env_int(chave: str, padrao: int) -> int:
    try:
        return int(os.environ.get(chave, padrao))
    except (TypeError, ValueError):
        return padrao


@dataclass(frozen=True, slots=True)
class FaixaEtaria:
    """Limites (em anos) e rótulos das faixas etárias usadas nas análises."""

    limites: tuple[int, ...] = (0, 10, 20, 30, 40, 50, 60, 70, 80, 200)
    rotulos: tuple[str, ...] = (
        "0–10", "11–20", "21–30", "31–40", "41–50",
        "51–60", "61–70", "71–80", "81+",
    )

    def __post_init__(self) -> None:
        if len(self.limites) != len(self.rotulos) + 1:
            raise ValueError("limites deve ter exatamente len(rotulos)+1 elementos")


@dataclass(frozen=True, slots=True)
class Settings:
    # --- Conexão ---
    database_url: str = field(
        default_factory=lambda: _env(
            "DATABASE_URL",
            "postgresql+pg8000://hospital:hospital@localhost:5433/hospital",
        )
    )

    # --- Fonte ---
    csv_path: Path = field(
        default_factory=lambda: BASE_DIR / _env("CSV_PATH", "data/saude_processada.csv")
    )

    # --- Regras de negócio / análise (antes: hardcoded) ---
    min_ano_atendimento: int = field(
        default_factory=lambda: _env_int("MIN_ANO_ATENDIMENTO", 2015)
    )
    top_n_padrao: int = field(default_factory=lambda: _env_int("TOP_N_PADRAO", 10))
    faixa_etaria: FaixaEtaria = field(default_factory=FaixaEtaria)

    # --- ETL ---
    etl_chunk_size: int = field(default_factory=lambda: _env_int("ETL_CHUNK_SIZE", 20_000))

    # Valores fixos do domínio (não configuráveis, mas centralizados)
    sexos_validos: tuple[str, ...] = ("F", "M", "I")
    tipos_atendimento: tuple[str, ...] = (
        "ATENDIMENTO", "CIRURGIA", "MEDICAMENTO", "TRIAGEM",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Instância única de configuração (cacheada)."""
    return Settings()
