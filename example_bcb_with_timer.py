#!/usr/bin/env python3
"""
Exemplo prático: Como usar o timer dinâmico para sites com carregamento lento.
Este exemplo demonstra o uso específico para sites do BCB e similares.
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_bcb_with_dynamic_timer():
    """
    Demonstra como usar o timer dinâmico para sites governamentais
    que dependem de carregamento JavaScript dinâmico.
    """
    
    api_url = "http://localhost:8000"
    api_key = os.getenv("API_KEY", "123")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Casos de uso reais para sites com carregamento dinâmico
    real_world_cases = [
        {
            "name": "Site do BCB - Timer Estendido",
            "description": "Sites governamentais geralmente precisam de mais tempo para carregar",
            "payload": {
                "url": "https://www.bcb.gov.br/estabilidadefinanceira/normasprudenciais",
                "task": """
                Acesse a página de normas prudenciais do BCB e tente localizar as normas mais recentes.
                Procure por elementos que contenham datas e títulos de normas.
                Se houver uma funcionalidade de busca, tente utilizá-la.
                Retorne as informações em formato JSON com título, data e link das normas encontradas.
                """,
                "model": "deepseek-reasoner",
                "timeout": 180,
                "additional_load_wait_time": 20,  # 20 segundos para sites governamentais pesados
                "debug_mode": True
            }
        },
        {
            "name": "Site da CVM - Timer Médio",
            "description": "Sites de notícias podem ter carregamento assíncrono",
            "payload": {
                "url": "https://www.gov.br/cvm/pt-br/assuntos/noticias",
                "task": """
                Acesse a página de notícias da CVM e liste as 3 notícias mais recentes.
                Aguarde que todas as notícias sejam carregadas completamente.
                Para cada notícia, extraia: título, data de publicação e link.
                Retorne em formato JSON.
                """,
                "model": "deepseek-reasoner",
                "timeout": 120,
                "additional_load_wait_time": 15,  # 15 segundos para carregamento de notícias
                "debug_mode": True
            }
        },
        {
            "name": "Site Simples - Timer Básico",
            "description": "Sites simples precisam de menos tempo de espera",
            "payload": {
                "url": "https://example.com",
                "task": "Capture o título da página e qualquer texto principal visível.",
                "model": "deepseek-reasoner",
                "timeout": 60,
                "additional_load_wait_time": 5,  # 5 segundos para sites simples
                "debug_mode": True
            }
        }
    ]
    
    print("🏛️  Testando Timer Dinâmico - Casos Reais")
    print("🎯 Focado em sites governamentais e carregamento dinâmico")
    print("=" * 80)
    
    for i, case in enumerate(real_world_cases, 1):
        print(f"\n🔬 Caso {i}: {case['name']}")
        print(f"📄 Descrição: {case['description']}")
        print(f"🌐 URL: {case['payload']['url']}")
        print(f"⏱️  Timer: {case['payload']['additional_load_wait_time']} segundos")
        print(f"⏰ Timeout total: {case['payload']['timeout']} segundos")
        
        try:
            print("📤 Enviando requisição...")
            response = requests.post(
                f"{api_url}/run_task",
                headers=headers,
                json=case['payload'],
                timeout=case['payload']['timeout'] + 30  # Timeout HTTP maior que o da task
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Task ID: {result.get('task_id', 'N/A')}")
                print(f"📋 Status: {result.get('status', 'N/A')}")
                
                if result.get('debug_info'):
                    task_details = result['debug_info'].get('task_details', {})
                    timer_used = task_details.get('additional_load_wait_time', 'N/A')
                    print(f"⏱️  Timer aplicado: {timer_used} segundos")
                    
                    execution_time = result['debug_info'].get('execution_time', 'N/A')
                    if execution_time != 'N/A':
                        print(f"⚡ Tempo de execução: {execution_time:.2f} segundos")
                
                if result.get('result'):
                    print("📊 Resultado obtido com sucesso!")
                    if isinstance(result['result'], dict) and len(str(result['result'])) > 100:
                        print("📝 Resultado (preview):", str(result['result'])[:200] + "...")
                    else:
                        print("📝 Resultado:", result['result'])
                elif result.get('error'):
                    print(f"⚠️  Erro na execução: {result.get('error')}")
                
            else:
                try:
                    error_detail = response.json().get('detail', 'Erro desconhecido')
                    print(f"❌ Erro HTTP: {error_detail}")
                except:
                    print(f"❌ Erro HTTP: {response.status_code} - {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout na requisição HTTP")
        except requests.exceptions.ConnectionError:
            print("🔌 Erro de conexão - Verifique se a API está rodando")
            print("💡 Execute './run_api.sh' para iniciar a API")
        except Exception as e:
            print(f"💥 Erro inesperado: {str(e)}")
        
        print("-" * 60)
    
    print("\n📋 Resumo das Configurações Recomendadas:")
    print("┌─────────────────────────────────────┬──────────────────┐")
    print("│ Tipo de Site                        │ Timer Recomendado│")
    print("├─────────────────────────────────────┼──────────────────┤")
    print("│ Sites simples (HTML básico)        │ 5 segundos       │")
    print("│ Sites de notícias                   │ 10-15 segundos   │")
    print("│ Sites governamentais (BCB, CVM)    │ 15-25 segundos   │")
    print("│ SPAs complexos                      │ 20-30 segundos   │")
    print("│ Sites com APIs/AJAX pesado          │ 25-40 segundos   │")
    print("└─────────────────────────────────────┴──────────────────┘")
    
    print("\n💡 Dicas de Uso:")
    print("• Comece com valores baixos e aumente se necessário")
    print("• Monitore os logs de debug para ajustar o timing")
    print("• Sites governamentais geralmente precisam de mais tempo")
    print("• Use timeout HTTP maior que o timer para evitar conflitos")

if __name__ == "__main__":
    print("🚀 Iniciando teste com casos reais...")
    test_bcb_with_dynamic_timer()
    print("\n✅ Teste concluído!") 