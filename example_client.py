import requests
import json
import os
from dotenv import load_dotenv
import argparse

# Carregar variáveis de ambiente
load_dotenv()

def run_browser_task(url, task_description, api_url="http://localhost:8000", api_key=None):
    """
    Cliente de exemplo para a Browser Use API
    
    Args:
        url (str): URL a ser acessada pelo browser
        task_description (str): Descrição detalhada da tarefa a ser executada
        api_url (str): URL da API
        api_key (str): Chave de API para autenticação
    
    Returns:
        dict: Resultado da tarefa
    """
    if not api_key:
        api_key = os.getenv("API_KEY", "default-key")
    
    # Preparar o payload
    payload = {
        "url": url,
        "task": task_description,
        "model": "deepseek-reasoner",  # Usando o modelo DeepSeek por padrão
        "timeout": 300,
        "debug_mode": True
    }
    
    # Configurar os headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Fazer a chamada à API
    try:
        response = requests.post(
            f"{api_url}/run_task",
            json=payload,
            headers=headers
        )
        
        # Verificar se a requisição foi bem-sucedida
        response.raise_for_status()
        
        # Retornar o resultado
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Resposta: {e.response.text}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Configurar o parser de argumentos
    parser = argparse.ArgumentParser(description="Cliente para a Browser Use API")
    parser.add_argument("--url", required=True, help="URL a ser acessada")
    parser.add_argument("--task", required=True, help="Descrição da tarefa")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL da API")
    parser.add_argument("--api-key", help="Chave de API (opcional se definida em .env)")
    parser.add_argument("--output", help="Arquivo para salvar a saída (opcional)")
    
    # Parsear os argumentos
    args = parser.parse_args()
    
    # Executar a tarefa
    print(f"Iniciando tarefa em {args.url}...")
    result = run_browser_task(
        args.url,
        args.task,
        args.api_url,
        args.api_key
    )
    
    # Mostrar o resultado
    print("\nResultado:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Salvar o resultado se especificado
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResultado salvo em {args.output}") 