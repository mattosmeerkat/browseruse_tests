# Timer Dinâmico para Carregamento - Guia de Uso

## 🚀 Visão Geral

O **Timer Dinâmico de Carregamento** é uma funcionalidade que permite configurar tempo de espera adicional para sites que dependem de JavaScript, AJAX, ou outros recursos que carregam dinamicamente após o carregamento inicial da página.

Esta funcionalidade é especialmente útil para:
- Sites governamentais (BCB, CVM, Receita Federal)
- SPAs (Single Page Applications)
- Sites com carregamento assíncrono de conteúdo
- Páginas com APIs internas que populam dados via JavaScript

## 🔧 Como Usar

### Parâmetro da API

Adicione o campo `additional_load_wait_time` ao corpo da requisição:

```json
{
    "url": "https://example.com",
    "task": "Sua tarefa aqui",
    "additional_load_wait_time": 15,
    "model": "deepseek-reasoner",
    "timeout": 300,
    "debug_mode": true
}
```

### Valores Recomendados

| Tipo de Site | Timer Recomendado | Exemplo |
|--------------|-------------------|---------|
| Sites simples (HTML básico) | 5 segundos | Páginas informativas |
| Sites de notícias | 10-15 segundos | Portais de mídia |
| Sites governamentais | 15-25 segundos | BCB, CVM, Receita |
| SPAs complexos | 20-30 segundos | Apps React/Vue/Angular |
| Sites com APIs pesadas | 25-40 segundos | Dashboards empresariais |

## 📝 Exemplos Práticos

### Exemplo 1: Site do BCB (Carregamento Pesado)

```json
{
    "url": "https://www.bcb.gov.br/estabilidadefinanceira/normasprudenciais",
    "task": "Acesse a página e liste as normas mais recentes disponíveis",
    "additional_load_wait_time": 20,
    "model": "deepseek-reasoner",
    "timeout": 180,
    "debug_mode": true
}
```

### Exemplo 2: Site da CVM (Carregamento Médio)

```json
{
    "url": "https://www.gov.br/cvm/pt-br/assuntos/noticias",
    "task": "Liste as 3 notícias mais recentes com títulos, datas e links",
    "additional_load_wait_time": 15,
    "model": "deepseek-reasoner",
    "timeout": 120,
    "debug_mode": true
}
```

### Exemplo 3: Site Simples (Timer Mínimo)

```json
{
    "url": "https://example.com",
    "task": "Capture o título e conteúdo principal da página",
    "additional_load_wait_time": 5,
    "model": "deepseek-reasoner",
    "timeout": 60,
    "debug_mode": true
}
```

### Exemplo 4: Desabilitar Timer (Valor 0)

```json
{
    "url": "https://static-site.com",
    "task": "Site completamente estático, não precisa de espera",
    "additional_load_wait_time": 0,
    "model": "deepseek-reasoner",
    "timeout": 60,
    "debug_mode": true
}
```

## ⚙️ Como Funciona Internamente

1. **Valor Padrão**: Se `additional_load_wait_time` não for especificado, usa 5 segundos por padrão
2. **Instruções Técnicas**: Quando um valor > 0 é especificado, instruções técnicas são automaticamente adicionadas ao prompt
3. **Prompt Enhancement**: O agente recebe instruções específicas sobre como aguardar o carregamento dinâmico
4. **Logging**: Todas as configurações de timing são registradas nos logs de debug

### Instruções Técnicas Automáticas

Quando um timer é configurado, estas instruções são automaticamente adicionadas ao prompt:

```
INSTRUÇÕES TÉCNICAS PARA CARREGAMENTO DINÂMICO:
1. Após carregar a página inicial, aguarde X segundos para que todo conteúdo dinâmico seja carregado
2. Aguarde elementos aparecerem completamente antes de tentar interagir com eles
3. Se necessário, aguarde que requisições AJAX/Fetch sejam concluídas
4. Para sites com carregamento assíncrono, certifique-se de que todos os elementos estejam visíveis
5. Use wait_for_selector ou wait_for_load_state quando apropriado
6. Considere que o conteúdo pode ser populado via JavaScript após o carregamento inicial
```

## 🧪 Scripts de Teste

### Teste Básico de Funcionalidade

```bash
python3 test_dynamic_timer.py
```

### Teste com Casos Reais (BCB, CVM)

```bash
python3 example_bcb_with_timer.py
```

## 📊 Monitoramento e Debug

### Verificando se o Timer foi Aplicado

Com `debug_mode: true`, você pode verificar nos logs:

```json
{
    "debug_info": {
        "task_details": {
            "url": "https://example.com",
            "additional_load_wait_time": 15
        },
        "logs": [
            {
                "message": "Adicionando instruções técnicas para espera de 15 segundos"
            }
        ]
    }
}
```

### Logs de Diagnóstico

O sistema registra automaticamente:
- Tempo de espera configurado
- Se instruções técnicas foram adicionadas
- Tempo total de execução
- Preview do prompt construído

## 🎯 Casos de Uso Específicos

### Sites Governamentais Brasileiros

Sites como BCB, CVM, Receita Federal frequentemente usam:
- Frameworks pesados (Angular, React)
- APIs internas para carregar dados
- Sistemas de autenticação complexos
- Múltiplas camadas de carregamento

**Configuração recomendada**: 15-25 segundos

### SPAs Modernas

Aplicações Single Page:
- Carregamento inicial mínimo
- Conteúdo populado via JavaScript
- Roteamento client-side
- Lazy loading de componentes

**Configuração recomendada**: 20-30 segundos

### Sites de E-commerce

Plataformas de vendas online:
- Carregamento de produtos via API
- Sistemas de filtros dinâmicos
- Carrinho de compras assíncrono
- Sistemas de recomendação

**Configuração recomendada**: 10-20 segundos

## 🚨 Troubleshooting

### Problema: Resultado vazio mesmo com timer

**Possíveis causas:**
- Timer insuficiente para o site específico
- Site usa autenticação ou captcha
- Conteúdo carregado via API protegida

**Soluções:**
1. Aumentar o timer gradualmente (5 → 10 → 15 → 20)
2. Verificar se o site requer interação específica
3. Usar o endpoint `/diagnose_browser` para análise

### Problema: Timeout na requisição

**Possíveis causas:**
- Timer muito alto em relação ao timeout total
- Site muito lento ou indisponível

**Soluções:**
1. Balancear `additional_load_wait_time` e `timeout`
2. Regra: `timeout` deve ser pelo menos 3x maior que o timer
3. Verificar conectividade com o site

### Problema: Instruções técnicas não aparecem

**Verificações:**
1. Confirmar que `additional_load_wait_time > 0`
2. Ativar `debug_mode: true`
3. Verificar logs de diagnóstico

## 📈 Otimização de Performance

### Estratégia Escalonada

1. **Início**: Comece com 5 segundos
2. **Teste**: Se resultado vazio, aumente para 10
3. **Ajuste**: Continue aumentando de 5 em 5 segundos
4. **Limite**: Raramente necessário > 30 segundos

### Balanceamento Timeout vs Timer

```
Timer de 10s → Timeout mínimo de 60s
Timer de 20s → Timeout mínimo de 120s
Timer de 30s → Timeout mínimo de 180s
```

## 💡 Dicas Avançadas

1. **Sites Governamentais**: Sempre usar 15+ segundos
2. **Horário de Pico**: Aumentar timer em 50% durante horários de maior tráfego
3. **Monitoramento**: Usar `debug_mode` para otimizar timers
4. **Testes A/B**: Testar diferentes valores para o mesmo site
5. **Cache**: Sites com cache agressivo podem precisar de menos tempo

## 🔗 Recursos Relacionados

- [API Documentation](./README.md)
- [Diagnostic Tools](./browser_diagnosis.py)
- [Test Scripts](./test_dynamic_timer.py)
- [Real World Examples](./example_bcb_with_timer.py) 