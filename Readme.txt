1.1. Abrir o Terminal
Abra o Prompt de Comando (Windows) ou PowerShell e navegue até a pasta do projeto:

cd C:\Dash

1.2. Instalação Manual do Streamlit (Obrigatório)
O único pacote que precisa ser instalado manualmente para que o script de instalação automática funcione corretamente é o próprio Streamlit.

pip install streamlit

2. Execução da Dashboard
Após instalar o Streamlit, o sistema de instalação automática do script cuidará do restante.

2.1. Comando de Execução
Execute o script Streamlit:

streamlit run app_dashboard.py

2.2. O que Acontece
Instalação Automática: Na primeira execução, o terminal mostrará diversas mensagens de instalação (Instalando pandas..., etc.). Isso é normal e garante que todas as bibliotecas (Plotly, WordCloud, Folium) estejam instaladas.

Carregamento: Após a instalação, a dashboard será aberta automaticamente no seu navegador web padrão.