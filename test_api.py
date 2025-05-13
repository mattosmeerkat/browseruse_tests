#!/usr/bin/env python3
"""
Script simples para testar a API localmente.
Executa uma tarefa básica e mostra o resultado.
"""

import requests
import json
import os
from dotenv import load_dotenv
import time

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
API_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "123")
TEST_URL = "https://www.gov.br/cvm/pt-br/pagina-inicial/"
TEST_TASK = "Extraia o título da página principal e retorne em formato JSON."

def test_api():
    print(f"Testando a API em {API_URL}...")
    print(f"URL de teste: {TEST_URL}")
    print(f"Tarefa: {TEST_TASK}")
    print(f"Usando API Key: {API_KEY}")
    
    # Verificar se a API está rodando
    try:
        health = requests.get(f"{API_URL}/health")
        if health.status_code != 200:
            print(f"Erro: API não está respondendo corretamente (status: {health.status_code})")
            return False
        print("API está online!")
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar à API. Certifique-se de que ela está rodando.")
        print("Execute './run_api.sh' primeiro para iniciar a API.")
        return False
    
    # Preparar o payload
    payload = {
        "url": TEST_URL,
        "task": TEST_TASK,
        "model": "gpt-4.1",
        "timeout": 300
    }
    
    # Configurar os headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Fazer a chamada à API
    print("\nEnviando requisição para a API...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_URL}/run_task",
            json=payload,
            headers=headers
        )
        
        # Verificar se a requisição foi bem-sucedida
        response.raise_for_status()
        
        # Exibir o tempo de execução
        execution_time = time.time() - start_time
        print(f"Requisição concluída em {execution_time:.2f} segundos")
        
        # Exibir o resultado
        result = response.json()
        print("\nResultado:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Verificar se houve erro
        if result.get("error"):
            print(f"\nAtenção: A tarefa retornou um erro: {result['error']}")
        else:
            print("\nTeste concluído com sucesso!")
        
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"\nErro na requisição: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Resposta: {e.response.text}")
        return False

if __name__ == "__main__":
    test_api() 