#!/usr/bin/env python3
"""
Script de teste para verificar o timer dinâmico de carregamento da API.
Demonstra como usar o campo additional_load_wait_time para sites com carregamento dinâmico.
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_dynamic_timer():
    """Testa o timer dinâmico com diferentes valores"""
    
    api_url = "http://localhost:8000"
    api_key = os.getenv("API_KEY", "123")  # Usar chave de desenvolvimento
    
    # Headers para autenticação
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Testes com diferentes tempos de espera
    test_cases = [
        {
            "name": "Timer Padrão (5 segundos)",
            "payload": {
                "url": "https://example.com",
                "task": "Acesse a página e capture o título",
                "model": "deepseek-reasoner",
                "timeout": 60,
                "debug_mode": True
                # additional_load_wait_time não especificado, usará o padrão (5)
            }
        },
        {
            "name": "Timer Customizado (10 segundos)",
            "payload": {
                "url": "https://example.com",
                "task": "Acesse a página e capture o título",
                "model": "deepseek-reasoner",
                "timeout": 60,
                "debug_mode": True,
                "additional_load_wait_time": 10
            }
        },
        {
            "name": "Timer Estendido (20 segundos - para sites pesados)",
            "payload": {
                "url": "https://example.com",
                "task": "Acesse a página e capture o título",
                "model": "deepseek-reasoner",
                "timeout": 60,
                "debug_mode": True,
                "additional_load_wait_time": 20
            }
        },
        {
            "name": "Sem Timer (0 segundos)",
            "payload": {
                "url": "https://example.com",
                "task": "Acesse a página e capture o título",
                "model": "deepseek-reasoner",
                "timeout": 60,
                "debug_mode": True,
                "additional_load_wait_time": 0
            }
        }
    ]
    
    print("🧪 Testando Timer Dinâmico para Carregamento")
    print(f"📡 API URL: {api_url}")
    print(f"🔑 API Key: {api_key[:10]}...")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 Teste {i}: {test_case['name']}")
        timer_value = test_case['payload'].get('additional_load_wait_time', 'padrão (5)')
        print(f"⏱️  Timer de carregamento: {timer_value} segundos")
        
        try:
            print("📤 Enviando requisição...")
            response = requests.post(
                f"{api_url}/run_task",
                headers=headers,
                json=test_case['payload'],
                timeout=120
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Sucesso! Task ID: {result.get('task_id', 'N/A')}")
                print(f"📋 Status: {result.get('status', 'N/A')}")
                
                if result.get('debug_info'):
                    task_details = result['debug_info'].get('task_details', {})
                    actual_timer = task_details.get('additional_load_wait_time', 'N/A')
                    print(f"⏱️  Timer configurado: {actual_timer} segundos")
                    
                    # Mostrar preview do prompt construído se disponível
                    logs = result['debug_info'].get('logs', [])
                    for log in logs:
                        if 'Construindo o prompt' in log.get('message', ''):
                            prompt_preview = log.get('extra_data', {}).get('full_task', '')
                            if 'INSTRUÇÕES TÉCNICAS' in prompt_preview:
                                print("🔧 Instruções técnicas adicionadas ao prompt")
                            else:
                                print("📝 Prompt básico (sem instruções técnicas)")
                            break
                    
            else:
                error_detail = response.json().get('detail', 'Erro desconhecido')
                print(f"❌ Erro: {error_detail}")
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout na requisição")
        except requests.exceptions.ConnectionError:
            print("🔌 Erro de conexão - Verifique se a API está rodando")
        except Exception as e:
            print(f"💥 Erro inesperado: {str(e)}")
        
        print("-" * 50)
    
    print("\n📋 Resumo dos testes:")
    print("• Timer padrão: 5 segundos (quando não especificado)")
    print("• Timer customizado: Aceita qualquer valor em segundos")
    print("• Timer 0: Desabilita instruções técnicas de espera")
    print("• Instruções técnicas são adicionadas automaticamente ao prompt")
    
    print("\n💡 Uso recomendado:")
    print("• Sites simples: 5-10 segundos")
    print("• Sites com JavaScript pesado: 15-20 segundos")
    print("• SPAs com carregamento lento: 20-30 segundos")
    print("• Sites do governo (BCB, CVM): 15-25 segundos")

if __name__ == "__main__":
    print("🚀 Iniciando testes do Timer Dinâmico...")
    test_dynamic_timer()
    print("\n✅ Testes concluídos!") 