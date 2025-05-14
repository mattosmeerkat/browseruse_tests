# Python 3.11 é recomendado para browser-use
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências básicas do sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    git \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt primeiro para aproveitar o cache de layers do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar browsers para Playwright (Chromium neste caso)
# O --no-shell é para evitar problemas em alguns ambientes Docker
RUN playwright install chromium --with-deps --no-shell

# Copiar o código da aplicação
COPY . .

# Expor a porta da API
EXPOSE 8000

# Executar a API com xvfb-run de forma mais robusta
CMD ["sh", "-c", "xvfb-run --auto-servernum --server-args='-screen 0 1280x1024x24' uvicorn api:app --host 0.0.0.0 --port 8000 2>/dev/null || uvicorn api:app --host 0.0.0.0 --port 8000"] 