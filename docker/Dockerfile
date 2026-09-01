# Imagem única compartilhada pelos serviços `etl` e `app`.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências primeiro (cache de camada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código + DDL
COPY app/ ./app/
COPY etl/ ./etl/
COPY db/  ./db/

# Usuário sem privilégios
RUN useradd --create-home appuser
USER appuser

EXPOSE 8501

# Sobrescrito pelo compose por serviço
CMD ["python", "-m", "etl.run_etl"]
