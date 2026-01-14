"""
Middleware Flask para gerenciar Tenant ID automaticamente
Injeta tenant_id em todas as operações do banco
"""
from flask import g, request, abort, jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Middleware que gerencia o contexto do tenant na aplicação
    
    Responsabilidades:
    - Identifica o tenant do usuário logado
    - Seta tenant_id no PostgreSQL session
    - Valida permissões de acesso
    - Registra audit logs
    """
    
    def __init__(self, app=None, db_manager=None):
        """
        Inicializa o middleware
        
        Args:
            app: Instância Flask
            db_manager: Instância de MultiTenantDatabase
        """
        self.app = app
        self.db_manager = db_manager
        
        if app and db_manager:
            self.init_app(app, db_manager)
    
    def init_app(self, app, db_manager):
        """Registra o middleware na aplicação Flask"""
        self.app = app
        self.db_manager = db_manager
        
        # Hooks do Flask
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)
        
        logger.info("TenantMiddleware inicializado")
    
    def _before_request(self):
        """
        Executado ANTES de cada request
        Configura tenant_id e sessão do banco
        """
        from flask_login import current_user
        
        # Rotas públicas que não precisam de tenant
        public_routes = ['/login', '/register', '/health', '/static']
        if any(request.path.startswith(route) for route in public_routes):
            return
        
        # Pega tenant_id do usuário
        tenant_id = self._get_tenant_id()
        
        if tenant_id is None:
            # Usuário não autenticado ou sem tenant
            g.tenant_id = None
            g.db_session = None
            return
        
        # Valida se tenant está ativo
        if not self._validate_tenant(tenant_id):
            abort(403, description="Tenant inativo ou suspenso")
        
        # Configura sessão do banco com tenant_id
        try:
            g.tenant_id = tenant_id
            g.db_session = self.db_manager.get_session(tenant_id)
            
            # Informações adicionais
            g.tenant_slug = self._get_tenant_slug(tenant_id)
            
            logger.debug(f"Request: tenant_id={tenant_id}, path={request.path}")
            
        except Exception as e:
            logger.error(f"Erro ao configurar tenant: {e}")
            abort(500, description="Erro ao configurar contexto do tenant")
    
    def _after_request(self, response):
        """
        Executado DEPOIS de cada request
        Adiciona headers e registra audit log
        """
        # Adiciona tenant_id no header da resposta (útil para debug)
        if hasattr(g, 'tenant_id') and g.tenant_id:
            response.headers['X-Tenant-ID'] = str(g.tenant_id)
        
        # Registra audit log para operações importantes
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            self._log_audit()
        
        return response
    
    def _teardown_request(self, exception=None):
        """
        Executado no FINAL do request (sempre)
        Fecha sessão do banco e limpa recursos
        """
        session = g.pop('db_session', None)
        
        if session:
            try:
                if exception:
                    logger.warning(f"Request com exception, rollback na sessão")
                    session.rollback()
                else:
                    session.commit()
            except Exception as e:
                logger.error(f"Erro no teardown: {e}")
                session.rollback()
            finally:
                session.close()
    
    def _get_tenant_id(self):
        """
        Identifica o tenant_id do usuário logado
        
        Estratégias (em ordem de prioridade):
        1. Header HTTP (para APIs)
        2. Subdomain (ex: cliente1.seucrm.com)
        3. current_user.tenant_id
        4. Session
        
        Returns:
            int: tenant_id ou None
        """
        from flask_login import current_user
        
        # 1. Header HTTP (para APIs/mobile)
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                return int(tenant_id)
            except ValueError:
                logger.warning(f"X-Tenant-ID inválido: {tenant_id}")
        
        # 2. Subdomain (ex: cliente1.seucrm.com -> tenant_id)
        subdomain = self._get_subdomain()
        if subdomain:
            tenant_id = self._subdomain_to_tenant_id(subdomain)
            if tenant_id:
                return tenant_id
        
        # 3. Usuário logado
        if current_user.is_authenticated:
            # Se for admin, pode estar vendo outro tenant
            if hasattr(current_user, 'viewing_tenant_id') and current_user.viewing_tenant_id:
                return current_user.viewing_tenant_id
            
            # Usuário normal
            if hasattr(current_user, 'tenant_id'):
                return current_user.tenant_id
            
            # Se for colaborador, pega tenant do admin
            if hasattr(current_user, 'get_tenant_id'):
                return current_user.get_tenant_id()
        
        # 4. Session (fallback)
        return g.get('tenant_id', None)
    
    def _get_subdomain(self):
        """
        Extrai subdomain da URL
        
        Ex: cliente1.seucrm.com -> "cliente1"
        
        Returns:
            str: subdomain ou None
        """
        host = request.host.split(':')[0]  # Remove porta
        parts = host.split('.')
        
        # Precisa ter pelo menos 3 partes (subdomain.domain.tld)
        if len(parts) >= 3:
            # Ignora www
            subdomain = parts[0]
            if subdomain != 'www':
                return subdomain
        
        return None
    
    def _subdomain_to_tenant_id(self, subdomain):
        """
        Converte subdomain em tenant_id
        Busca no banco de dados
        
        Args:
            subdomain: String do subdomain
            
        Returns:
            int: tenant_id ou None
        """
        try:
            from models import Tenant
            
            # Usa uma sessão temporária SEM tenant_id
            # (tabela tenants não tem RLS)
            with self.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(
                    text("SELECT id FROM tenants WHERE slug = :slug AND ativo = true"),
                    {"slug": subdomain}
                ).fetchone()
                
                if result:
                    return result[0]
        
        except Exception as e:
            logger.error(f"Erro ao buscar tenant por subdomain: {e}")
        
        return None
    
    def _validate_tenant(self, tenant_id):
        """
        Valida se o tenant está ativo e pode acessar o sistema
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            from models import Tenant
            
            with self.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(
                    text("""
                        SELECT ativo, data_trial_fim 
                        FROM tenants 
                        WHERE id = :tenant_id
                    """),
                    {"tenant_id": tenant_id}
                ).fetchone()
                
                if not result:
                    logger.warning(f"Tenant {tenant_id} não encontrado")
                    return False
                
                ativo, data_trial_fim = result
                
                # Verifica se está ativo
                if not ativo:
                    logger.warning(f"Tenant {tenant_id} inativo")
                    return False
                
                # Verifica trial expirado
                if data_trial_fim:
                    from datetime import datetime
                    if datetime.now() > data_trial_fim:
                        logger.warning(f"Tenant {tenant_id} com trial expirado")
                        return False
                
                return True
        
        except Exception as e:
            logger.error(f"Erro ao validar tenant: {e}")
            return False
    
    def _get_tenant_slug(self, tenant_id):
        """
        Busca o slug do tenant
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            str: slug do tenant
        """
        try:
            with self.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(
                    text("SELECT slug FROM tenants WHERE id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).fetchone()
                
                if result:
                    return result[0]
        except:
            pass
        
        return None
    
    def _log_audit(self):
        """
        Registra operação no audit log
        """
        from flask_login import current_user
        
        if not hasattr(g, 'tenant_id') or not g.tenant_id:
            return
        
        try:
            with self.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                
                usuario_id = current_user.id if current_user.is_authenticated else None
                
                conn.execute(
                    text("""
                        INSERT INTO audit_logs 
                        (tenant_id, usuario_id, acao, ip_address, user_agent)
                        VALUES (:tenant_id, :usuario_id, :acao, :ip, :user_agent)
                    """),
                    {
                        "tenant_id": g.tenant_id,
                        "usuario_id": usuario_id,
                        "acao": f"{request.method} {request.path}",
                        "ip": request.remote_addr,
                        "user_agent": request.headers.get('User-Agent', '')[:200]
                    }
                )
                conn.commit()
        
        except Exception as e:
            logger.error(f"Erro ao registrar audit log: {e}")


# ========================================
# DECORATORS ÚTEIS
# ========================================

def require_tenant(f):
    """
    Decorator que garante que a rota tem um tenant_id válido
    
    Uso:
        @app.route('/leads')
        @require_tenant
        def list_leads():
            # g.tenant_id está garantido aqui
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_id') or g.tenant_id is None:
            abort(401, description="Autenticação necessária")
        return f(*args, **kwargs)
    return decorated_function


def admin_only(f):
    """
    Decorator que permite acesso apenas para admins
    
    Uso:
        @app.route('/admin/dashboard')
        @admin_only
        def admin_dashboard():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            abort(401, description="Autenticação necessária")
        
        if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
            abort(403, description="Acesso restrito a administradores")
        
        return f(*args, **kwargs)
    return decorated_function


def tenant_rate_limit(max_requests=100, window_seconds=60):
    """
    Rate limiting por tenant
    
    Uso:
        @app.route('/api/leads')
        @tenant_rate_limit(max_requests=100, window_seconds=60)
        def list_leads():
            pass
    """
    from functools import wraps
    from collections import defaultdict
    from time import time
    
    # Cache de requisições por tenant
    request_counts = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant_id') or not g.tenant_id:
                return f(*args, **kwargs)
            
            tenant_id = g.tenant_id
            now = time()
            
            # Remove requisições antigas
            request_counts[tenant_id] = [
                req_time for req_time in request_counts[tenant_id]
                if now - req_time < window_seconds
            ]
            
            # Verifica limite
            if len(request_counts[tenant_id]) >= max_requests:
                abort(429, description="Taxa de requisições excedida. Tente novamente em breve.")
            
            # Registra requisição
            request_counts[tenant_id].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ========================================
# HELPER FUNCTIONS
# ========================================

def get_current_tenant_id():
    """
    Retorna o tenant_id do contexto atual
    
    Returns:
        int: tenant_id ou None
    """
    return getattr(g, 'tenant_id', None)


def get_db_session():
    """
    Retorna a sessão do banco do tenant atual
    
    Returns:
        Session: Sessão SQLAlchemy
    
    Raises:
        RuntimeError: Se sessão não está configurada
    """
    if not hasattr(g, 'db_session') or g.db_session is None:
        raise RuntimeError("Sessão do banco não configurada")
    
    return g.db_session


def switch_tenant(tenant_id):
    """
    Troca o tenant do contexto atual (apenas para admins)
    
    Args:
        tenant_id: ID do tenant para acessar
    
    Raises:
        PermissionError: Se usuário não é admin
    """
    from flask_login import current_user
    
    if not current_user.is_authenticated:
        raise PermissionError("Usuário não autenticado")
    
    if not hasattr(current_user, 'tipo') or current_user.tipo != 'admin':
        raise PermissionError("Apenas admins podem trocar de tenant")
    
    # Fecha sessão atual
    if hasattr(g, 'db_session') and g.db_session:
        g.db_session.close()
    
    # Seta novo tenant
    from app_connection_rls import db
    g.tenant_id = tenant_id
    g.db_session = db.get_session(tenant_id)
    
    logger.info(f"Admin {current_user.id} trocou para tenant {tenant_id}")


# ========================================
# EXEMPLO DE USO COMPLETO
# ========================================

"""
# app.py

from flask import Flask
from app_connection_rls import MultiTenantDatabase
from middleware_tenant import TenantMiddleware, require_tenant

app = Flask(__name__)

# Inicializa database
db = MultiTenantDatabase("postgresql://app_user:senha@localhost/crm_saas")

# Inicializa middleware
tenant_middleware = TenantMiddleware(app, db)

@app.route('/api/leads')
@require_tenant
def list_leads():
    from models import Lead
    session = get_db_session()
    
    # RLS garante isolamento automático
    leads = session.query(Lead).all()
    
    return jsonify([{'id': l.id, 'nome': l.nome} for l in leads])

if __name__ == '__main__':
    app.run()
"""
