import subprocess
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

# --- Bloco 1: Verificação e Instalação de Dependências ---

def check_and_install_package(package):
    """Verifica se o pacote está instalado e o instala se necessário."""
    try:
        import_name = package.split('-')[0]
        __import__(import_name) 
    except ImportError:
        print(f"Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Lista de pacotes necessários
required_packages = [
    "streamlit", 
    "pandas", 
    "plotly", 
    "wordcloud", 
    "folium", 
    "streamlit-folium",
    "numpy",
    "Pillow", 
    "matplotlib"
]

for package in required_packages:
    check_and_install_package(package)

# --- Bloco 2: Importação Standard (Após a instalação garantida) ---
try:
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    from wordcloud import WordCloud, STOPWORDS
    import folium
    from streamlit_folium import st_folium
    from PIL import Image
    
except ImportError as e:
    st.error(f"Erro Crítico de Importação após a instalação: {e}. Verifique o ambiente virtual.")
    sys.exit(1)


# =================================================================
#                         INÍCIO DA DASHBOARD
# =================================================================

# --- Configurações Iniciais da Página ---
st.set_page_config(
    layout="wide",
    page_title="Fatec - Painel de Análise Hospitalar",
    initial_sidebar_state="expanded"
)

# --- Cores Fatec ---
FATEC_RED = '#d4222a'
FATEC_GRAY = '#444c52'
FATEC_YELLOW = '#f59b00'

# --- Funções de Pré-Processamento ---

@st.cache_data
def load_data(file_path):
    """
    Carrega e preprocessa o DataFrame principal.
    O caminho é ajustado para buscar o arquivo dentro da pasta 'data/'.
    """
    try:
        # Caminho corrigido para a pasta 'data/'
        df = pd.read_csv(f"data/{file_path}") 
        df['dataEntrada'] = pd.to_datetime(df['dataEntrada'], errors='coerce')
        df['dataNascimento'] = pd.to_datetime(df['dataNascimento'], errors='coerce')
        return df
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{file_path}' não foi encontrado. Verifique se está em **data/{file_path}**.")
        return pd.DataFrame()

@st.cache_data
def calculate_age(birth_date):
    """Calcula a idade a partir da data de nascimento."""
    if pd.isna(birth_date):
        return np.nan
    today = datetime.now()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

# --- Carregamento de Dados ---
# A função é chamada com o NOME do arquivo, o prefixo 'data/' é adicionado DENTRO da função.
df_original = load_data('saude_processada.csv')
if df_original.empty:
    st.stop()

# --- 3. Sidebar e Logo (FIX DE CARREGAMENTO) ---
# Procura o arquivo da logo dentro da pasta 'img/' (Corrigido)
logo_file_path = next(Path('img').glob('fatec_pompeia.*'), None)
if not logo_file_path:
    logo_file_path = next(Path('img').glob('image_1fde71.*'), None)

if logo_file_path:
    st.sidebar.image(str(logo_file_path), use_container_width=True)
else:
    st.sidebar.warning("Aviso: Logo não encontrada (Verifique se fatec_pompeia ou image_1fde71 está dentro da pasta **img/**).")

st.sidebar.markdown(f"# Painel de Análise Hospitalar")
page = st.sidebar.radio("Navegação", ["Visão Geral", "Análise Focada em Processos e Recursos"])
st.sidebar.markdown("---")
st.sidebar.info("Dashboard desenvolvida utilizando Python (Streamlit, Plotly, Pandas).")


# =================================================================
#                         PÁGINA 1: VISÃO GERAL
# =================================================================
if page == "Visão Geral":
    st.title("Visão Geral: Performance Operacional e Perfil Demográfico")

    # --- Cards de Resumo ---
    total_atendimentos = df_original.shape[0]
    df_entradas = df_original.dropna(subset=['dataEntrada'])
    periodo_inicio = df_entradas['dataEntrada'].min().strftime('%d/%m/%Y') if not df_entradas.empty else 'N/A'
    periodo_fim = df_entradas['dataEntrada'].max().strftime('%d/%m/%Y') if not df_entradas.empty else 'N/A'


    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Registros (Base)", f"{total_atendimentos:,.0f}")
    with col2:
        st.metric("Início da Coleta", periodo_inicio)
    with col3:
        st.metric("Data Mais Recente", periodo_fim)
    with col4:
        st.metric("Total de IDs Únicos", f"{df_original['_id'].nunique():,.0f}")
    st.markdown("---")

    # --- Análise de Tendência (Equipe 6) ---
    st.header("📈 Análise de Tendência: Série Histórica e Sazonalidade de Atendimentos")
    df_volume = df_original.dropna(subset=['dataEntrada']).copy()
    df_volume['AnoMes'] = df_volume['dataEntrada'].dt.to_period('M').astype(str)
    volume_mensal_data = df_volume.groupby('AnoMes').size().reset_index(name='Contagem')

    fig_volume = px.line(
        volume_mensal_data,
        x='AnoMes',
        y='Contagem',
        title='Volume Mensal de Atendimentos (Identificação de Picos)',
        markers=True,
        color_discrete_sequence=[FATEC_RED]
    )
    fig_volume.update_layout(xaxis_title="Período (Mês/Ano)", yaxis_title="Contagem de Atendimentos")
    st.plotly_chart(fig_volume, use_container_width=True)

    # --- Estrutura de Ocorrências (Equipe 1) & Perfil Demográfico (Equipe 7) ---
    col5, col6 = st.columns(2)

    with col5:
        st.header("📊 Estrutura de Ocorrências: Distribuição de Tipos de Atendimento")
        tipo_data = df_original['tipo'].value_counts(normalize=True).mul(100).head(5).reset_index()
        tipo_data.columns = ['Tipo de Ocorrência', 'Percentual']
        
        fig_tipo = px.bar(
            tipo_data.sort_values('Percentual'),
            x='Percentual',
            y='Tipo de Ocorrência', 
            orientation='h',
            title='Top 5 Tipos de Ocorrência Registrados',
            text='Percentual',
            color_discrete_sequence=[FATEC_YELLOW]
        )
        fig_tipo.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_tipo.update_layout(xaxis_title="Representatividade no Total (%)", yaxis_title="", uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig_tipo, use_container_width=True)

    with col6:
        st.header("👶 Perfil Demográfico: Distribuição de Pacientes por Faixa Etária")
        df_original['Idade'] = df_original['dataNascimento'].apply(calculate_age)
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 100]
        labels = ['0-10 anos', '11-20 anos', '21-30 anos', '31-40 anos', '41-50 anos', '51-60 anos', '61-70 anos', '71-80 anos', '81+ anos']
        df_original['Faixa Etária'] = pd.cut(df_original['Idade'], bins=bins, labels=labels, right=True, include_lowest=True)
        faixa_etaria_data = df_original['Faixa Etária'].value_counts(normalize=True).mul(100).round(2).reset_index()
        faixa_etaria_data.columns = ['Faixa Etária', 'Percentual']
        
        fig_idade = px.bar(
            faixa_etaria_data.sort_values('Percentual', ascending=False),
            x='Faixa Etária',
            y='Percentual',
            title='Distribuição de Atendimentos por Faixa Etária',
            color='Faixa Etária',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_idade.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        fig_idade.update_layout(xaxis_title="Faixa Etária", yaxis_title="Percentual de Atendimentos (%)")
        st.plotly_chart(fig_idade, use_container_width=True)


# =================================================================
#                         PÁGINA 2: ANÁLISE DETALHADA
# =================================================================
elif page == "Análise Focada em Processos e Recursos":
    st.title("Análise Focada: Processos, Recursos e Impacto Geográfico")

    # --- Gestão de Recursos (Equipe 9) e Processos de Atendimento (Equipe 3) ---
    col7, col8 = st.columns(2)

    with col7:
        st.header("💊 Gestão de Recursos: Consumo e Uso de Medicamentos Frequentes")
        medicamento_data = df_original['descricaoMedicamento'].value_counts().head(10).reset_index()
        medicamento_data.columns = ['Medicamento', 'Volume de Uso']

        fig_med = px.bar(
            medicamento_data.sort_values('Volume de Uso', ascending=False),
            x='Volume de Uso',
            y='Medicamento',
            orientation='h',
            title='Ranking dos 10 Medicamentos Mais Utilizados',
            color_discrete_sequence=['#1abc9c'] # Verde Menta
        )
        fig_med.update_traces(texttemplate='%{x:,.0f}', textposition='outside')
        fig_med.update_layout(xaxis_title="Contagem de Prescrições", yaxis_title="")
        st.plotly_chart(fig_med, use_container_width=True)

    with col8:
        st.header("🏥 Processos de Atendimento: Proporção e Tipos de Serviço Hospitalar")
        servico_data = df_original['servico'].value_counts().head(5).reset_index()
        servico_data.columns = ['Serviço Hospitalar', 'Contagem']
        
        fig_servico = px.pie(
            servico_data,
            values='Contagem',
            names='Serviço Hospitalar', 
            title='Proporção de Atendimentos por Serviço',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_servico.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_servico, use_container_width=True)

    st.markdown("---")

    # --- Frequência Clínica (Equipe 5) ---
    st.header("💬 Frequência Clínica: Diagnóstico e Queixas Mais Recorrentes")
    col9, col10 = st.columns(2)
    
    stop_words_pt = set(STOPWORDS)
    stop_words_pt.update(['DA', 'DE', 'DO', 'E', 'É', 'NA', 'NO', 'COM', 'A', 'O', 'AS', 'OS', 'QUE', 'PARA', 'REFERE', 'PACIENTE', 'TEM', 'ESTA', 'ESTÁ', 'DESDE', 'DIAS', 'DIA', 'HOJE', 'HÁ', 'UM', 'UMA', 'AO', 'AOS', 'APRESENTA', 'NEGA', 'MÃE', 'T', 'PU', 'PA', 'SAT', 'DOR', 'USO', 'SEM', 'NAO'])

    # Nuvem de Palavras - Queixas
    with col9:
        st.subheader("Queixas Focais Mais Comuns")
        queixa_text = ' '.join(df_original['queixa'].dropna().astype(str).str.upper().tolist())
        
        wc_queixa = WordCloud(background_color="white", max_words=100, stopwords=stop_words_pt, width=800, height=400, colormap='Reds').generate(queixa_text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc_queixa, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

    # Nuvem de Palavras - Diagnósticos
    with col10:
        st.subheader("Diagnósticos Predominantes")
        diagnostico_text = ' '.join(df_original['diagnostico'].dropna().astype(str).str.upper().tolist())
        
        wc_diag = WordCloud(background_color="white", max_words=100, stopwords=stop_words_pt, width=800, height=400, colormap='Blues').generate(diagnostico_text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wc_diag, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
        
    st.markdown("---")

    # --- Inteligência Geográfica (Equipe 2/8) ---
    st.header("📍 Inteligência Geográfica: Origem dos Pacientes e Foco da Demanda")
    
    col11, col12 = st.columns(2)
    with col11:
        st.subheader("Top 10 Bairros com Maior Demanda")
        bairro_data = df_original['bairro'].value_counts().head(10).reset_index()
        bairro_data.columns = ['Bairro de Origem', 'Contagem']
        
        fig_bairro = px.bar(
            bairro_data.sort_values('Contagem', ascending=True),
            x='Contagem',
            y='Bairro de Origem', 
            orientation='h',
            title='Contagem de Atendimentos por Bairro',
            color_discrete_sequence=[FATEC_RED]
        )
        fig_bairro.update_layout(xaxis_title="Volume de Atendimentos", yaxis_title="")
        st.plotly_chart(fig_bairro, use_container_width=True)

    with col12:
        st.subheader("Visualização Geográfica (Mapa Interativo)")
        st.info("⚠️ **Atenção:** Para criar um **Mapa de Calor** (Equipe 8) funcional, seriam necessárias as colunas de Latitude e Longitude dos bairros/cidades. O mapa abaixo ilustra o potencial interativo.")
        
        # Coordenadas de Pompeia/SP (exemplo)
        m = folium.Map(location=[-22.12, -50.21], zoom_start=12) 
        
        folium.Marker(
            [-22.12, -50.21], 
            popup="Unidade Hospitalar - FATEC", 
            tooltip="Localização Central" 
        ).add_to(m)

        st_folium(m, width=700, height=400)
                                                                                                         