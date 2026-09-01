"""
Coordenadas aproximadas (sede) dos municípios da microrregião de Marília /
Pompéia-SP, usadas para posicionar a demanda no mapa.

As chaves estão em CAIXA ALTA, sem acento uniforme, para casar com o valor já
padronizado de `cidade` vindo do transform. Municípios fora deste dicionário
entram no banco com latitude/longitude nulas (não aparecem no mapa).
"""

from __future__ import annotations

# nome_municipio -> (latitude, longitude)
COORDENADAS_MUNICIPIOS: dict[str, tuple[float, float]] = {
    "POMPEIA": (-22.1103, -50.1706),
    "ORIENTE": (-22.1553, -50.0908),
    "MARILIA": (-22.2139, -49.9458),
    "QUINTANA": (-22.0989, -50.3078),
    "HERCULANDIA": (-22.0028, -50.3903),
    "ALVARO DE CARVALHO": (-22.0808, -49.7194),
    "ALTO ALEGRE": (-21.9367, -50.1586),
    "QUEIROZ": (-21.8378, -50.2258),
    "GALIA": (-22.2933, -49.5508),
    "GARCA": (-22.2100, -49.6547),
    "VERA CRUZ": (-22.2181, -49.8214),
    "LUPERCIO": (-22.2650, -49.8261),
    "OCAUCU": (-22.4322, -49.9214),
    "FERNAO": (-22.3319, -49.5136),
    "JULIO MESQUITA": (-22.0072, -49.7944),
    "GETULINA": (-21.7972, -49.9308),
    "GUARANTA": (-21.8981, -49.5928),
    "CAFELANDIA": (-21.8036, -49.6108),
    "LINS": (-21.6786, -49.7425),
    "PROMISSAO": (-21.5375, -49.8578),
    "TUPA": (-21.9350, -50.5136),
    "IACRI": (-21.8564, -50.6828),
    "BASTOS": (-21.9214, -50.7325),
    "RINOPOLIS": (-21.7300, -50.7250),
    "PARAPUA": (-21.7803, -50.7947),
    "ECHAPORA": (-22.4319, -50.2039),
    "SAO PEDRO DO TURVO": (-22.7447, -49.7286),
    "ADAMANTINA": (-21.6853, -51.0742),
    "BAURU": (-22.3147, -49.0606),
    "ARCO IRIS": (-21.7683, -50.4478),
    "BORA": (-22.2497, -49.7139),
}


def coordenadas(municipio: str | None) -> tuple[float | None, float | None]:
    """Retorna (lat, lon) para o município, ou (None, None) se desconhecido."""
    if not municipio:
        return (None, None)
    return COORDENADAS_MUNICIPIOS.get(municipio.strip().upper(), (None, None))
