FROM python:3.10-slim

WORKDIR /app

# Instalar dependências básicas do sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Playwright (com chromium incluído)
RUN pip install playwright && playwright install --with-deps

# Copiar requirements.txt primeiro para aproveitar o cache de layers do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor a porta da API
EXPOSE 8000

# Executar a API (correção do path do módulo)
CMD ["uvicorn", "browseruse_tests.api:app", "--host", "0.0.0.0", "--port", "8000"] 