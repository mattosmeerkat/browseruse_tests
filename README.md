# Browser Use API

API para execução de tarefas automatizadas de navegação web usando LLMs e browser automation.

## Requisitos

- Python 3.8+
- Docker e Docker Compose (para implantação em contêiner)

## Configuração

1. Clone o repositório
2. Configure o arquivo `.env` com suas chaves de API (veja `example.env` para referência)
3. Configure uma `API_KEY` forte para autenticação da API

```bash
cp example.env .env
# Edite o arquivo .env e configure suas chaves de API
# Certifique-se de definir uma API_KEY segura:
echo "API_KEY=sua-chave-secreta-aqui" >> .env
```

### Configuração para Ambiente de Produção

Para uso em produção, certifique-se de:

1. Gerar uma API_KEY forte (32+ caracteres):
   ```bash
   # No Linux/Mac
   openssl rand -base64 32
   ```

2. Configurar a variável ENVIRONMENT:
   ```bash
   echo "ENVIRONMENT=production" >> .env
   ```

3. Em produção, a chave de teste "123" é desabilitada automaticamente.

## Executando localmente para testes

### Modo Desenvolvimento

Para facilitar o desenvolvimento local:

```bash
# Habilitar o modo desenvolvimento (ativa a chave "123" para testes)
echo "ENVIRONMENT=development" >> .env
```

### Método 1: Usando o script de conveniência

```bash
chmod +x run_api.sh
./run_api.sh
```

### Método 2: Manual

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute o servidor uvicorn:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em `http://localhost:8000`. Você pode acessar a documentação interativa em `http://localhost:8000/docs`.

## Implantação com Docker

Para implantar usando Docker:

```bash
docker-compose up -d
```

## Exemplos de uso

### Corpo da requisição

Para enviar uma tarefa para a API, use o seguinte formato:

**Endpoint:** POST `/run_task`

**Headers:**
```
Authorization: Bearer sua-chave-secreta-aqui
Content-Type: application/json
```

**Corpo da requisição:**
```json
{
  "url": "https://www.gov.br/cvm/pt-br/pagina-inicial/",
  "task": "Acesse o site, clique em 'Assuntos', depois em 'Notícias'. Leia as notícias do dia de ontem e extraia o título, data e autor de cada uma. Retorne os resultados em formato JSON.",
  "model": "gpt-4.1",
  "timeout": 300,
  "additional_params": {
    "max_iterations": 10,
    "verbose": true
  }
}
```

**Exemplo de resposta:**
```json
{
  "task_id": "task_1a2b3c4d",
  "status": "completed",
  "result": [
    {
      "titulo": "CVM alerta sobre empresa não autorizada",
      "data_publicacao": "12/07/2023",
      "dia_semana": "quarta-feira",
      "hora_publicacao": "14:30",
      "feito_por": "Nome do Autor",
      "regulador": "CVM",
      "link": "https://www.gov.br/cvm/..."
    },
    {
      "titulo": "Outro título de notícia",
      "data_publicacao": "12/07/2023",
      "dia_semana": "quarta-feira",
      "hora_publicacao": "10:15",
      "feito_por": "Outro Autor",
      "regulador": "CVM",
      "link": "https://www.gov.br/cvm/..."
    }
  ]
}
```

### Exemplos com curl

```bash
# Para produção (substitua pela sua API_KEY)
curl -X POST "http://localhost:8000/run_task" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer MHBp3X8JfKw9yR2sTqZ5vC7bD6nG4mL1aE0xN" \
  -d '{
    "url": "https://www.gov.br/cvm/pt-br/pagina-inicial/",
    "task": "Acesse o site, clique em \"Assuntos\", depois em \"Notícias\". Extraia o título e data das 3 notícias mais recentes.",
    "model": "gpt-4.1"
  }'

# Para desenvolvimento local (usando a chave de teste)
curl -X POST "http://localhost:8000/run_task" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 123" \
  -d '{
    "url": "https://www.gov.br/cvm/pt-br/pagina-inicial/",
    "task": "Extraia o título da página principal.",
    "model": "gpt-4.1"
  }'
```

### Usando o cliente Python

```bash
python example_client.py --url "https://www.gov.br/cvm/pt-br/pagina-inicial/" \
  --task "Acesse o site, clique em 'Assuntos', depois em 'Notícias'. Extraia o título e data das 3 notícias mais recentes." \
  --output "noticias_recentes.json"
```

## Implantação na AWS

### EC2 (Recomendado)

1. **Provisionar Instância EC2**
   - Acesse o Console AWS e navegue até o serviço EC2
   - Clique em "Launch Instance"
   - Selecione uma imagem Ubuntu Server 22.04 LTS
   - Escolha o tipo de instância t3.medium (mínimo recomendado) ou superior
   - Configure o armazenamento com pelo menos 20GB
   - Configure um Security Group com as seguintes regras:
     - SSH (porta 22): Restrinja ao seu IP
     - HTTP (porta 80): Se for usar proxy reverso
     - TCP personalizado (porta 8000): Para acesso direto à API

2. **Configurar a Instância**
   ```bash
   # Atualizar pacotes
   sudo apt update && sudo apt upgrade -y

   # Instalar Docker e Docker Compose
   sudo apt install -y docker.io docker-compose

   # Adicionar usuário ao grupo docker
   sudo usermod -aG docker ubuntu
   newgrp docker
   ```

3. **Clonar e Configurar o Projeto**
   ```bash
   # Clonar o repositório
   git clone [seu-repositorio] browseruse-api
   cd browseruse-api

   # Configurar o arquivo .env
   cp example.env .env

   # Gerar uma API_KEY forte para produção
   API_KEY=$(openssl rand -base64 32)
   echo "API_KEY=$API_KEY" >> .env
   echo "ENVIRONMENT=production" >> .env

   # Edite o arquivo .env para adicionar suas chaves de API
   nano .env
   ```

4. **Implantar com Docker Compose**
   ```bash
   # Iniciar os containers
   docker-compose up -d

   # Verificar se está rodando
   docker ps
   docker logs browseruse-api_browser-use-api_1
   ```

5. **Configurar para Alta Disponibilidade (Opcional)**
   ```bash
   # Verificar que o docker inicia no boot
   sudo systemctl enable docker

   # Criar script para reiniciar o serviço
   cat > /home/ubuntu/restart-api.sh << 'EOF'
   #!/bin/bash
   cd /home/ubuntu/browseruse-api
   docker-compose up -d
   EOF

   chmod +x /home/ubuntu/restart-api.sh

   # Adicionar ao crontab
   (crontab -l 2>/dev/null; echo "@reboot /home/ubuntu/restart-api.sh") | crontab -
   ```

6. **Configurar HTTPS com Nginx (Recomendado)**
   ```bash
   # Instalar Nginx
   sudo apt install -y nginx certbot python3-certbot-nginx

   # Configurar Nginx como proxy reverso
   sudo nano /etc/nginx/sites-available/browseruse-api

   # Adicione a configuração:
   server {
       listen 80;
       server_name seu-dominio.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }

   # Ativar o site
   sudo ln -s /etc/nginx/sites-available/browseruse-api /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx

   # Configurar SSL/TLS
   sudo certbot --nginx -d seu-dominio.com
   ```

7. **Ajustes de Performance**
   
   Para melhorar o desempenho em produção, ajuste o docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G  # Aumentar para instâncias maiores
       reservations:
         memory: 2G
   ```

8. **Backup e Manutenção**
   ```bash
   # Criar script de backup
   cat > /home/ubuntu/backup.sh << 'EOF'
   #!/bin/bash
   BACKUP_DIR="/home/ubuntu/backups"
   mkdir -p $BACKUP_DIR
   TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
   tar -czf $BACKUP_DIR/browseruse_backup_$TIMESTAMP.tar.gz -C /home/ubuntu/browseruse-api .env logs
   EOF

   chmod +x /home/ubuntu/backup.sh

   # Programar backup diário
   (crontab -l 2>/dev/null; echo "0 1 * * * /home/ubuntu/backup.sh") | crontab -
   ```

### AWS Lambda (Alternativa)

É possível implantar em Lambda usando containers, mas existem limitações:
- Timeout máximo de 15 minutos
- Limite de RAM (até 10GB)
- Tamanho total do container não pode exceder 10GB

Para implantação em Lambda, considere os seguintes ajustes:
1. Adapte o Dockerfile para reduzir o tamanho da imagem
2. Configure a API para responder via API Gateway
3. Considere usar Lambda Layers para dependências

## Logs e Monitoramento

A API mantém logs detalhados no diretório `logs/api.log`, incluindo:
- Tentativas de acesso com API keys inválidas
- Início e conclusão de tarefas
- Erros durante a execução

Para monitoramento em produção, considere:
- Configurar ELK (Elasticsearch, Logstash, Kibana) para análise de logs
- Implementar métricas usando Prometheus + Grafana
- Configurar alertas para erros frequentes

## Segurança

- Use HTTPS para implantações em produção
- Substitua a API_KEY por um valor forte e exclusivo (min 32 caracteres)
- Mantenha ENVIRONMENT=production em ambientes de produção
- Considere implementar rate limiting e monitoramento # browseruse_tests
