"""
Exception Handling - Tratamento centralizado de exceções
"""
import logging
from typing import Tuple, Dict, Any
from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .validators import ValidationError

logger = logging.getLogger(__name__)


# ==================== EXCEÇÕES CUSTOMIZADAS ====================

class CRMException(Exception):
    """Exceção base do CRM"""
    def __init__(self, message: str, status_code: int = 500, payload: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


class DatabaseError(CRMException):
    """Erro relacionado ao banco de dados"""
    def __init__(self, message: str = "Erro ao acessar banco de dados", original_error: Exception = None):
        super().__init__(message, status_code=500)
        self.original_error = original_error


class ExternalAPIError(CRMException):
    """Erro ao comunicar com API externa"""
    def __init__(self, service: str, message: str = "Erro ao comunicar com serviço externo", status_code: int = 503):
        super().__init__(f"{service}: {message}", status_code=status_code)
        self.service = service


class PermissionDeniedError(CRMException):
    """Erro de permissão"""
    def __init__(self, message: str = "Você não tem permissão para realizar esta ação"):
        super().__init__(message, status_code=403)


class ResourceNotFoundError(CRMException):
    """Recurso não encontrado"""
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} não encontrado"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, status_code=404)


# ==================== HANDLERS ====================

def handle_exception(error: Exception) -> Tuple[Dict[str, Any], int]:
    """
    Handler centralizado de exceções
    
    Args:
        error: Exceção capturada
    
    Returns:
        Tupla (resposta_json, status_code)
    """
    
    # Exceções customizadas do CRM
    if isinstance(error, CRMException):
        logger.warning(f"CRM Exception: {error.message}", exc_info=True)
        return jsonify({
            "erro": error.message,
            "tipo": error.__class__.__name__,
            **error.payload
        }), error.status_code
    
    # Erros de validação
    if isinstance(error, ValidationError):
        logger.info(f"Validation error: {error.field} - {error.message}")
        return jsonify({
            "erro": "Dados inválidos",
            "campo": error.field,
            "mensagem": error.message
        }), 422  # Unprocessable Entity
    
    # Erros HTTP do Werkzeug
    if isinstance(error, HTTPException):
        logger.warning(f"HTTP Exception: {error.code} - {error.description}")
        return jsonify({
            "erro": error.description or "Erro HTTP",
            "codigo": error.code
        }), error.code or 500
    
    # Erros de integridade do banco
    if isinstance(error, IntegrityError):
        logger.error("Database integrity error", exc_info=True)
        
        # Tentar identificar a constraint violada
        error_msg = str(error.orig) if hasattr(error, 'orig') else str(error)
        
        if 'unique' in error_msg.lower():
            return jsonify({
                "erro": "Registro duplicado. Já existe um registro com estes dados.",
                "tipo": "IntegrityError"
            }), 409  # Conflict
        elif 'foreign key' in error_msg.lower():
            return jsonify({
                "erro": "Referência inválida. Verifique os dados relacionados.",
                "tipo": "IntegrityError"
            }), 422
        else:
            return jsonify({
                "erro": "Erro de integridade no banco de dados",
                "tipo": "IntegrityError"
            }), 422
    
    # Outros erros do SQLAlchemy
    if isinstance(error, SQLAlchemyError):
        logger.error("Database error", exc_info=True)
        return jsonify({
            "erro": "Erro ao acessar o banco de dados",
            "tipo": "DatabaseError"
        }), 500
    
    # Erros genéricos (não expor detalhes em produção)
    logger.error(f"Unhandled exception: {type(error).__name__}", exc_info=True)
    
    # Em desenvolvimento, pode expor mais detalhes
    import os
    if os.getenv('FLASK_ENV') == 'development':
        return jsonify({
            "erro": "Erro interno do servidor",
            "tipo": type(error).__name__,
            "detalhes": str(error)
        }), 500
    else:
        # Em produção, mensagem genérica
        return jsonify({
            "erro": "Erro interno do servidor. Tente novamente mais tarde.",
            "tipo": "InternalServerError"
        }), 500


def safe_commit(db_session, operation_name: str = "operação"):
    """
    Context manager para commit seguro com rollback automático
    
    Usage:
        with safe_commit(db.session, "criar cliente"):
            db.session.add(cliente)
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _safe_commit():
        try:
            yield
            db_session.commit()
            logger.info(f"Commit successful: {operation_name}")
        except Exception as e:
            db_session.rollback()
            logger.error(f"Rollback executed for {operation_name}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Erro ao executar {operation_name}", original_error=e)
    
    return _safe_commit()
