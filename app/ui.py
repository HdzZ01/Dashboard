"""
Camada de apresentação: tema, CSS, e helpers de layout/gráfico.

Tudo que é "como o painel se parece" mora aqui. O `dashboard.py` só compõe:
chama `db` para os dados e `ui` para desenhar.
"""

from __future__ import annotations

import streamlit as st

# --------------------------------------------------------------------- paleta
BG          = "#0d1015"
SURFACE     = "#161a21"
SURFACE_2   = "#1c222c"
BORDER      = "#262d38"
BORDER_2    = "#333b48"
TEXT        = "#e8ebf1"
TEXT_DIM    = "#8b94a3"
TEXT_FAINT  = "#5c6472"
ACCENT      = "#2db8a3"
ACCENT_SOFT = "rgba(45,184,163,0.14)"
POS         = "#57b981"
NEG         = "#d17f70"

# séries categóricas (donut, barras multi-cor): acento + tons neutros
CATEGORICA = [ACCENT, "#3f8078", BORDER_2, SURFACE_2, TEXT_FAINT]

FONT_SANS = "'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif"
FONT_MONO = "'IBM Plex Mono', ui-monospace, monospace"


# --------------------------------------------------------------------- página
def configurar_pagina() -> None:
    st.set_page_config(
        page_title="Inteligência Hospitalar",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _injetar_css()


def _injetar_css() -> None:
    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

          html, body, [class*="css"], .stMarkdown, .stButton, .stSelectbox,
          [data-testid="stSidebar"] {{ font-family: {FONT_SANS}; }}

          /* remove chrome padrão */
          #MainMenu, header[data-testid="stHeader"], [data-testid="stToolbar"],
          [data-testid="stStatusWidget"], footer {{ display: none !important; }}

          .block-container {{ padding: 1.4rem 2rem 3rem; max-width: 1360px; }}

          /* sidebar */
          [data-testid="stSidebar"] {{
            background: {SURFACE}; border-right: 1px solid {BORDER};
          }}
          [data-testid="stSidebar"] .block-container {{ padding-top: 1rem; }}
          .sb-foot {{
            color: {TEXT_FAINT}; font-size: 10.5px; line-height: 1.6;
            letter-spacing: .03em; margin-top: 2rem;
          }}

          /* título da página */
          .page-h1 {{ font-size: 17px; font-weight: 600; letter-spacing: -.01em; margin: 0; }}
          .page-sub {{ color: {TEXT_DIM}; font-size: 12.5px; margin: 2px 0 0; }}

          /* KPI cards */
          .kpi {{
            background: {SURFACE}; border: 1px solid {BORDER};
            border-radius: 10px; padding: 14px 15px; height: 100%;
          }}
          .kpi .lab {{
            font-family: {FONT_MONO}; font-size: 10px; letter-spacing: .09em;
            text-transform: uppercase; color: {TEXT_DIM};
          }}
          .kpi .val {{
            font-family: {FONT_MONO}; font-variant-numeric: tabular-nums;
            font-size: 21px; font-weight: 500; letter-spacing: -.02em;
            color: {TEXT}; margin-top: 6px;
          }}
          .kpi .val small {{ font-size: 12px; color: {TEXT_FAINT}; font-weight: 400; }}
          .kpi .meta {{ font-size: 11px; margin-top: 3px; color: {TEXT_FAINT}; }}
          .kpi .meta.up {{ color: {POS}; font-family: {FONT_MONO}; }}
          .kpi .meta.down {{ color: {NEG}; font-family: {FONT_MONO}; }}

          /* cards nativos (st.container(border=True)) */
          [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {SURFACE}; border-color: {BORDER} !important;
            border-radius: 10px;
          }}

          /* cabeçalho de seção dentro de um card */
          .sec-h {{
            display: flex; justify-content: space-between; align-items: baseline;
            border-bottom: 1px solid {BORDER}; padding-bottom: 10px; margin-bottom: 14px;
          }}
          .sec-h h3 {{ font-size: 12.5px; font-weight: 600; margin: 0; letter-spacing: .01em; }}
          .sec-h span {{
            font-family: {FONT_MONO}; font-size: 10px; letter-spacing: .09em;
            text-transform: uppercase; color: {TEXT_DIM};
          }}

          /* barra de filtros */
          .filterbar-wrap [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {SURFACE};
          }}
          .stSelectbox label, .stMultiSelect label, [data-testid="stWidgetLabel"] p {{
            font-family: {FONT_MONO} !important; font-size: 10px !important;
            letter-spacing: .09em; text-transform: uppercase; color: {TEXT_DIM} !important;
          }}

          /* option-menu: encosta na paleta */
          .nav-link-selected {{ background-color: {SURFACE_2} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------- helpers
def titulo_pagina(titulo: str, subtitulo: str) -> None:
    st.markdown(
        f"<p class='page-h1'>{titulo}</p><p class='page-sub'>{subtitulo}</p>",
        unsafe_allow_html=True,
    )


def kpi(coluna, rotulo: str, valor: str, *, sufixo: str = "",
        meta: str | None = None, direcao: str | None = None,
        compacto: bool = False) -> None:
    val = f"{valor}<small> {sufixo}</small>" if sufixo else valor
    cls = f"meta {direcao}" if direcao else "meta"
    meta_html = f"<div class='{cls}'>{meta}</div>" if meta else ""
    estilo = " style='font-size:14px;letter-spacing:0'" if compacto else ""
    coluna.markdown(
        f"<div class='kpi'><div class='lab'>{rotulo}</div>"
        f"<div class='val'{estilo}>{val}</div>{meta_html}</div>",
        unsafe_allow_html=True,
    )


def cabecalho_secao(titulo: str, nota: str = "") -> None:
    st.markdown(
        f"<div class='sec-h'><h3>{titulo}</h3><span>{nota}</span></div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------- Plotly
def estilizar(fig, altura: int = 300, legenda: bool = False):
    fig.update_layout(
        template="none",
        height=altura,
        margin=dict(l=52, r=16, t=14, b=34, autoexpand=True),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_SANS, color=TEXT, size=12),
        showlegend=legenda,
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                    font=dict(size=9, color=TEXT_DIM)),
        title_text="",
        colorway=CATEGORICA,
        hoverlabel=dict(font_family=FONT_SANS, font_size=12,
                        bgcolor=SURFACE_2, bordercolor=BORDER_2),
    )
    eixo = dict(zerolinecolor=BORDER, linecolor=BORDER,
                tickfont=dict(color=TEXT_DIM, size=10, family=FONT_MONO),
                title_font=dict(color=TEXT_FAINT, size=10))
    # só o eixo Y mantém grade — menos ruído
    fig.update_xaxes(showgrid=False, **eixo)
    fig.update_yaxes(showgrid=True, gridcolor=BORDER, **eixo)
    return fig


# --------------------------------------------------------------------- wordcloud
def render_nuvem(texto: str, colormap: str, stopwords: set[str]) -> None:
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud

    nuvem = WordCloud(
        width=800, height=380, background_color=None, mode="RGBA",
        max_words=90, stopwords=stopwords, colormap=colormap,
        prefer_horizontal=0.95, font_path=None,
    ).generate(texto)

    fig, ax = plt.subplots(figsize=(8, 3.8))
    fig.patch.set_alpha(0)
    ax.imshow(nuvem, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
