from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from browser_use import Agent
import asyncio
import json
import os
from dotenv import load_dotenv
load_dotenv()

def get_llm_instance(model_name: str = "deepseek-reasoner"):
    """
    Retorna a instância correta do LLM baseado no nome do modelo.
    Suporta tanto OpenAI quanto DeepSeek.
    """
    # Modelos DeepSeek
    if any(keyword in model_name.lower() for keyword in ['deepseek', 'reasoner']):
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        return ChatDeepSeek(
            model=model_name,
            temperature=0.7,
            max_tokens=2048,
            api_key=deepseek_api_key,
        )
    
    # Modelos OpenAI (padrão)
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
            max_tokens=2048,
            api_key=openai_api_key,
        )

async def main():
    print('Iniciando o agente...')
    
    # Usar DeepSeek por padrão, mas permite alterar o modelo aqui
    model_name = "deepseek-reasoner"  # Altere aqui para usar outro modelo
    
    agent = Agent(
        task="""Acesse https://www.amf-france.org/fr/actualites-publications/actualites and Action: Navigate directly to the news section of the website. You must actively browse through the news pages, including pagination if necessary, to find the last news article.

Copy the the URL from this last new from href.

The response must be a JSON formatted exactly as below, containing for each news item: Name, Date, and Link:

{
 "news": [
 {
 "Date": "date of the news",
 "Name": "title of the news",
 "Link": "href of the news"
 },
 ...
 ]
}

Do not provide any additional text outside the JSON. Only return the JSON strictly in this format""",
        llm=get_llm_instance(model_name),
    )
    print(f'Executando agent.run() com modelo: {model_name}...')
    result = await agent.run()
    print('Resultado do agent.run():')
    print(result)
    
    # Tentativa de salvar os resultados em um arquivo JSON
    try:
        final_result = result.final_result()
        if final_result:
            with open('noticias_extraidas.json', 'w', encoding='utf-8') as f:
                f.write(final_result)
            print('Dados salvos em noticias_extraidas.json')
    except Exception as e:
        print(f'Erro ao salvar resultados: {e}')

print('Chamando asyncio.run(main())...')
asyncio.run(main())
print('Script finalizado.')