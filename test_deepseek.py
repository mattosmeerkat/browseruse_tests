#!/usr/bin/env python3
"""
Script de teste para verificar se a API suporta DeepSeek corretamente.
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_deepseek_api():
    """Testa a API com diferentes modelos DeepSeek"""
    
    api_url = "http://localhost:8000"
    api_key = os.getenv("API_KEY", "123")  # Usar chave de desenvolvimento
    
    # Headers para autenticação
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Testes com diferentes modelos
    test_cases = [
        {
            "name": "DeepSeek Reasoner",
            "payload": {
                "url": "https://example.com",
                "task": "Acesse o site e me diga qual é o título da página",
                "model": "deepseek-reasoner",
                "timeout": 60,
                "debug_mode": True
            }
        },
        {
            "name": "DeepSeek Chat",
            "payload": {
                "url": "https://example.com", 
                "task": "Acesse o site e me diga qual é o título da página",
                "model": "deepseek-chat",
                "timeout": 60,
                "debug_mode": True
            }
        },
        {
            "name": "OpenAI GPT-4 (fallback)",
            "payload": {
                "url": "https://example.com",
                "task": "Acesse o site e me diga qual é o título da página", 
                "model": "gpt-4",
                "timeout": 60,
                "debug_mode": True
            }
        }
    ]
    
    print("🧪 Testando API com diferentes modelos...")
    print(f"📡 API URL: {api_url}")
    print(f"🔑 API Key: {api_key[:10]}...")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n🔬 Testando: {test_case['name']}")
        print(f"📝 Modelo: {test_case['payload']['model']}")
        
        try:
            response = requests.post(
                f"{api_url}/run_task",
                headers=headers,
                json=test_case['payload'],
                timeout=120  # Timeout maior para o request HTTP
            )
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Sucesso! Task ID: {result.get('task_id', 'N/A')}")
                print(f"📋 Status: {result.get('status', 'N/A')}")
                
                if result.get('debug_info'):
                    task_details = result['debug_info'].get('task_details', {})
                    print(f"⚙️  Modelo usado: {task_details.get('model', 'N/A')}")
                    
            else:
                error_detail = response.json().get('detail', 'Erro desconhecido')
                print(f"❌ Erro: {error_detail}")
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout na requisição")
        except requests.exceptions.ConnectionError:
            print("🔌 Erro de conexão - Verifique se a API está rodando")
        except Exception as e:
            print(f"💥 Erro inesperado: {str(e)}")
        
        print("-" * 40)

def test_health_endpoint():
    """Testa o endpoint de health da API"""
    api_url = "http://localhost:8000"
    
    print("\n🏥 Testando endpoint de health...")
    
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API está rodando!")
            print(f"🌍 Environment: {health_data.get('environment', 'N/A')}")
        else:
            print(f"⚠️  API retornou status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ API não está acessível em http://localhost:8000")
        print("💡 Verifique se a API está rodando com: python api.py ou docker-compose up")
    except Exception as e:
        print(f"💥 Erro: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando testes da API com DeepSeek")
    print("=" * 60)
    
    # Verificar variáveis de ambiente
    print("\n🔍 Verificando variáveis de ambiente...")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    api_key = os.getenv("API_KEY")
    
    print(f"🔑 DEEPSEEK_API_KEY: {'✅ Configurada' if deepseek_key else '❌ Não encontrada'}")
    print(f"🔑 OPENAI_API_KEY: {'✅ Configurada' if openai_key else '❌ Não encontrada'}")
    print(f"🔑 API_KEY: {'✅ Configurada' if api_key else '❌ Não encontrada (usando padrão)'}")
    
    if not deepseek_key:
        print("\n⚠️  AVISO: DEEPSEEK_API_KEY não configurada!")
        print("💡 Adicione no seu arquivo .env: DEEPSEEK_API_KEY=sua_chave_aqui")
    
    print("\n" + "=" * 60)
    
    # Testar health primeiro
    test_health_endpoint()
    
    # Testar endpoints principais
    test_deepseek_api()
    
    print("\n🏁 Testes concluídos!") 