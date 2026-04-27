"""
Logger - Sistema de logging seguro e estruturado
"""
import logging
import re
from typing import Any, Dict
from logging.handlers import RotatingFileHandler
import os


def mask_sensitive_data(text: str) -> str:
    """
    Mascara dados sensíveis em strings
    
    Args:
        text: Texto que pode conter dados sensíveis
    
    Returns:
        Texto com dados sensíveis mascarados
    """
    if not text:
        return text
    
    # Mascara emails
    text = re.sub(
        r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'\1***@\2',
        text
    )
    
    # Mascara telefones (mantém apenas 4 primeiros dígitos)
    text = re.sub(
        r'\b(\d{4})\d{6,11}\b',
        r'\1******',
        text
    )
    
    # Mascara CPF (mantém apenas 3 primeiros dígitos)
    text = re.sub(
        r'\b(\d{3})\d{8}\b',
        r'\1********',
        text
    )
    
    # Mascara tokens e senhas
    for keyword in ['token', 'password', 'senha', 'secret', 'api_key']:
        text = re.sub(
            rf'{keyword}["\']?\s*[:=]\s*["\']?([^"\'\s]+)',
            f'{keyword}=***MASKED***',
            text,
            flags=re.IGNORECASE
        )
    
    return text


class SensitiveDataFilter(logging.Filter):
    """Filtro de logging que mascara dados sensíveis"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Mascara a mensagem
        if hasattr(record, 'msg'):
            record.msg = mask_sensitive_data(str(record.msg))
        
        # Mascara argumentos
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True


def setup_logger(
    name: str,
    log_file: str = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configura logger com rotação de arquivos e mascaramento de dados sensíveis
    
    Args:
        name: Nome do logger
        log_file: Caminho do arquivo de log (opcional)
        level: Nível de log (INFO, DEBUG, etc.)
        max_bytes: Tamanho máximo do arquivo de log
        backup_count: Número de backups a manter
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if log_file:
        # Criar diretório se não existir
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(file_handler)
    
    return logger


def log_api_call(logger: logging.Logger, service: str, endpoint: str, response_data: Dict[str, Any]):
    """
    Loga chamadas de API de forma estruturada
    
    Args:
        logger: Logger a ser usado
        service: Nome do serviço (ex: 'Z-API', 'Meta')
        endpoint: Endpoint chamado
        response_data: Dados da resposta
    """
    status = response_data.get('status', 'unknown')
    
    # Mascara dados sensíveis na resposta
    safe_response = {
        k: mask_sensitive_data(str(v)) if isinstance(v, str) else v
        for k, v in response_data.items()
    }
    
    logger.info(
        f"API Call - Service: {service} | Endpoint: {endpoint} | Status: {status}",
        extra={'response': safe_response}
    )


def log_database_operation(logger: logging.Logger, operation: str, model: str, record_id: Any = None):
    """
    Loga operações de banco de dados
    
    Args:
        logger: Logger a ser usado
        operation: Tipo de operação (CREATE, UPDATE, DELETE, READ)
        model: Nome do modelo
        record_id: ID do registro (se aplicável)
    """
    message = f"DB Operation - {operation} on {model}"
    if record_id:
        message += f" (ID: {record_id})"
    
    logger.info(message)
