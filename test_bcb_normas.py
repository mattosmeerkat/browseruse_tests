#!/usr/bin/env python3
"""
Teste específico para busca de normas do BCB.
Testa tanto DeepSeek quanto GPT com timer dinâmico otimizado.
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_bcb_normas():
    """Testa a busca de normas do BCB com diferentes modelos"""
    
    api_url = "http://localhost:8000"
    api_key = os.getenv("API_KEY", "123")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Payload base da requisição - REFINADO PARA JSON ESTRITO
    base_task = """IMPORTANTE: Sua resposta DEVE SER APENAS um JSON válido, sem nenhum texto adicional, explicações ou markdown. 
Acesse o site: https://www.bcb.gov.br/estabilidadefinanceira/buscanormas?dataInicioBusca=21%2F05%2F2025&dataFimBusca=21%2F05%2F2025&tipoDocumento=Todos. 
No site, localize todas as normas publicadas no período informado. Para cada norma encontrada, extraia as seguintes informações: 
1. Título completo da norma. 
2. Data e hora da publicação (separar também o dia da semana). 
3. Nome do regulador (usar sempre "Banco Central do Brasil" ou "BCB" se aplicável). 
4. Assunto ou ementa da norma. 
5. Conteúdo completo da norma (incluindo corpo, artigos e parágrafos). 
6. URL direta para a página da norma. 

Formate a resposta ESTRITAMENTE no seguinte modelo JSON (array de objetos). Não inclua comentários ou texto explicativo no JSON: 
[{ 
    "revisado_por": "", 
    "data_publicacao": "2025-05-21", 
    "dia_semana": "quarta-feira", 
    "hora_publicacao": "", 
    "regulador": "BCB", 
    "titulo": "", 
    "ementa": "", 
    "conteudo_completo": "", 
    "link": "" 
}]. 

Se algum dado não estiver disponível na página, preencha com string vazia "", mas mantenha a chave no JSON. 
Se nenhuma norma for encontrada, retorne um array JSON vazio: []. 
NÃO adicione nenhuma palavra antes ou depois do JSON resultante."""
    
    # Configurações de teste para diferentes modelos
    test_configs = [
        {
            "name": "🤖 DeepSeek Chat (V3)",
            "payload": {
                "url": "https://www.bcb.gov.br/estabilidadefinanceira/buscanormas?dataInicioBusca=21%2F05%2F2025&dataFimBusca=21%2F05%2F2025&tipoDocumento=Todos",
                "task": base_task,
                "model": "deepseek-chat",  # CORRIGIDO: nome correto do modelo
                "timeout": 600,
                "additional_load_wait_time": 25,  # Timer aumentado para site governamental
                "debug_mode": True
            }
        },
        {
            "name": "🧠 DeepSeek Reasoner (R1)",
            "payload": {
                "url": "https://www.bcb.gov.br/estabilidadefinanceira/buscanormas?dataInicioBusca=21%2F05%2F2025&dataFimBusca=21%2F05%2F2025&tipoDocumento=Todos",
                "task": base_task,
                "model": "deepseek-reasoner",  # CORRIGIDO: nome correto do modelo
                "timeout": 600,
                "additional_load_wait_time": 25,
                "debug_mode": True
            }
        },
        {
            "name": "🔥 OpenAI GPT-4o",
            "payload": {
                "url": "https://www.bcb.gov.br/estabilidadefinanceira/buscanormas?dataInicioBusca=21%2F05%2F2025&dataFimBusca=21%2F05%2F2025&tipoDocumento=Todos",
                "task": base_task,
                "model": "gpt-4o",
                "timeout": 600,
                "additional_load_wait_time": 25,
                "debug_mode": True
            }
        }
    ]
    
    print("🚀 Iniciando testes de busca de normas do BCB")
    print("=" * 80)
    
    # Executar testes com diferentes modelos
    for config in test_configs:
        print(f"\n📊 Testando: {config['name']}")
        print(f"⏱️ Timer de carregamento: {config['payload']['additional_load_wait_time']}s")
        print(f"⏰ Timeout: {config['payload']['timeout']}s")
        print(f"🤖 Modelo: {config['payload']['model']}")
        print("-" * 60)
        
        try:
            # Fazer a requisição
            response = requests.post(
                f"{api_url}/run_task",
                headers=headers,
                json=config["payload"],
                timeout=700  # Timeout da requisição HTTP maior que o timeout da tarefa
            )
            
            print(f"📡 Status HTTP: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status da tarefa: {result.get('status', 'unknown')}")
                
                # Verificar se há resultado
                if result.get('result'):
                    if isinstance(result['result'], list):
                        print(f"📋 Normas encontradas: {len(result['result'])}")
                        for i, norma in enumerate(result['result'][:2], 1):  # Mostrar apenas as primeiras 2
                            print(f"  {i}. {norma.get('titulo', 'Título não encontrado')[:100]}...")
                    else:
                        print(f"📝 Resultado: {str(result['result'])[:200]}...")
                
                # Debug info se disponível
                if result.get('debug_info'):
                    debug = result['debug_info']
                    if 'execution_time' in debug:
                        print(f"⏱️ Tempo de execução: {debug['execution_time']:.2f}s")
                    
                    task_details = debug.get('task_details', {})
                    timer_usado = task_details.get('additional_load_wait_time', 'N/A')
                    print(f"⏳ Timer dinâmico usado: {timer_usado}s")
                
                # Mostrar se houve erro
                if result.get('error'):
                    print(f"❌ Erro: {result['error']}")
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Detalhes: {error_detail}")
                except:
                    print(f"   Resposta: {response.text[:200]}...")
                    
        except requests.exceptions.Timeout:
            print("⏰ Timeout na requisição HTTP (>700s)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {str(e)}")
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
        
        print("-" * 60)
    
    print("\n🏁 Teste concluído!")
    print("\n💡 Dicas:")
    print("- Se algum modelo falhou, verifique se as chaves de API estão configuradas")
    print("- O timer dinâmico de 25s é otimizado para sites governamentais lentos")
    print("- DeepSeek Chat (V3) é ótimo para estruturação de dados")
    print("- DeepSeek Reasoner (R1) é melhor para análise complexa")
    print("- GPT-4o oferece boa qualidade geral")

if __name__ == "__main__":
    test_bcb_normas() 