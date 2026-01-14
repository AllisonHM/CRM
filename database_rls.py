# database_rls.py
"""
Gerenciador de conexão multi-tenant com PostgreSQL RLS
Versão adaptada para o CRM
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from flask import g
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy instance (para tabelas globais como UsuarioCRM)
db = SQLAlchemy()


class TenantDatabaseManager:
    """
    Gerencia sessões com tenant_id para RLS
    Integrado com Flask-SQLAlchemy
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa com a aplicação Flask"""
        self.app = app
        
        # Registra hooks do Flask
        app.before_request(self._before_request)
        app.teardown_appcontext(self._teardown_request)
        
        logger.info("TenantDatabaseManager inicializado")
    
    def _before_request(self):
        """Seta tenant_id na sessão antes de cada request"""
        from flask_login import current_user
        
        # Rotas públicas que não precisam de tenant
        from flask import request
        public_routes = ['/login', '/logout', '/register', '/health', '/static']
        if any(request.path.startswith(route) for route in public_routes):
            g.tenant_id = None
            return
        
        # Pega tenant_id do usuário
        if current_user.is_authenticated:
            tenant_id = current_user.get_usuario_principal_id()
            g.tenant_id = tenant_id
            
            # Seta na sessão PostgreSQL
            self._set_tenant_id(tenant_id)
        else:
            g.tenant_id = None
    
    def _set_tenant_id(self, tenant_id):
        """Seta tenant_id na sessão PostgreSQL para RLS"""
        if tenant_id is None:
            return
        
        try:
            db.session.execute(
                text("SET LOCAL app.current_tenant = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            logger.debug(f"Tenant {tenant_id} setado na sessão")
        except Exception as e:
            logger.error(f"Erro ao setar tenant_id: {e}")
    
    def _teardown_request(self, exception=None):
        """Limpa recursos ao final do request"""
        # Flask-SQLAlchemy já gerencia a sessão
        g.pop('tenant_id', None)
    
    @contextmanager
    def tenant_context(self, tenant_id):
        """
        Context manager para operações com tenant específico
        
        Uso:
            with tenant_db.tenant_context(5):
                clientes = Cliente.query.all()
        """
        old_tenant = g.get('tenant_id')
        
        try:
            g.tenant_id = tenant_id
            self._set_tenant_id(tenant_id)
            yield
        finally:
            g.tenant_id = old_tenant
            if old_tenant:
                self._set_tenant_id(old_tenant)


# Instância global
tenant_db = TenantDatabaseManager()


def get_current_tenant_id():
    """Retorna o tenant_id do contexto atual"""
    return getattr(g, 'tenant_id', None)


def init_db(app):
    """Inicializa banco de dados com suporte a RLS"""
    db.init_app(app)
    tenant_db.init_app(app)
    
    # Cria tabelas
    with app.app_context():
        db.create_all()
