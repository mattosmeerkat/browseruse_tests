#!/usr/bin/env python3
"""
Ferramenta de diagnóstico para verificar se o browser consegue acessar corretamente os sites.
Este script testa diretamente o acesso usando Playwright sem depender do browser_use,
ajudando a identificar se o problema está na biblioteca ou no site.
"""

import asyncio
import json
import os
import sys
import argparse
import time
from datetime import datetime
from playwright.async_api import async_playwright

# Configuração
DEFAULT_URL = "https://www.gov.br/cvm/pt-br/assuntos/noticias"
OUTPUT_DIR = "diagnostic_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def diagnose_site(url, selectors=None, wait_time=5, headless=True, verbose=True):
    """
    Realiza um diagnóstico detalhado do acesso ao site usando Playwright.
    
    Args:
        url: URL do site a ser testado
        selectors: Lista de seletores CSS para verificar na página
        wait_time: Tempo de espera adicional após carregar a página
        headless: Executa em modo headless (sem interface gráfica)
        verbose: Mostra informações detalhadas durante a execução
    
    Returns:
        dict: Resultados do diagnóstico
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "success": False,
        "steps": [],
        "errors": [],
        "page_info": {},
        "selectors": {}
    }
    
    def log(message, level="INFO"):
        timestamp = datetime.now().isoformat()
        if verbose:
            print(f"[{timestamp}] [{level}] {message}")
        result["steps"].append({"time": timestamp, "level": level, "message": message})
    
    log(f"Iniciando diagnóstico para URL: {url}")
    
    try:
        async with async_playwright() as p:
            log("Playwright inicializado")
            
            # Iniciar o navegador
            browser_type = p.chromium
            log("Inicializando navegador Chromium")
            browser = await browser_type.launch(headless=headless)
            
            # Criar contexto e página
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # Configurar logs de console e erros
            page = await context.new_page()
            
            # Registrar logs do console
            page.on("console", lambda msg: log(f"Console {msg.type}: {msg.text}", level="CONSOLE"))
            page.on("pageerror", lambda err: log(f"Erro na página: {err}", level="ERROR"))
            
            # Navegar para a URL
            log(f"Navegando para {url}")
            start_time = time.time()
            
            try:
                response = await page.goto(url, wait_until="networkidle", timeout=60000)
                load_time = time.time() - start_time
                
                if response:
                    status = response.status
                    result["page_info"]["status_code"] = status
                    result["page_info"]["load_time_seconds"] = round(load_time, 2)
                    log(f"Página carregada: Status {status} em {load_time:.2f} segundos")
                    
                    # Verificar se é redirecionamento
                    if status >= 300 and status < 400:
                        redir_url = response.headers.get("location")
                        log(f"Redirecionamento detectado para: {redir_url}", level="WARNING")
                        result["page_info"]["redirect_url"] = redir_url
                else:
                    log("Resposta nula ao carregar a página", level="ERROR")
                    result["errors"].append("Resposta nula")
                
                # Aguardar tempo adicional se solicitado
                if wait_time > 0:
                    log(f"Aguardando {wait_time} segundos adicionais")
                    await asyncio.sleep(wait_time)
                
                # Capturar título da página
                title = await page.title()
                log(f"Título da página: {title}")
                result["page_info"]["title"] = title
                
                # Verificar URL atual (para detectar redirecionamentos)
                current_url = page.url
                result["page_info"]["final_url"] = current_url
                if current_url != url:
                    log(f"URL final diferente da inicial: {current_url}", level="WARNING")
                
                # Verificar seletores
                if selectors:
                    for selector in selectors:
                        log(f"Verificando seletor: {selector}")
                        try:
                            start_selector = time.time()
                            element = await page.wait_for_selector(selector, timeout=5000)
                            selector_time = time.time() - start_selector
                            
                            if element:
                                is_visible = await element.is_visible()
                                result["selectors"][selector] = {
                                    "found": True,
                                    "visible": is_visible,
                                    "time_seconds": round(selector_time, 2)
                                }
                                
                                # Tentar obter o texto do elemento
                                try:
                                    text = await element.text_content()
                                    text_preview = text[:100] + "..." if len(text) > 100 else text
                                    result["selectors"][selector]["text_preview"] = text_preview.strip()
                                    log(f"Seletor '{selector}' encontrado, visível: {is_visible}, texto: {text_preview}")
                                except Exception as e:
                                    log(f"Erro ao obter texto do seletor '{selector}': {str(e)}", level="WARNING")
                            else:
                                result["selectors"][selector] = {"found": False}
                                log(f"Seletor '{selector}' não encontrado (timeout)", level="WARNING")
                                
                        except Exception as e:
                            result["selectors"][selector] = {"found": False, "error": str(e)}
                            log(f"Erro ao verificar seletor '{selector}': {str(e)}", level="ERROR")
                
                # Capturar screenshot
                screenshot_path = os.path.join(OUTPUT_DIR, f"screenshot_{int(time.time())}.png")
                await page.screenshot(path=screenshot_path)
                log(f"Screenshot salvo em: {screenshot_path}")
                result["page_info"]["screenshot_path"] = screenshot_path
                
                # Capturar HTML da página para análise
                html_path = os.path.join(OUTPUT_DIR, f"page_{int(time.time())}.html")
                content = await page.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(content)
                log(f"HTML da página salvo em: {html_path}")
                result["page_info"]["html_path"] = html_path
                
                # Verificar se há frames na página
                frames = page.frames
                result["page_info"]["frames_count"] = len(frames)
                if len(frames) > 1:
                    log(f"Página contém {len(frames)} frames", level="INFO")
                    frame_info = []
                    for i, frame in enumerate(frames):
                        frame_url = frame.url
                        frame_name = frame.name or f"frame_{i}"
                        log(f"Frame {i}: URL={frame_url}, Name={frame_name}")
                        frame_info.append({"name": frame_name, "url": frame_url})
                    result["page_info"]["frames"] = frame_info
                
                # Tentar extrair informações de notícias (específico para o site da CVM)
                if "cvm" in url and "noticias" in url:
                    log("Tentando extrair informações de notícias...")
                    try:
                        # Modificar estes seletores conforme a estrutura do site
                        noticia_selector = ".titulo"
                        noticias = await page.query_selector_all(noticia_selector)
                        
                        news_list = []
                        for i, noticia in enumerate(noticias[:5]):  # Limitar a 5 notícias
                            try:
                                titulo = await noticia.inner_text()
                                link_element = await noticia.query_selector("a") or noticia
                                link = await link_element.get_attribute("href") or "N/A"
                                news_list.append({"titulo": titulo, "link": link})
                                log(f"Notícia {i+1}: {titulo}")
                            except Exception as ne:
                                log(f"Erro ao extrair notícia {i+1}: {str(ne)}", level="WARNING")
                        
                        result["news_sample"] = news_list
                        log(f"Extraídas {len(news_list)} notícias de exemplo")
                    except Exception as e:
                        log(f"Erro ao extrair notícias: {str(e)}", level="ERROR")
                
                result["success"] = True
                log("Diagnóstico concluído com sucesso")
                
            except Exception as e:
                log(f"Erro ao navegar para a URL: {str(e)}", level="ERROR")
                result["errors"].append(str(e))
            
            finally:
                # Fechar o navegador
                await browser.close()
                log("Navegador fechado")
    
    except Exception as e:
        log(f"Erro durante o diagnóstico: {str(e)}", level="ERROR")
        result["errors"].append(str(e))
    
    # Salvar resultado em JSON
    result_path = os.path.join(OUTPUT_DIR, f"diagnosis_{int(time.time())}.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    if verbose:
        print(f"\nResultado do diagnóstico salvo em: {result_path}")
        print(f"Screenshot salvo em: {result.get('page_info', {}).get('screenshot_path', 'N/A')}")
        print(f"HTML salvo em: {result.get('page_info', {}).get('html_path', 'N/A')}")
    
    return result

async def main():
    parser = argparse.ArgumentParser(description="Ferramenta de diagnóstico para sites usando Playwright")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"URL do site a ser diagnosticado (padrão: {DEFAULT_URL})")
    parser.add_argument("--selectors", nargs="+", help="Seletores CSS para verificar (ex: '.titulo' 'h1' 'header')")
    parser.add_argument("--wait", type=int, default=5, help="Tempo de espera adicional em segundos (padrão: 5)")
    parser.add_argument("--visible", action="store_true", help="Executar em modo visível (não headless)")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso (menos output)")
    
    args = parser.parse_args()
    
    print(f"Iniciando diagnóstico do site: {args.url}")
    result = await diagnose_site(
        url=args.url,
        selectors=args.selectors,
        wait_time=args.wait,
        headless=not args.visible,
        verbose=not args.quiet
    )
    
    if result["success"]:
        print("\n✅ Diagnóstico concluído com sucesso")
        if result.get("page_info", {}).get("status_code", 0) >= 400:
            print(f"⚠️ Atenção: Status HTTP {result['page_info']['status_code']}")
    else:
        print("\n❌ Diagnóstico falhou")
        for error in result["errors"]:
            print(f"Erro: {error}")
    
    # Resumo para seletores
    if args.selectors:
        print("\nResultado dos seletores:")
        for selector, info in result.get("selectors", {}).items():
            status = "✅ Encontrado" if info.get("found", False) else "❌ Não encontrado"
            print(f"{selector}: {status}")
    
    print(f"\nArquivos de diagnóstico salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main()) 