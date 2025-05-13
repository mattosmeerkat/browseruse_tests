#!/bin/bash

# Verificar se variáveis de ambiente estão configuradas
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando a partir de example.env..."
    cp example.env .env
    echo "Por favor, configure suas chaves de API no arquivo .env"
fi

# Definir API_KEY para testes
echo "API_KEY=123" > .env
echo "API_KEY definida como '123' para testes."

# API Key para debugging
echo "API Key atual: $API_KEY"

# Verificar se OPENAI_API_KEY está definida
grep -q "^OPENAI_API_KEY=" .env
if [ $? -ne 0 ]; then
    echo "OPENAI_API_KEY=sk-example-key" >> .env
    echo "AVISO: OPENAI_API_KEY adicionada com valor de exemplo. Configure uma chave válida."
fi

# Exportar variáveis de ambiente
export $(grep -v '^#' .env | xargs)

# Verificar se o uvicorn está instalado
if ! command -v uvicorn &> /dev/null; then
    echo "Uvicorn não encontrado. Instalando dependências..."
    pip install -r requirements.txt
fi

# Criar diretório para logs se não existir
mkdir -p logs

# Mostrar informações úteis
echo ""
echo "===================================="
echo "Iniciando a API de Browser Use"
echo "===================================="
echo "URL: http://localhost:8000"
echo "Documentação: http://localhost:8000/docs"
echo "API Key para testes: $API_KEY"
echo ""
echo "Exemplo de curl para teste:"
echo "curl -X POST http://localhost:8000/run_task \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer $API_KEY\" \\"
echo "  -d '{\"url\": \"https://www.gov.br/cvm/pt-br/pagina-inicial/\", \"task\": \"Extraia o título da página\"}'"
echo "===================================="
echo ""

# Iniciar a API
echo "Iniciando a API..."
uvicorn api:app --reload --host 0.0.0.0 --port 8000 