# Painel de Inteligência Hospitalar

Dashboard interativo desenvolvido em Python para análise de performance operacional e perfil demográfico. O sistema automatiza a transformação de dados brutos de atendimento em indicadores estratégicos (KPIs) para gestão de saúde.

### O que o projeto faz:
* **Análise Operacional:** Monitoramento de volume de atendimentos e identificação de picos sazonais em séries históricas.
* **Gestão de Recursos:** Ranking de medicamentos mais prescritos e análise da proporção de serviços hospitalares utilizados.
* **Inteligência Geográfica:** Mapeamento interativo de origem dos pacientes (via Folium) e análise de demanda por bairros.
* **Frequência Clínica:** Processamento de linguagem natural (NLP) básico com Nuvem de Palavras para diagnósticos e queixas principais.

### Tecnologias Utilizadas:
* **Python:** Linguagem principal para processamento e lógica de negócio.
* **Streamlit:** Framework utilizado para a criação da interface web e visualização dinâmica.
* **Pandas/NumPy:** Manipulação eficiente de bases de dados e cálculos demográficos/estatísticos.
* **Plotly/Folium:** Bibliotecas responsáveis pela geração de gráficos interativos e mapas geográficos.

### Como funciona:
O script verifica e instala automaticamente todas as dependências necessárias no primeiro carregamento. Ele realiza a leitura de bases CSV, aplica filtros de data e faixa etária em tempo real e renderiza os dashboards de forma otimizada utilizando cache de memória para garantir performance.
