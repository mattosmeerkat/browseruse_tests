from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
import os
import json
import secrets
import logging
import traceback
import time
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
load_dotenv()

# Configuração de logging avançada
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Logger principal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/api.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("browser-use-api")

# Logger específico para diagnóstico do browser_use
diag_logger = logging.getLogger("browser-use-diag")
diag_handler = logging.FileHandler(f"{log_dir}/browser_use_debug.log")
diag_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
diag_logger.addHandler(diag_handler)
diag_logger.setLevel(logging.DEBUG)

# Configuração da API
app = FastAPI(
    title="Browser Use API",
    description="API para executar tarefas de navegação web usando LLMs",
    version="1.0.0"
)

# Sistema de autenticação aprimorado
security = HTTPBearer()

# Gerar uma chave padrão forte se não existir no env
DEFAULT_API_KEY = os.getenv("API_KEY")
if not DEFAULT_API_KEY:
    DEFAULT_API_KEY = secrets.token_urlsafe(32)
    logger.warning(f"API_KEY não encontrada no ambiente. Gerada chave temporária: {DEFAULT_API_KEY}")

# Suporte a múltiplas chaves API
API_KEYS = {}

# Adicionar chave do ambiente
API_KEYS[DEFAULT_API_KEY] = "admin"

# Suporte a chave de desenvolvimento local para testes
DEV_KEY = "123"
if os.getenv("ENVIRONMENT", "production").lower() != "production":
    API_KEYS[DEV_KEY] = "developer"
    logger.info("Modo de desenvolvimento ativado. Chave de teste '123' habilitada.")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica se a API key fornecida é válida"""
    if not credentials.credentials in API_KEYS:
        logger.warning(f"Tentativa de acesso com API key inválida: {credentials.credentials[:5]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Registra o acesso bem-sucedido
    user_role = API_KEYS[credentials.credentials]
    logger.info(f"Acesso autorizado para usuário com role: {user_role}")
    return user_role

# Modelos de dados
class BrowserTask(BaseModel):
    url: str
    task: str
    model: Optional[str] = "gpt-4.1"
    timeout: Optional[int] = 300
    additional_params: Optional[Dict[str, Any]] = None
    debug_mode: Optional[bool] = False

class TaskResponse(BaseModel):
    task_id: str
    result: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    status: str = "completed"
    error: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None

class DiagnosticRequest(BaseModel):
    url: str
    selector: Optional[str] = None
    wait_time: Optional[int] = 5
    capture_screenshot: Optional[bool] = True

class DiagnosticResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    debug_info: Optional[Dict[str, Any]] = None

# Função para logs detalhados
def log_detailed_info(task_id: str, message: str, level: str = "INFO", extra_data: Any = None):
    """Registra informações detalhadas no log de diagnóstico"""
    log_entry = {
        "task_id": task_id,
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "extra_data": extra_data
    }
    
    if level.upper() == "DEBUG":
        diag_logger.debug(json.dumps(log_entry))
    elif level.upper() == "INFO":
        diag_logger.info(json.dumps(log_entry))
    elif level.upper() == "WARNING":
        diag_logger.warning(json.dumps(log_entry))
    elif level.upper() == "ERROR":
        diag_logger.error(json.dumps(log_entry))
    else:
        diag_logger.info(json.dumps(log_entry))

# Endpoints da API
@app.post("/run_task", response_model=TaskResponse)
async def run_task(task_request: BrowserTask, user_role: str = Depends(verify_api_key)):
    """
    Executa uma tarefa de navegação web usando o agente LLM.
    Requer autenticação via Bearer Token.
    """
    task_id = f"task_{secrets.token_hex(8)}"
    logger.info(f"Nova tarefa iniciada: {task_id} - URL: {task_request.url}")
    log_detailed_info(task_id, f"Iniciando tarefa com URL: {task_request.url}", "INFO", 
                     {"task": task_request.task, "timeout": task_request.timeout})
    
    debug_info = {
        "start_time": datetime.now().isoformat(),
        "task_details": {
            "url": task_request.url,
            "model": task_request.model,
            "timeout": task_request.timeout
        },
        "logs": []
    }
    
    try:
        # Inicializar o agente com os parâmetros recebidos
        # Inclui a URL na task
        full_task = f"Acesse {task_request.url}. {task_request.task}"
        log_detailed_info(task_id, "Construindo o prompt para o agente", "DEBUG", {"full_task": full_task})
        
        # Iniciar timer para medir desempenho
        start_time = time.time()
        
        try:
            # Criar e configurar o agente
            agent = Agent(
                task=full_task,
                llm=ChatOpenAI(model=task_request.model),
            )
            log_detailed_info(task_id, "Agente inicializado com sucesso", "DEBUG")
            
            # Executar a tarefa
            logger.info(f"Executando agente para tarefa {task_id}")
            log_detailed_info(task_id, "Iniciando execução do agente run()", "INFO")
            
            # Definir timeout customizado se fornecido
            result = await asyncio.wait_for(
                agent.run(), 
                timeout=task_request.timeout
            )
            
            execution_time = time.time() - start_time
            log_detailed_info(task_id, f"Execução do agente concluída em {execution_time:.2f} segundos", "INFO")
            
            # Obter resultado final
            log_detailed_info(task_id, "Extraindo resultado final do agente", "DEBUG")
            final_result = result.final_result()
            
            if final_result:
                log_detailed_info(task_id, "Resultado final obtido", "DEBUG", 
                                 {"result_size": len(final_result)})
            else:
                log_detailed_info(task_id, "Resultado final vazio", "WARNING")
            
            logger.info(f"Tarefa {task_id} concluída em {execution_time:.2f} segundos")
            
            # Adicionar informações de timing ao debug
            debug_info["execution_time"] = execution_time
            debug_info["end_time"] = datetime.now().isoformat()
            
            # Verificar se o resultado é JSON válido
            try:
                if final_result:
                    log_detailed_info(task_id, "Tentando parsear resultado como JSON", "DEBUG")
                    json_result = json.loads(final_result)
                    log_detailed_info(task_id, "Parse JSON bem-sucedido", "DEBUG")
                    
                    # Lidar com diferentes formatos de resultado (objeto único ou array)
                    if isinstance(json_result, list):
                        log_detailed_info(task_id, f"Resultado é uma lista com {len(json_result)} itens", "DEBUG")
                    else:
                        log_detailed_info(task_id, "Resultado é um objeto único", "DEBUG")
                    
                    return TaskResponse(
                        task_id=task_id,
                        result=json_result,
                        status="completed",
                        debug_info=debug_info if task_request.debug_mode else None
                    )
                else:
                    logger.warning(f"Tarefa {task_id} retornou resultado vazio")
                    log_detailed_info(task_id, "Retornando resultado vazio", "WARNING")
                    
                    return TaskResponse(
                        task_id=task_id,
                        status="completed",
                        result={},
                        error="Sem resultados retornados",
                        debug_info=debug_info if task_request.debug_mode else None
                    )
            except json.JSONDecodeError as e:
                # Se não for JSON válido, retornamos como texto
                logger.warning(f"Tarefa {task_id} retornou resultado não-JSON: {str(e)}")
                log_detailed_info(task_id, "Erro ao parsear JSON", "WARNING", {"error": str(e)})
                
                # Para depuração, tentamos mostrar o início do resultado
                result_preview = final_result[:500] + "..." if len(final_result) > 500 else final_result
                log_detailed_info(task_id, "Preview do resultado não-JSON", "DEBUG", {"preview": result_preview})
                
                return TaskResponse(
                    task_id=task_id,
                    result={"raw_text": final_result},
                    status="completed",
                    debug_info=debug_info if task_request.debug_mode else None
                )
        except asyncio.TimeoutError:
            logger.error(f"Timeout na tarefa {task_id} após {task_request.timeout} segundos")
            log_detailed_info(task_id, f"Timeout após {task_request.timeout} segundos", "ERROR")
            
            debug_info["error"] = "TIMEOUT"
            debug_info["end_time"] = datetime.now().isoformat()
            
            return TaskResponse(
                task_id=task_id,
                status="error",
                error=f"Timeout após {task_request.timeout} segundos",
                debug_info=debug_info if task_request.debug_mode else None
            )
            
    except Exception as e:
        # Captura detalhada de exceções
        error_msg = str(e)
        trace = traceback.format_exc()
        logger.error(f"Erro na tarefa {task_id}: {error_msg}", exc_info=True)
        log_detailed_info(task_id, f"Erro durante execução: {error_msg}", "ERROR", {"traceback": trace})
        
        debug_info["error"] = error_msg
        debug_info["traceback"] = trace
        debug_info["end_time"] = datetime.now().isoformat()
        
        return TaskResponse(
            task_id=task_id,
            status="error",
            error=error_msg,
            debug_info=debug_info if task_request.debug_mode else None
        )

@app.post("/diagnose_browser", response_model=DiagnosticResponse)
async def diagnose_browser(
    diagnostic_req: DiagnosticRequest, 
    user_role: str = Depends(verify_api_key)
):
    """
    Endpoint de diagnóstico que testa o acesso a um URL específico.
    Usado para verificar se o browser-use consegue acessar corretamente os sites.
    """
    diag_id = f"diag_{secrets.token_hex(6)}"
    logger.info(f"Solicitação de diagnóstico: {diag_id} - URL: {diagnostic_req.url}")
    
    debug_info = {
        "id": diag_id,
        "timestamp": datetime.now().isoformat(),
        "url": diagnostic_req.url,
    }
    
    try:
        # Esta é uma simplificação - na implementação real você usaria o browser_use
        # para capturar uma screenshot e outros diagnósticos
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Adicionar logs para diagnóstico
            page.on("console", lambda msg: diag_logger.debug(f"Browser console [{msg.type}]: {msg.text}"))
            page.on("pageerror", lambda err: diag_logger.error(f"Page error: {err}"))
            
            # Registrar progresso de navegação
            diag_logger.info(f"[{diag_id}] Navegando para {diagnostic_req.url}")
            response = await page.goto(diagnostic_req.url, wait_until="networkidle")
            
            # Verificar resposta HTTP
            status_code = response.status if response else 0
            debug_info["status_code"] = status_code
            diag_logger.info(f"[{diag_id}] Página carregada com status: {status_code}")
            
            # Aguardar tempo adicional se solicitado
            if diagnostic_req.wait_time > 0:
                diag_logger.info(f"[{diag_id}] Aguardando {diagnostic_req.wait_time}s adicionais")
                await asyncio.sleep(diagnostic_req.wait_time)
            
            # Verificar se o seletor está presente, se fornecido
            if diagnostic_req.selector:
                diag_logger.info(f"[{diag_id}] Verificando seletor: {diagnostic_req.selector}")
                try:
                    element = await page.wait_for_selector(diagnostic_req.selector, timeout=5000)
                    is_visible = await element.is_visible()
                    debug_info["selector_found"] = True
                    debug_info["selector_visible"] = is_visible
                    diag_logger.info(f"[{diag_id}] Seletor encontrado, visível: {is_visible}")
                except Exception as se:
                    debug_info["selector_found"] = False
                    debug_info["selector_error"] = str(se)
                    diag_logger.warning(f"[{diag_id}] Seletor não encontrado: {str(se)}")
            
            # Capturar screenshot se solicitado
            if diagnostic_req.capture_screenshot:
                screenshot_path = f"{log_dir}/screenshot_{diag_id}.png"
                await page.screenshot(path=screenshot_path)
                debug_info["screenshot_path"] = screenshot_path
                diag_logger.info(f"[{diag_id}] Screenshot salvo em: {screenshot_path}")
            
            # Obter conteúdo da página
            page_content = await page.content()
            content_preview = page_content[:500] + "..." if len(page_content) > 500 else page_content
            debug_info["content_preview"] = content_preview
            
            # Verificar título da página
            title = await page.title()
            debug_info["page_title"] = title
            
            await browser.close()
            
            return DiagnosticResponse(
                status="success",
                message=f"Diagnóstico concluído com sucesso para {diagnostic_req.url}",
                timestamp=datetime.now().isoformat(),
                debug_info=debug_info
            )
            
    except Exception as e:
        error_msg = str(e)
        trace = traceback.format_exc()
        logger.error(f"Erro no diagnóstico {diag_id}: {error_msg}", exc_info=True)
        
        debug_info["error"] = error_msg
        debug_info["traceback"] = trace
        
        return DiagnosticResponse(
            status="error",
            message=f"Erro durante diagnóstico: {error_msg}",
            timestamp=datetime.now().isoformat(),
            debug_info=debug_info
        )

@app.get("/health")
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {"status": "ok", "environment": os.getenv("ENVIRONMENT", "production")}

@app.get("/view_logs/{lines}")
async def view_recent_logs(lines: int = 50, user_role: str = Depends(verify_api_key)):
    """Retorna as linhas mais recentes do log de diagnóstico"""
    if lines > 1000:
        lines = 1000  # Limitar para evitar problemas de performance
        
    try:
        log_path = f"{log_dir}/browser_use_debug.log"
        if not os.path.exists(log_path):
            return {"status": "error", "message": "Arquivo de log não encontrado"}
            
        # Ler as últimas 'lines' linhas do arquivo
        with open(log_path, 'r') as f:
            # Ler todas as linhas e obter as últimas N
            all_lines = f.readlines()
            recent_logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
        return {
            "status": "success", 
            "lines_count": len(recent_logs),
            "logs": recent_logs
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro ao ler logs: {str(e)}"}

# Documentação interativa aprimorada
@app.get("/")
async def root():
    """Endpoint raiz com informações sobre a API"""
    return {
        "message": "Browser Use API está rodando!",
        "documentação": "/docs",
        "endpoints": [
            {"método": "POST", "caminho": "/run_task", "descrição": "Executa tarefa de navegação web"},
            {"método": "POST", "caminho": "/diagnose_browser", "descrição": "Realiza diagnóstico de acesso a sites"},
            {"método": "GET", "caminho": "/health", "descrição": "Verifica se a API está funcionando"},
            {"método": "GET", "caminho": "/view_logs/{lines}", "descrição": "Visualiza logs recentes"}
        ]
    }

# Inicialização da API
if __name__ == "__main__":
    import uvicorn
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Mostrar a chave API para ambiente de desenvolvimento
    if os.getenv("ENVIRONMENT", "production").lower() != "production":
        print(f"Modo de desenvolvimento. API Keys disponíveis: {list(API_KEYS.keys())}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 