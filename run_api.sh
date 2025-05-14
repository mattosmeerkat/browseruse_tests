#!/bin/bash
# Muda para o diretório do script, garantindo que os caminhos relativos funcionem
cd "$(dirname "$0")"

# AVISO: Este script é destinado APENAS para desenvolvimento local.
# NÃO o utilize para iniciar a aplicação em um ambiente de produção.
# Em produção, as variáveis de ambiente devem ser gerenciadas de forma segura
# e o serviço deve ser iniciado via Docker Compose ou outro orquestrador.

# Verificar se variáveis de ambiente estão configuradas
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando a partir de example.env..."
    cp example.env .env
    echo "AVISO IMPORTANTE: O arquivo .env foi copiado de example.env."
    echo "Configure suas chaves de API e outras variáveis (como OPENAI_API_KEY, API_KEY, ENVIRONMENT=production, LOG_GROUP_NAME) no arquivo .env antes de continuar para produção."
    echo "Para desenvolvimento local, uma API_KEY de teste pode ser usada, mas garanta que ENVIRONMENT não seja 'production' com chaves de teste."
fi

# Verificar se OPENAI_API_KEY está definida no .env
if ! grep -q "^OPENAI_API_KEY=" .env || [[ "$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2)" == "" ]]; then
    echo "AVISO: OPENAI_API_KEY não está definida ou está vazia no arquivo .env."
    echo "A aplicação pode não funcionar corretamente sem uma OPENAI_API_KEY válida."
    echo "Por favor, adicione OPENAI_API_KEY=sua_chave_aqui ao arquivo .env"
fi

# Exportar variáveis de ambiente do .env para este script (apenas para execução local)
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else 
  echo ".env file not found. Skipping export of environment variables for local run."
fi

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
echo "Iniciando a API de Browser Use (MODO DESENVOLVIMENTO LOCAL)"
echo "===================================="
echo "URL: http://localhost:8000"
echo "Documentação: http://localhost:8000/docs"

DEV_API_KEY=$(grep "^API_KEY=" .env | cut -d'=' -f2)
if [[ -z "$DEV_API_KEY" ]]; then
  DEV_API_KEY="SUA_API_KEY_CONFIGURADA_NO_.ENV"
fi

echo "API Key para testes (definida em .env): $DEV_API_KEY"
echo "Certifique-se que ENVIRONMENT está como 'development' em .env se estiver usando chaves de teste."

echo ""
echo "Exemplo de curl para teste (substitua pela API_KEY do seu .env):"
echo "curl -X POST http://localhost:8000/run_task \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"Authorization: Bearer $DEV_API_KEY\" \\"
echo "  -d '{\"url\": \"https://www.gov.br/cvm/pt-br/pagina-inicial/\", \"task\": \"Extraia o título da página\"}'"
echo "===================================="
echo ""

# Iniciar a API
echo "Iniciando a API..."
uvicorn api:app --reload --host 0.0.0.0 --port 8000 