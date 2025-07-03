#!/usr/bin/env python3
"""
Script de teste para verificar carregamento de variáveis de ambiente e modelos.
"""
import os
import sys
from dotenv import load_dotenv

def test_environment_loading():
    """Testa o carregamento das variáveis de ambiente"""
    print("🔧 Testando carregamento de variáveis de ambiente...")
    
    # Carregar como na API
    load_dotenv(override=True)
    
    # Verificar chaves
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"✅ DEEPSEEK_API_KEY: {'✓ SET' if deepseek_key else '❌ NOT SET'}")
    if deepseek_key:
        print(f"   Preview: {deepseek_key[:10]}...{deepseek_key[-4:]}")
    
    print(f"✅ OPENAI_API_KEY: {'✓ SET' if openai_key else '❌ NOT SET'}")
    if openai_key:
        print(f"   Preview: {openai_key[:10]}...{openai_key[-4:]}")
    
    return deepseek_key, openai_key

def test_model_initialization():
    """Testa a inicialização dos modelos"""
    print("\n🤖 Testando inicialização de modelos...")
    
    try:
        # Importar função da API
        sys.path.append('.')
        from api import get_llm_instance
        
        # Testar modelos DeepSeek
        print("\n📊 Testando DeepSeek Chat...")
        try:
            llm_deepseek_chat = get_llm_instance("deepseek-chat")
            print("✅ deepseek-chat: OK")
        except Exception as e:
            print(f"❌ deepseek-chat: {str(e)}")
        
        print("\n🧠 Testando DeepSeek Reasoner...")
        try:
            llm_deepseek_reasoner = get_llm_instance("deepseek-reasoner")
            print("✅ deepseek-reasoner: OK")
        except Exception as e:
            print(f"❌ deepseek-reasoner: {str(e)}")
        
        # Testar modelo OpenAI
        print("\n🔥 Testando OpenAI GPT-4o...")
        try:
            llm_gpt4o = get_llm_instance("gpt-4o")
            print("✅ gpt-4o: OK")
        except Exception as e:
            print(f"❌ gpt-4o: {str(e)}")
            
    except Exception as e:
        print(f"❌ Erro ao importar função get_llm_instance: {str(e)}")

def test_api_direct():
    """Testa a API diretamente"""
    print("\n🌐 Testando API diretamente...")
    
    try:
        import requests
        
        # Teste com deepseek-chat
        payload = {
            "url": "https://httpbin.org/json",
            "task": "Acesse a página e me diga qual é o conteúdo JSON retornado",
            "model": "deepseek-chat",
            "timeout": 60,
            "additional_load_wait_time": 5,
            "debug_mode": True
        }
        
        print("📤 Enviando requisição de teste para API...")
        response = requests.post(
            "http://localhost:8000/run_task",
            headers={
                "Authorization": "Bearer 123",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=90
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Task Status: {result.get('status', 'unknown')}")
            
            if result.get('debug_info'):
                debug = result['debug_info']
                task_details = debug.get('task_details', {})
                print(f"🤖 Modelo usado: {task_details.get('model', 'N/A')}")
                timer_value = task_details.get('additional_load_wait_time')
                print(f"⏱️ Timer (task_details): {timer_value if timer_value is not None else 'N/A (não presente nos detalhes)'}s")
                print(f"⚡ Tempo execução: {debug.get('execution_time', 'N/A')}s")
        else:
            error = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Erro: {error}")
            
    except requests.exceptions.ConnectionError:
        print("❌ API não está rodando. Execute: python api.py")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

def main():
    """Função principal"""
    print("🧪 TESTE COMPLETO - Variáveis de Ambiente e Modelos")
    print("=" * 60)
    
    # Teste 1: Variáveis de ambiente
    deepseek_key, openai_key = test_environment_loading()
    
    # Teste 2: Inicialização de modelos
    if deepseek_key or openai_key:
        test_model_initialization()
    else:
        print("⚠️ Pulando teste de modelos - chaves não encontradas")
    
    # Teste 3: API direta
    test_api_direct()
    
    print("\n📋 Resumo:")
    print("- Se os modelos falharam, verifique as chaves de API")
    print("- Se a API falhou, certifique-se que está rodando (python api.py)")
    print("- DeepSeek usa: deepseek-chat e deepseek-reasoner")
    print("- OpenAI usa: gpt-4o, gpt-4, etc.")

if __name__ == "__main__":
    main() 