# Imagem base Python 3.11
FROM python:3.11-slim

# Metadados
LABEL maintainer="seu-email@exemplo.com"
LABEL description="Sistema de Automação Shopee + Instagram com LangGraph"

# Define diretório de trabalho
WORKDIR /app

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivo de dependências
COPY requirements.txt .

# Instala dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia o código da aplicação
COPY app/ ./app/
COPY scripts/ ./scripts/

# Cria diretórios necessários
RUN mkdir -p /app/logs /app/data

# Usuário não-root para segurança
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Comando padrão
CMD ["python", "-m", "app.main"]
