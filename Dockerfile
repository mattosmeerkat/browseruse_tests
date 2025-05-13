FROM python:3.10-slim

WORKDIR /app

# Instalar dependências do sistema e Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chromium e suas dependências
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Playwright
RUN pip install playwright && playwright install chromium

# Copiar requirements.txt primeiro para aproveitar o cache de layers do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor a porta da API
EXPOSE 8000

# Executar a API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 