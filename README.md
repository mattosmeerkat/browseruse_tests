# Browser Use API

API para execução de tarefas automatizadas de navegação web usando LLMs e browser automation.

## Atualizações Recentes (Junho 2024)

* **Suporte ao Headless Browser**: Adicionado suporte ao xvfb para execução do browser em ambiente sem interface gráfica
* **Melhorias no Dockerfile**: Configuração otimizada para garantir que o Chromium funcione corretamente em containers
* **Correção de caminhos**: Ajustado o Dockerfile e script de execução para lidar corretamente com a estrutura do módulo
* **Melhorias no tratamento de resultados**: Adicionado manejo seguro de diferentes tipos de retorno do agente
* **Atualização do Watchtower**: Atualizado para versão >=3.0.0 para compatibilidade com parâmetros de configuração
* **Instalação otimizada de Playwright**: Configuração do Dockerfile para uso eficiente do Playwright/Chromium
* **Segurança aprimorada**: Remoção de chaves API expostas das configurações de exemplo
* **Implementação da dependência browser-use**: Compatibilidade com versões atuais do browser-use e suas dependências

## Nota sobre o pacote browser-use

Este projeto depende do pacote `browser-use`, que é uma biblioteca para automação de navegadores com LLMs. O pacote é instalado automaticamente através do `requirements.txt`.

O Docker utiliza xvfb para permitir que o Chromium seja executado em ambientes sem interface gráfica, como servidores na AWS.

Para um ambiente de produção completo, você deve:

1. **Em desenvolvimento local**: 
   - Clone o repositório do `browser-use` (se disponível publicamente)
   - Instale-o em modo de desenvolvimento: `pip install -e /path/to/browser-use`
   - Ou solicite acesso à equipe responsável

2. **Em Docker (produção)**: 
   - O Dockerfile inclui uma implementação simulada para fins de demonstração
   - Para produção, você deve substituir a implementação simulada pela biblioteca real, modificando o Dockerfile:
     ```dockerfile
     # Remova as linhas de simulação e adicione a instalação correta
     RUN pip install git+https://github.com/sua-org/browser-use.git
     # OU: instale a partir de um servidor PyPI privado
     # OU: adicione o código fonte como um submódulo git
     ```

3. **Funcionalidades esperadas do pacote**: A implementação deve fornecer:
   - Classe `Agent` com método `__init__(task, llm)` 
   - Método assíncrono `run()`
   - Método `final_result()` que retorna o resultado formatado

## Requisitos

- Python 3.11+
- Docker e Docker Compose (para implantação em contêiner)
- Em caso de execução local: Chromium ou Google Chrome instalado

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
# Dentro do diretório browseruse_tests
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# OU na raiz do projeto
uvicorn browseruse_tests.api:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em `http://localhost:8000`. Você pode acessar a documentação interativa em `http://localhost:8000/docs`.

## Guia de Deploy Rápido (Mínimo Funcional)

Este guia oferece uma implantação mínima funcional, adequada para testes ou ambientes simples:

1. **Preparação do ambiente:**
   ```bash
   # Clonar o repositório 
   git clone [seu-repositorio] browser-use-api
   cd browser-use-api
   
   # Configurar variáveis de ambiente
   cp example.env .env
   # Edite o arquivo .env para definir:
   # - OPENAI_API_KEY=sua-chave-openai
   # - API_KEY=sua-api-key-segura
   # - ENVIRONMENT=production
   ```

2. **Implantação com Docker:**
   ```bash
   # Construir a imagem
   docker compose build

   # Iniciar o serviço
   docker compose up -d

   # Verificar logs
   docker compose logs -f
   ```

3. **Verificar a instalação:**
   ```bash
   # Verificar a saúde da API
   curl http://localhost:8000/health
   # Deve retornar: {"status":"ok","environment":"production"}
   ```

4. **Exemplo de uso:**
   ```bash
   # Executar uma tarefa simples (substitua API_KEY pelo valor do seu .env)
   curl -X POST http://localhost:8000/run_task \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sua-api-key" \
     -d '{"url": "https://www.gov.br/cvm/pt-br/pagina-inicial/", "task": "Extraia o título da página principal", "model": "gpt-4.1"}'
   ```

Se você encontrar problemas com a execução do browser, verifique os logs do container para mais informações:

```bash
docker compose logs -f
```

## Implantação com Docker

Para implantar usando Docker:

```bash
# Construir a imagem
docker compose build

# Iniciar o serviço
docker compose up -d

# Verificar logs
docker compose logs -f
```

O Dockerfile já está configurado com todas as dependências necessárias, incluindo:
- Python 3.11 (recomendado para browser-use)
- Playwright com Chromium
- xvfb para execução headless do navegador
- Todas as bibliotecas do sistema necessárias

### Verificando se a instalação está funcionando

Após iniciar o container, você pode verificar se a API está funcionando corretamente:

```bash
# Verificar a saúde da API
curl http://localhost:8000/health

# Executar uma tarefa simples (substitua API_KEY pelo valor do seu .env)
curl -X POST http://localhost:8000/run_task \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sua-api-key" \
  -d '{"url": "https://www.gov.br/cvm/pt-br/pagina-inicial/", "task": "Extraia o título da página principal", "model": "gpt-4.1"}'
```

Se você encontrar problemas com a execução do browser, verifique os logs do container para mais informações:

```bash
docker compose logs -f
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
  -H "Authorization: Bearer sua-api-key-segura" \
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
   git clone https://github.com/mattosmeerkat/browseruse_tests.git browseruse_api
   cd browseruse_api

   # Configurar o arquivo .env
   # Crie o arquivo .env com as configurações básicas
    cat > .env << 'EOF'
    # API Keys
    OPENAI_API_KEY=sua_chave_openai_aqui
    API_KEY=chave_segura_para_autenticacao_da_api

    # Configurações de ambiente
    ENVIRONMENT=production

    # Configurações de fuso horário
    TZ=America/Sao_Paulo

    # Configurações de CloudWatch (opcional)
    # AWS_ACCESS_KEY_ID=sua_chave_aws
    # AWS_SECRET_ACCESS_KEY=sua_chave_secreta_aws
    # AWS_DEFAULT_REGION=sa-east-1
    # LOG_GROUP_NAME=BrowserUseAPILogs
    EOF

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

A API mantém logs detalhados no diretório `logs/api.log` e `logs/browser_use_debug.log`. 
Em um ambiente de produção na AWS, os logs são automaticamente enviados para o Amazon CloudWatch se as seguintes variáveis de ambiente estiverem configuradas no seu arquivo `.env` (ou nas configurações de ambiente da sua instância EC2/ECS Task Definition):

- `ENVIRONMENT=production`
- `LOG_GROUP_NAME`: Nome do grupo de logs no CloudWatch (ex: `BrowserUseAPILogs`)
- `LOG_STREAM_NAME_API`: Nome do stream para logs principais da API (ex: `api-service-logs`)
- `LOG_STREAM_NAME_DIAG`: Nome do stream para logs de diagnóstico do browser (ex: `browser-diag-logs`)

**Permissões IAM:**
A instância EC2 ou o Role da Task do ECS onde a API está rodando precisará das seguintes permissões IAM para enviar logs ao CloudWatch:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CloudWatchLogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

### Configuração de Alertas para Falhas (AWS CloudWatch Alarms)

É altamente recomendável configurar alarmes no CloudWatch para monitorar a saúde da sua aplicação e ser notificado sobre falhas. Exemplos de métricas para monitorar:

1.  **Erros de Aplicação**: Crie filtros de métrica nos seus Log Groups do CloudWatch para contar ocorrências de erros (ex: palavras-chave como "ERROR", "Traceback", "Timeout"). Configure alarmes quando essa contagem exceder um limite aceitável.
2.  **Uso de CPU e Memória da Instância EC2/ECS Task**: Configure alarmes para `CPUUtilization` e `MemoryUtilization` para detectar sobrecarga.
3.  **Status do Health Check do Load Balancer**: Se estiver usando um Application Load Balancer (ALB), monitore a métrica `HealthyHostCount` e `UnHealthyHostCount`.
4.  **Latência da API**: Monitore a latência das suas requisições através do ALB ou métricas customizadas.

Consulte a [documentação da AWS sobre CloudWatch Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html) para criar e configurar alarmes.

### Escalabilidade Horizontal (AWS)

Para garantir que sua API possa lidar com variações de carga e manter alta disponibilidade, considere as seguintes estratégias de escalabilidade horizontal na AWS:

1.  **Application Load Balancer (ALB)**: Distribua o tráfego de entrada entre múltiplas instâncias da sua API rodando em diferentes Zonas de Disponibilidade.
2.  **Auto Scaling Group (ASG)**: Configure um ASG para suas instâncias EC2. O ASG pode automaticamente aumentar ou diminuir o número de instâncias com base em métricas como utilização de CPU, número de requisições, ou schedules definidos.
3.  **Amazon ECS com Auto Scaling**: Se estiver usando ECS, configure o Service Auto Scaling para ajustar o número de tasks rodando com base em métricas como CPU e memória, ou métricas customizadas.

O `docker-compose.yml` fornecido é adequado para um único host ou como base para uma definição de task no ECS. Para escalabilidade real, você precisará integrar com os serviços mencionados acima.

## Segurança

- Use HTTPS para implantações em produção
- Substitua a API_KEY por um valor forte e exclusivo (min 32 caracteres)
- Mantenha ENVIRONMENT=production em ambientes de produção
- Considere implementar rate limiting e monitoramento

**Variáveis de Ambiente Críticas para Produção:**

Certifique-se de que as seguintes variáveis estejam corretamente configuradas no seu arquivo `.env` (ou no sistema de gerenciamento de segredos da AWS) para o ambiente de produção:

- `ENVIRONMENT=production`: Essencial para desabilitar chaves de teste e ativar comportamentos de produção (como logging para CloudWatch).
- `API_KEY`: Uma chave de API forte e única. Gere usando `openssl rand -base64 32`.
- `OPENAI_API_KEY`: Sua chave da API da OpenAI.
- `LOG_GROUP_NAME`: (Opcional, mas recomendado para CloudWatch) Ex: `YourAppProductionLogs`.

**Dependências e Playwright:**

- **Versões de Dependências**: É uma boa prática fixar (pin) as versões das suas dependências no `requirements.txt` para garantir builds consistentes. A dependência `browser-use` e `playwright` devem ser testadas no ambiente de produção.
- **Playwright no EC2**: O `Dockerfile` já inclui a instalação do Chromium e suas dependências, o que é adequado para execução em instâncias EC2. Certifique-se que a instância tem recursos suficientes (CPU/memória) conforme especificado no `docker-compose.yml` (mínimo 1G reservado, limite 2G, mas pode precisar de mais sob carga).
