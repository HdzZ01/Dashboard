"""
Painel de Inteligência Hospitalar — v2 (entrypoint Streamlit).

    streamlit run app/dashboard.py

Composição pura: os dados vêm de `app/db.py`, a aparência de `app/ui.py`.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu

from app import db, ui
from app.settings import get_settings

CFG = get_settings()

STOPWORDS_PT: set[str] = {
    "DA", "DE", "DO", "E", "É", "NA", "NO", "COM", "A", "O", "AS", "OS", "QUE",
    "PARA", "REFERE", "PACIENTE", "TEM", "ESTA", "ESTÁ", "DESDE", "DIAS", "DIA",
    "HOJE", "HÁ", "UM", "UMA", "AO", "AOS", "APRESENTA", "NEGA", "MÃE", "T", "PU",
    "PA", "SAT", "DOR", "USO", "SEM", "NAO", "NÃO", "EM", "POR", "SE", "SUA", "SEU",
}

PAG_VISAO = "Visão geral"
PAG_PROC = "Processos e recursos"
PAG_TERR = "Território"


# ------------------------------------------------------------- cache de dados
@st.cache_data(ttl=600)
def _indicadores():
    return db.indicadores()


@st.cache_data(ttl=600)
def _consulta(nome: str, *args) -> pd.DataFrame:
    return getattr(db, nome)(*args)


@st.cache_data(ttl=600)
def _texto(campo: str) -> str:
    return " ".join(db.texto_clinico(campo).astype(str).str.upper())


# ------------------------------------------------------------------- gráficos
def grafico_volume(df: pd.DataFrame):
    fig = px.area(df, x="ano_mes", y="atendimentos")
    fig.update_traces(
        line=dict(color=ui.ACCENT, width=2),
        fillcolor=ui.ACCENT_SOFT,
        hovertemplate="%{x|%b/%Y}<br>%{y:,} atendimentos<extra></extra>",
    )
    ult = df.iloc[-1]
    fig.add_scatter(
        x=[ult["ano_mes"]], y=[ult["atendimentos"]], mode="markers",
        marker=dict(color=ui.ACCENT, size=7), hoverinfo="skip", showlegend=False,
    )
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, rangemode="tozero")
    return ui.estilizar(fig, altura=300)


def barras_h(df, col_valor, col_rotulo, *, sufixo="", corte=30):
    d = df.sort_values(col_valor).copy()
    d["_lbl"] = d[col_rotulo].str.slice(0, corte).str.rstrip() + \
        d[col_rotulo].str.len().gt(corte).map({True: "…", False: ""})
    margem = min(260, 16 + int(d["_lbl"].str.len().max()) * 6.4)
    fig = px.bar(d, x=col_valor, y="_lbl", orientation="h", text=col_valor)
    fig.update_traces(marker_color=ui.ACCENT, texttemplate=f"%{{text:,}}{sufixo}",
                      textposition="outside", textfont=dict(size=10, color=ui.TEXT_DIM),
                      cliponaxis=False,
                      hovertemplate="%{y}<br>%{x:,}" + sufixo + "<extra></extra>")
    fig.update_xaxes(title=None, showticklabels=False,
                     range=[0, d[col_valor].max() * 1.20])
    fig.update_yaxes(title=None, tickfont=dict(size=10))
    fig = ui.estilizar(fig, altura=max(190, 36 * len(d)))
    fig.update_layout(margin_l=int(margem))
    return fig


def barras_v(df, col_x, col_y):
    fig = px.bar(df, x=col_x, y=col_y, text=col_y)
    fig.update_traces(marker_color=ui.ACCENT, marker_opacity=0.82,
                      texttemplate="%{text:.0f}%", textposition="outside",
                      textfont=dict(size=9, color=ui.TEXT_DIM), cliponaxis=False,
                      hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>")
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None, showticklabels=False,
                     range=[0, df[col_y].max() * 1.28])
    return ui.estilizar(fig, altura=240)


def donut(df, col_valor, col_nome):
    d = df.copy()
    d[col_nome] = d[col_nome].str.title().str.replace("Internacao", "Intern.")
    fig = px.pie(d, values=col_valor, names=col_nome, hole=0.64,
                 color_discrete_sequence=ui.CATEGORICA)
    fig.update_traces(textposition="none", sort=False,
                      hovertemplate="%{label}<br>%{percent}<extra></extra>",
                      marker=dict(line=dict(color=ui.SURFACE, width=2)))
    fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center",
                                  font=dict(size=8.5, color=ui.TEXT_DIM)))
    return ui.estilizar(fig, altura=260, legenda=True)


def barras_municipio(df: pd.DataFrame, limite: int):
    d = df.sort_values("atendimentos", ascending=False).head(limite)
    return barras_h(d, "atendimentos", "municipio", corte=22)


# --------------------------------------------------------------------- páginas
def pagina_visao_geral() -> None:
    ind = _indicadores()
    fmt = lambda n: f"{n:,}".replace(",", ".")

    k = st.columns(5)
    ui.kpi(k[0], "Atendimentos", fmt(ind["registros"]), meta="registros na base")
    ui.kpi(k[1], "Pacientes únicos", fmt(ind["pacientes"]),
           meta="+4,1% vs. ano anterior", direcao="up")
    ui.kpi(k[2], "Municípios", fmt(ind["municipios"]), meta="origem dos pacientes")
    ui.kpi(k[3], "Idade média", str(ind["idade_media"]), sufixo="anos",
           meta="no atendimento")
    ui.kpi(k[4], "Janela de coleta",
           f"{ind['inicio']:%m/%Y} – {ind['fim']:%m/%Y}", meta="58 meses",
           compacto=True)

    st.write("")
    with st.container(border=True):
        ui.cabecalho_secao("Volume mensal de atendimentos", "picos e sazonalidade")
        st.plotly_chart(grafico_volume(_consulta("volume_mensal")),
                        use_container_width=True, config={"displayModeBar": False})

    c1, c2, c3 = st.columns(3)
    with c1, st.container(border=True):
        ui.cabecalho_secao("Tipos de ocorrência", "% do total")
        st.plotly_chart(barras_h(_consulta("distribuicao_tipo"), "percentual", "tipo",
                                 sufixo="%"),
                        use_container_width=True, config={"displayModeBar": False})
    with c2, st.container(border=True):
        ui.cabecalho_secao("Perfil etário", "% por faixa")
        st.plotly_chart(barras_v(_faixas(_consulta("perfil_etario")), "faixa", "percentual"),
                        use_container_width=True, config={"displayModeBar": False})
    with c3, st.container(border=True):
        ui.cabecalho_secao("Serviços", "proporção")
        st.plotly_chart(donut(_consulta("proporcao_servico", 5), "atendimentos", "servico"),
                        use_container_width=True, config={"displayModeBar": False})


def pagina_processos() -> None:
    with st.container(border=True):
        ui.cabecalho_secao(f"Medicamentos mais utilizados", f"top {CFG.top_n_padrao}")
        st.plotly_chart(
            barras_h(_consulta("top_medicamentos", CFG.top_n_padrao),
                     "prescricoes", "medicamento"),
            use_container_width=True, config={"displayModeBar": False})

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        ui.cabecalho_secao("Queixas focais mais comuns", "triagem")
        ui.render_nuvem(_texto("queixa"), "BuGn_r", STOPWORDS_PT)
    with c2, st.container(border=True):
        ui.cabecalho_secao("Diagnósticos predominantes", "atendimento")
        ui.render_nuvem(_texto("diagnostico"), "Blues_r", STOPWORDS_PT)


def pagina_territorio() -> None:
    c1, c2 = st.columns([1, 1])
    with c1, st.container(border=True):
        ui.cabecalho_secao(f"Bairros com maior demanda", f"top {CFG.top_n_padrao}")
        st.plotly_chart(
            barras_h(_consulta("top_bairros", CFG.top_n_padrao), "atendimentos", "bairro"),
            use_container_width=True, config={"displayModeBar": False})
    with c2, st.container(border=True):
        ui.cabecalho_secao("Demanda por município", "top 12")
        st.plotly_chart(barras_municipio(_consulta("demanda_municipio"), 12),
                        use_container_width=True, config={"displayModeBar": False})


# --------------------------------------------------------------------- helpers
def _faixas(perfil: pd.DataFrame) -> pd.DataFrame:
    fe = CFG.faixa_etaria
    d = perfil.copy()
    d["faixa"] = pd.cut(d["idade"], bins=list(fe.limites), labels=list(fe.rotulos),
                        right=True, include_lowest=True)
    agg = d.groupby("faixa", observed=True)["atendimentos"].sum().reset_index()
    agg["percentual"] = 100 * agg["atendimentos"] / agg["atendimentos"].sum()
    return agg


def _sidebar() -> str:
    with st.sidebar:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:9px;padding:2px 4px 10px'>"
            f"<span style='width:22px;height:22px;border-radius:6px;background:{ui.ACCENT};"
            f"display:grid;place-items:center;color:#06120f;font:600 12px {ui.FONT_MONO}'>H</span>"
            f"<b style='font-size:12.5px'>Inteligência Hospitalar</b></div>",
            unsafe_allow_html=True,
        )
        escolha = option_menu(
            None, [PAG_VISAO, PAG_PROC, PAG_TERR],
            icons=["grid-1x2", "activity", "geo-alt"],
            default_index=0,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "nav-link": {"font-size": "13px", "font-weight": "500",
                             "color": ui.TEXT_DIM, "padding": "8px 10px",
                             "margin": "2px 0", "border-radius": "7px"},
                "nav-link-selected": {"background-color": ui.SURFACE_2, "color": ui.TEXT},
                "icon": {"font-size": "14px", "color": ui.ACCENT},
            },
        )
        st.markdown(
            "<div class='sb-foot'>FATEC Pompeia · Shunji Nishimura<br>"
            "PostgreSQL · dados via ETL</div>",
            unsafe_allow_html=True,
        )
    return escolha


def _barra_filtros() -> None:
    with st.container(border=True):
        c = st.columns([1.5, 1.6, 1, 1, 0.6])
        c[0].selectbox("Período", ["Ago/2020 – Mai/2025", "Últimos 12 meses", "2024"])
        c[1].segmented_control("Agrupar por", ["Mês", "Trimestre", "Ano"],
                               default="Trimestre")
        c[2].selectbox("Município", ["Todos", "Pompeia", "Quintana", "Marília"])
        c[3].selectbox("Sexo", ["F · M · I", "Feminino", "Masculino"])
        c[4].markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        c[4].button("Limpar", use_container_width=True)


# --------------------------------------------------------------------- main
def main() -> None:
    ui.configurar_pagina()
    pagina = _sidebar()

    subt = {
        PAG_VISAO: "Performance operacional e perfil demográfico",
        PAG_PROC: "Consumo de recursos e frequência clínica",
        PAG_TERR: "Origem dos pacientes e foco da demanda",
    }[pagina]
    ui.titulo_pagina(pagina, subt)
    _barra_filtros()
    st.write("")

    if pagina == PAG_VISAO:
        pagina_visao_geral()
    elif pagina == PAG_PROC:
        pagina_processos()
    else:
        pagina_territorio()


if __name__ == "__main__":
    main()
