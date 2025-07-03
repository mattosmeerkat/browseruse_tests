from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from browser_use import Agent, Browser, BrowserConfig
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
import tempfile

# Importar watchtower para CloudWatch logging
import watchtower

# Carregar variáveis de ambiente com prioridade absoluta
load_dotenv(override=True)

# Configuração de logging avançada
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Obter nome do grupo de logs do ambiente, default para "BrowserUseAPI"
LOG_GROUP_NAME = os.getenv("LOG_GROUP_NAME", "BrowserUseAPILogs")
# Obter nome do stream de logs do ambiente, default para "api"
LOG_STREAM_NAME_API = os.getenv("LOG_STREAM_NAME_API", "api-logs")
LOG_STREAM_NAME_DIAG = os.getenv("LOG_STREAM_NAME_DIAG", "diag-logs")

# Logger principal
logger = logging.getLogger("browser-use-api")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.addHandler(logging.FileHandler(f"{log_dir}/api.log"))

# Logger específico para diagnóstico do browser_use
diag_logger = logging.getLogger("browser-use-diag")
diag_logger.setLevel(logging.DEBUG) # Mantido como DEBUG para logs detalhados
diag_handler = logging.FileHandler(f"{log_dir}/browser_use_debug.log")
diag_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
diag_logger.addHandler(diag_handler)

# Configurar Watchtower se estiver em ambiente de produção e LOG_GROUP_NAME estiver definido
if os.getenv("ENVIRONMENT", "development").lower() == "production" and LOG_GROUP_NAME:
    try:
        # Handler para o logger principal
        cw_handler_api = watchtower.CloudWatchLogHandler(
            log_group_name=LOG_GROUP_NAME,
            log_stream_name=LOG_STREAM_NAME_API,
            send_interval=60,  # Envia logs a cada 60 segundos
            create_log_group=True
        )
        cw_handler_api.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(cw_handler_api)
        logger.info(f"Watchtower configurado para o logger principal. Grupo: {LOG_GROUP_NAME}, Stream: {LOG_STREAM_NAME_API}")

        # Handler para o logger de diagnóstico
        cw_handler_diag = watchtower.CloudWatchLogHandler(
            log_group_name=LOG_GROUP_NAME,
            log_stream_name=LOG_STREAM_NAME_DIAG,
            send_interval=60,
            create_log_group=True # O grupo já deve ter sido criado acima, mas para garantir
        )
        cw_handler_diag.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        diag_logger.addHandler(cw_handler_diag)
        diag_logger.info(f"Watchtower configurado para o logger de diagnóstico. Grupo: {LOG_GROUP_NAME}, Stream: {LOG_STREAM_NAME_DIAG}")

    except Exception as e:
        logger.error(f"Falha ao configurar Watchtower: {e}", exc_info=True)
else:
    logger.info("Watchtower não configurado (não é ambiente de produção ou LOG_GROUP_NAME não definido).")

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
DEV_KEY = "123"  # Definindo a chave de teste
if os.getenv("ENVIRONMENT", "development").lower() != "production":
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
    model: Optional[str] = "deepseek-chat"
    timeout: Optional[int] = 300
    additional_params: Optional[Dict[str, Any]] = None
    debug_mode: Optional[bool] = False
    additional_load_wait_time: Optional[int] = 5

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

def get_llm_instance(model_name: str):
    """
    Retorna a instância correta do LLM baseado no nome do modelo.
    Suporta tanto OpenAI quanto DeepSeek com carregamento dinâmico.
    """
    logger.info(f"Inicializando modelo: {model_name}")
    
    # Modelos DeepSeek - detecção mais precisa
    if any(keyword in model_name.lower() for keyword in ['deepseek']):
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            logger.error("DEEPSEEK_API_KEY não encontrada nas variáveis de ambiente")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DEEPSEEK_API_KEY não encontrada nas variáveis de ambiente"
            )
        
        logger.info(f"Configurando DeepSeek com modelo: {model_name}, API Base: https://api.deepseek.com")
        logger.debug(f"DEEPSEEK_API_KEY disponível: {deepseek_api_key[:10]}...")
        
        try:
            return ChatDeepSeek(
                model=model_name,
                temperature=0.7,
                max_tokens=2048,
                api_key=deepseek_api_key,
                api_base="https://api.deepseek.com"
            )
        except Exception as e:
            logger.error(f"Erro ao inicializar DeepSeek: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao inicializar modelo DeepSeek: {str(e)}"
            )
    
    # Modelos OpenAI (padrão para outros modelos)
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENAI_API_KEY não encontrada nas variáveis de ambiente"
            )
        
        logger.info(f"Configurando OpenAI com modelo: {model_name}")
        logger.debug(f"OPENAI_API_KEY disponível: {openai_api_key[:10]}...")
        
        try:
            return ChatOpenAI(
                model=model_name,
                temperature=0.7,
                max_tokens=2048,
                api_key=openai_api_key,
            )
        except Exception as e:
            logger.error(f"Erro ao inicializar OpenAI: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao inicializar modelo OpenAI: {str(e)}"
            )

# Endpoints da API
@app.post("/run_task", response_model=TaskResponse)
async def run_task(task_request: BrowserTask, user_role: str = Depends(verify_api_key)):
    """
    Executa uma tarefa de navegação web usando o agente LLM.
    Requer autenticação via Bearer Token.
    """
    task_id = f"task_{secrets.token_hex(8)}"
    original_debug_mode_flag = task_request.debug_mode
    
    # Use o objeto task_request diretamente para os logs e debug_info para consistência
    logger.info(f"Nova tarefa iniciada: {task_id} - URL: {task_request.url}, Model: {task_request.model}, WaitTime: {task_request.additional_load_wait_time}")
    log_detailed_info(task_id, f"Iniciando tarefa com URL: {task_request.url}", "INFO", 
                     {"task": task_request.task, 
                      "timeout": task_request.timeout, 
                      "additional_load_wait_time": task_request.additional_load_wait_time})
    
    # Construir debug_info explicitamente
    task_details_for_debug = {
        "url": task_request.url,
        "model": task_request.model,
        "timeout": task_request.timeout,
        # Garantir que additional_load_wait_time esteja presente se não for None
        "additional_load_wait_time": task_request.additional_load_wait_time 
    }
    # Adicionar additional_params apenas se existir e não for None
    if task_request.additional_params is not None:
        task_details_for_debug["additional_params"] = task_request.additional_params
    # Adicionar debug_mode explicitamente (como booleano)
    task_details_for_debug["debug_mode"] = original_debug_mode_flag

    debug_info = {
        "start_time": datetime.now().isoformat(),
        "task_details": task_details_for_debug,
        "logs": []
    }

    try:
        technical_instructions = ""
        if task_request.additional_load_wait_time and task_request.additional_load_wait_time > 0:
            technical_instructions = f"""

INSTRUÇÕES TÉCNICAS PARA CARREGAMENTO DINÂMICO:
1. Após carregar a página inicial, aguarde {task_request.additional_load_wait_time} segundos para que todo conteúdo dinâmico seja carregado
2. Aguarde elementos aparecerem completamente antes de tentar interagir com eles
3. Se necessário, aguarde que requisições AJAX/Fetch sejam concluídas
4. Para sites com carregamento assíncrono, certifique-se de que todos os elementos estejam visíveis
5. Use wait_for_selector ou wait_for_load_state quando apropriado
6. Considere que o conteúdo pode ser populado via JavaScript após o carregamento inicial

"""
            log_detailed_info(task_id, f"Adicionando instruções técnicas para espera de {task_request.additional_load_wait_time} segundos", "DEBUG")
        
        full_task = f"Acesse {task_request.url}.{technical_instructions}{task_request.task}"
        log_detailed_info(task_id, "Construindo o prompt para o agente", "DEBUG", {"full_task": full_task[:500] + "..." if len(full_task) > 500 else full_task})
        
        start_time = time.time()
        final_result = "" # Initialize final_result
        result = None # Initialize result

        browser = None
        temp_dir = None
        try:
            # CRIAR DIRETÓRIO TEMPORÁRIO ÚNICO para cada execução
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix=f"browser_{task_id}_")
            log_detailed_info(task_id, f"Diretório temporário criado: {temp_dir}", "DEBUG")
            
            # CONFIGURAÇÃO CRÍTICA: Browser totalmente isolado a cada execução
            browser_config = BrowserConfig(
                # Forçar headless para servidor
                headless=True,
                
                # CRITICAL: Args anti-cache explícitos para isolamento total
                extra_chromium_args=[
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-features=TranslateUI,VizDisplayCompositor',
                    '--disable-web-security',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    
                    # CACHE DESTRUCTION: Zero persistência entre execuções
                    '--disk-cache-size=0',           # Zero cache de disco
                    '--memory-cache-size=0',         # Zero cache de memória  
                    '--disable-application-cache',   # Sem cache de aplicações
                    '--disable-offline-load-stale-cache',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    
                    # MODO INCÓGNITO FORÇADO: Sem dados persistentes
                    '--incognito',
                    f'--user-data-dir={temp_dir}',  # Dir temporário ÚNICO por execução
                    '--data-reduction-proxy-bypass',
                    '--disable-session-crashed-bubble',
                    '--disable-infobars',
                    '--disable-features=VizDisplayCompositor',
                    
                    # OTIMIZAÇÕES ADICIONAIS
                    '--disable-blink-features=AutomationControlled',
                    '--disable-ipc-flooding-protection',
                ]
            )
            
            # Criar browser isolado para esta execução
            browser = Browser(config=browser_config)
            log_detailed_info(task_id, "Browser isolado criado com configuração anti-cache", "DEBUG")
            
            # Criar agente com browser explícito e isolado
            agent = Agent(
                task=full_task,
                llm=get_llm_instance(task_request.model),
                browser=browser  # Browser explícito e isolado para esta tarefa
            )
            log_detailed_info(task_id, "Agente inicializado com sucesso", "DEBUG")
            
            logger.info(f"Executando agente para tarefa {task_id}")
            log_detailed_info(task_id, "Iniciando execução do agente run()", "INFO")
            
            # DEBUG: Log do timeout antes de usar
            print(f"DEBUG: timeout = {task_request.timeout}, tipo = {type(task_request.timeout)}")
            print(f"DEBUG: timeout é None? {task_request.timeout is None}")
            print(f"DEBUG: timeout convertido para float: {float(task_request.timeout)}")
            
            # VERIFICAR SE O TIMEOUT É VÁLIDO
            timeout_value = task_request.timeout
            if timeout_value is None or timeout_value <= 0:
                logger.warning(f"Timeout inválido detectado: {timeout_value}, usando padrão de 300")
                timeout_value = 300
            
            # USAR TIMEOUT EXPLÍCITO
            try:
                result = await asyncio.wait_for(
                    agent.run(), 
                    timeout=float(timeout_value)
                )
            except asyncio.TimeoutError:
                # CAPTURAR O TIMEOUT EXPLICITAMENTE
                logger.error(f"TIMEOUT CAPTURADO - Tarefa {task_id} expirou após {timeout_value} segundos")
                raise  # Re-raise para ser capturado pelo except externo
            
            execution_time = time.time() - start_time
            log_detailed_info(task_id, f"Execução do agente concluída em {execution_time:.2f} segundos", "INFO")
            
            if hasattr(result, "final_result"):
                final_result = result.final_result()
            elif isinstance(result, str):
                final_result = result
            else:
                try:
                    final_result = str(result)
                    log_detailed_info(task_id, "Resultado convertido para string", "WARNING")
                except Exception as e:
                    log_detailed_info(task_id, f"Erro ao converter resultado: {str(e)}", "ERROR")
            
            if final_result:
                log_detailed_info(task_id, "Resultado final obtido", "DEBUG", {"result_size": len(final_result)})
            else:
                log_detailed_info(task_id, "Resultado final vazio", "WARNING")
            
            logger.info(f"Tarefa {task_id} concluída em {execution_time:.2f} segundos")
            
            debug_info["execution_time"] = execution_time
            debug_info["end_time"] = datetime.now().isoformat()
            
            # Limpeza EXPLÍCITA do browser isolado
            try:
                if browser:
                    await browser.close()
                    log_detailed_info(task_id, "Browser isolado fechado com sucesso", "DEBUG")
                # Limpar diretório temporário ÚNICO desta execução
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    log_detailed_info(task_id, f"Diretório temporário {temp_dir} limpo", "DEBUG")
            except Exception as cleanup_error:
                log_detailed_info(task_id, f"Erro na limpeza do browser: {cleanup_error}", "WARNING")
            
            try:
                if final_result:
                    json_result = json.loads(final_result)
                    return TaskResponse(
                        task_id=task_id,
                        result=json_result,
                        status="completed",
                        debug_info=debug_info if original_debug_mode_flag else None
                    )
                else:
                    logger.warning(f"Tarefa {task_id} retornou resultado vazio")
                    return TaskResponse(
                        task_id=task_id,
                        status="completed",
                        result={},
                        error="Sem resultados retornados",
                        debug_info=debug_info if original_debug_mode_flag else None
                    )
            except json.JSONDecodeError as e:
                logger.warning(f"Tarefa {task_id} retornou resultado não-JSON: {str(e)}")
                log_detailed_info(task_id, "Erro ao parsear JSON final", "WARNING", {"error": str(e), "raw_output": final_result[:1000] + ("..." if len(final_result) > 1000 else "") })
                result_preview = final_result[:500] + "..." if len(final_result) > 500 else final_result
                log_detailed_info(task_id, "Preview do resultado não-JSON", "DEBUG", {"preview": result_preview})
                # Modificado para retornar um array com o texto bruto, conforme solicitado
                return TaskResponse(
                    task_id=task_id,
                    result=[{"raw_text": final_result}], # Retorna array com o dado bruto
                    status="completed_with_parsing_error", # Novo status para indicar o problema
                    error="JSON parsing failed for final result, returning raw text.",
                    debug_info=debug_info if original_debug_mode_flag else None
                )
        except asyncio.TimeoutError:
            logger.error(f"Timeout na tarefa {task_id} após {task_request.timeout} segundos")
            log_detailed_info(task_id, f"Timeout após {task_request.timeout} segundos", "ERROR")
            debug_info["error"] = "TIMEOUT"
            debug_info["end_time"] = datetime.now().isoformat()
            
            # Limpeza EXPLÍCITA após timeout
            try:
                if browser:
                    await browser.close()
                    log_detailed_info(task_id, "Browser isolado fechado após timeout", "DEBUG")
                # Limpar diretório temporário ÚNICO
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    log_detailed_info(task_id, f"Diretório temporário {temp_dir} limpo após timeout", "DEBUG")
            except Exception as cleanup_error:
                log_detailed_info(task_id, f"Erro na limpeza após timeout: {cleanup_error}", "WARNING")
            
            return TaskResponse(
                task_id=task_id,
                status="error",
                error=f"Timeout após {task_request.timeout} segundos",
                debug_info=debug_info if original_debug_mode_flag else None
            )
            
    except Exception as e:
        error_msg = str(e)
        trace = traceback.format_exc()
        logger.error(f"Erro na tarefa {task_id}: {error_msg}", exc_info=True)
        log_detailed_info(task_id, f"Erro durante execução: {error_msg}", "ERROR", {"traceback": trace})
        debug_info["error"] = error_msg
        debug_info["traceback"] = trace
        debug_info["end_time"] = datetime.now().isoformat()
        
        # Limpeza EXPLÍCITA após erro
        try:
            if browser:
                await browser.close()
                log_detailed_info(task_id, "Browser isolado fechado após erro", "DEBUG")
            # Limpar diretório temporário ÚNICO
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                log_detailed_info(task_id, f"Diretório temporário {temp_dir} limpo após erro", "DEBUG")
        except Exception as cleanup_error:
            log_detailed_info(task_id, f"Erro na limpeza após exceção: {cleanup_error}", "WARNING")
        
        return TaskResponse(
            task_id=task_id,
            status="error",
            error=error_msg,
            debug_info=debug_info if original_debug_mode_flag else None
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