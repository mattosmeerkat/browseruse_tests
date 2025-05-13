from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()

async def main():
    print('Iniciando o agente...')
    agent = Agent(
        task="""Acesse https://www.gov.br/cvm/pt-br/pagina-inicial/, clique em 'Assuntos', depois em 'Notícias'.
Leia as notícias do dia de ontem e para cada uma extraia os seguintes dados:

1. Título da notícia
2. Data e hora de publicação (extraindo dia da semana separadamente)
3. Quem fez a notícia 
4. Quem revisou a notícia
5. Nome do regulador (normalmente CVM)
6. Ementa ou resumo da notícia
7. Conteúdo completo da notícia
8. URL/link da notícia

Formate as informações de cada notícia em JSON seguindo exatamente este modelo:
{
  "feito_por": "",
  "revisado_por": "",
  "data_publicacao": "",
  "dia_semana": "",
  "hora_publicacao": "",
  "regulador": "CVM",
  "titulo": "",
  "ementa": "",
  "conteudo_completo": "",
  "link": ""
}

Se algum dos campos não estiver disponível, deixe-o vazio, mas inclua todos os campos.
Retorne um JSON válido para cada notícia de hoje. Se houver mais de uma notícia, retorne um array de JSONs.
""",
        llm=ChatOpenAI(model="gpt-4.1"),
    )
    print('Executando agent.run()...')
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