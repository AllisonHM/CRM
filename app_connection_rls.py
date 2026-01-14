"""
Conexão PostgreSQL Multi-Tenant com RLS
Gerencia o tenant_id na sessão do PostgreSQL automaticamente
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class MultiTenantDatabase:
    """
    Gerenciador de conexão multi-tenant com PostgreSQL RLS
    
    Uso:
        db = MultiTenantDatabase("postgresql://app_user:senha@localhost/crm_saas")
        
        with db.session_scope(tenant_id=5) as session:
            leads = session.query(Lead).all()  # RLS filtra automaticamente
    """
    
    def __init__(self, database_url, pool_size=20, max_overflow=40):
        """
        Inicializa conexão com PostgreSQL
        
        Args:
            database_url: URL de conexão (ex: postgresql://user:pass@host/db)
            pool_size: Tamanho do pool de conexões
            max_overflow: Conexões adicionais permitidas
        """
        # Cria engine com pool otimizado
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verifica conexão antes de usar
            pool_recycle=3600,   # Recicla conexões após 1 hora
            echo=False           # Set True para debug SQL
        )
        
        # Session factory
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
        # Registra listener para setar tenant_id
        self._register_tenant_listener()
        
        logger.info("Database multi-tenant inicializado")
    
    def _register_tenant_listener(self):
        """
        Registra listener que seta tenant_id ao iniciar conexão
        """
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Executado quando uma nova conexão é criada"""
            logger.debug(f"Nova conexão PostgreSQL criada: {id(dbapi_conn)}")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """
            Executado quando uma conexão é pega do pool
            Garante que tenant_id é resetado
            """
            # Reset tenant_id (por segurança)
            cursor = dbapi_conn.cursor()
            cursor.execute("SET app.current_tenant = NULL")
            cursor.close()
    
    def set_tenant(self, session, tenant_id):
        """
        Define o tenant_id na sessão PostgreSQL
        RLS usa esse valor para filtrar automaticamente
        
        Args:
            session: Sessão SQLAlchemy
            tenant_id: ID do tenant
        """
        if tenant_id is None:
            raise ValueError("tenant_id não pode ser None")
        
        try:
            # Seta tenant_id na sessão PostgreSQL
            session.execute(
                text("SET LOCAL app.current_tenant = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            logger.debug(f"Tenant {tenant_id} setado na sessão")
        except Exception as e:
            logger.error(f"Erro ao setar tenant_id: {e}")
            raise
    
    @contextmanager
    def session_scope(self, tenant_id):
        """
        Context manager para operações com tenant específico
        
        Uso:
            with db.session_scope(tenant_id=5) as session:
                lead = Lead(nome="Novo Lead")
                session.add(lead)
                # Commit automático ao sair do with
        
        Args:
            tenant_id: ID do tenant
            
        Yields:
            session: Sessão SQLAlchemy com tenant_id setado
        """
        session = self.Session()
        
        try:
            # Seta tenant_id
            self.set_tenant(session, tenant_id)
            
            # Yield da sessão para uso
            yield session
            
            # Commit se tudo ok
            session.commit()
            
        except Exception as e:
            # Rollback em caso de erro
            session.rollback()
            logger.error(f"Erro na transação (tenant {tenant_id}): {e}")
            raise
            
        finally:
            # Sempre fecha a sessão
            session.close()
    
    def get_session(self, tenant_id):
        """
        Retorna uma sessão com tenant_id já setado
        ATENÇÃO: Você é responsável por fazer commit/rollback/close
        
        Uso:
            session = db.get_session(tenant_id=5)
            try:
                leads = session.query(Lead).all()
                session.commit()
            finally:
                session.close()
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            session: Sessão SQLAlchemy
        """
        session = self.Session()
        self.set_tenant(session, tenant_id)
        return session
    
    def verify_tenant_isolation(self, tenant1_id, tenant2_id):
        """
        Testa se RLS está funcionando corretamente
        Garante que tenant1 não vê dados do tenant2
        
        Args:
            tenant1_id: ID do primeiro tenant
            tenant2_id: ID do segundo tenant
            
        Returns:
            dict: Resultado dos testes
        """
        from models import Lead  # Import aqui para evitar circular
        
        results = {
            'passed': True,
            'tests': []
        }
        
        try:
            # Teste 1: Inserir como tenant1
            with self.session_scope(tenant1_id) as session:
                test_lead = Lead(
                    tenant_id=tenant1_id,
                    nome="Test Lead Tenant 1",
                    email=f"test_{tenant1_id}@test.com"
                )
                session.add(test_lead)
                session.commit()
                
                count1 = session.query(Lead).count()
                
                results['tests'].append({
                    'name': 'Insert as Tenant 1',
                    'passed': count1 >= 1,
                    'message': f"Tenant {tenant1_id} vê {count1} lead(s)"
                })
            
            # Teste 2: Verificar que tenant2 NÃO vê dados do tenant1
            with self.session_scope(tenant2_id) as session:
                # Busca apenas por email (sem filtro de tenant_id)
                # RLS deve bloquear
                lead_tenant2 = session.query(Lead).filter_by(
                    email=f"test_{tenant1_id}@test.com"
                ).first()
                
                test_passed = lead_tenant2 is None
                
                results['tests'].append({
                    'name': 'Isolation Test',
                    'passed': test_passed,
                    'message': f"Tenant {tenant2_id} {'NÃO' if test_passed else 'CONSEGUIU'} ver dados do tenant {tenant1_id}"
                })
                
                if not test_passed:
                    results['passed'] = False
            
            # Limpeza: Remove lead de teste
            with self.session_scope(tenant1_id) as session:
                session.query(Lead).filter_by(
                    email=f"test_{tenant1_id}@test.com"
                ).delete()
                session.commit()
            
        except Exception as e:
            results['passed'] = False
            results['error'] = str(e)
            logger.error(f"Erro no teste de isolamento: {e}")
        
        return results
    
    def health_check(self):
        """
        Verifica se a conexão com o banco está ok
        
        Returns:
            bool: True se conectado, False caso contrário
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False
    
    def get_pool_status(self):
        """
        Retorna status do pool de conexões
        
        Returns:
            dict: Informações do pool
        """
        pool = self.engine.pool
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total': pool.size() + pool.overflow()
        }


# ========================================
# EXEMPLO DE USO EM UMA APLICAÇÃO FLASK
# ========================================

from flask import Flask, g, request
from flask_login import current_user

app = Flask(__name__)

# Inicializa database
db = MultiTenantDatabase(
    database_url="postgresql://app_user:senha@localhost/crm_saas",
    pool_size=20
)


def get_current_tenant_id():
    """
    Retorna o tenant_id do usuário logado
    Customize conforme sua lógica de autenticação
    """
    if current_user.is_authenticated:
        # Se for admin, pode estar acessando outro tenant
        if hasattr(current_user, 'viewing_tenant_id'):
            return current_user.viewing_tenant_id
        
        # Usuário normal usa seu próprio tenant
        return current_user.tenant_id
    
    return None


@app.before_request
def setup_tenant_session():
    """
    Executado antes de cada request
    Configura a sessão do banco com o tenant correto
    """
    tenant_id = get_current_tenant_id()
    
    if tenant_id:
        # Cria sessão com tenant_id setado
        g.db_session = db.get_session(tenant_id)
        g.tenant_id = tenant_id
        logger.debug(f"Request com tenant_id={tenant_id}")
    else:
        g.db_session = None
        g.tenant_id = None


@app.teardown_request
def teardown_tenant_session(exception=None):
    """
    Executado após cada request
    Fecha a sessão do banco
    """
    session = g.pop('db_session', None)
    
    if session:
        try:
            if exception:
                session.rollback()
            else:
                session.commit()
        except Exception as e:
            logger.error(f"Erro no teardown: {e}")
            session.rollback()
        finally:
            session.close()


def get_db_session():
    """
    Helper para pegar a sessão do banco no request atual
    
    Uso nas rotas:
        session = get_db_session()
        leads = session.query(Lead).all()
    """
    if not hasattr(g, 'db_session') or g.db_session is None:
        raise RuntimeError("Sessão do banco não configurada. Usuário não autenticado?")
    
    return g.db_session


# ========================================
# EXEMPLO DE ROTAS
# ========================================

@app.route('/api/leads', methods=['GET'])
def list_leads():
    """Lista leads do tenant logado"""
    from models import Lead
    
    session = get_db_session()
    
    # RLS filtra automaticamente por tenant_id!
    leads = session.query(Lead).filter_by(deleted_at=None).all()
    
    return {
        'tenant_id': g.tenant_id,
        'leads': [{'id': l.id, 'nome': l.nome} for l in leads]
    }


@app.route('/api/leads', methods=['POST'])
def create_lead():
    """Cria novo lead para o tenant logado"""
    from models import Lead
    import json
    
    session = get_db_session()
    data = request.get_json()
    
    # tenant_id é setado automaticamente (ou pode ser explícito)
    novo_lead = Lead(
        tenant_id=g.tenant_id,  # Explícito (recomendado)
        nome=data['nome'],
        email=data.get('email'),
        telefone=data.get('telefone')
    )
    
    session.add(novo_lead)
    session.commit()
    
    return {'success': True, 'lead_id': novo_lead.id}, 201


@app.route('/api/admin/tenants/<int:tenant_id>/stats')
def admin_tenant_stats(tenant_id):
    """Admin pode ver stats de qualquer tenant"""
    from models import Lead, Oportunidade
    
    # Admin usa sessão específica do tenant
    with db.session_scope(tenant_id) as session:
        total_leads = session.query(Lead).count()
        total_oportunidades = session.query(Oportunidade).count()
    
    return {
        'tenant_id': tenant_id,
        'total_leads': total_leads,
        'total_oportunidades': total_oportunidades
    }


@app.route('/health')
def health():
    """Verifica saúde do sistema"""
    db_ok = db.health_check()
    pool_status = db.get_pool_status()
    
    return {
        'status': 'healthy' if db_ok else 'unhealthy',
        'database': 'connected' if db_ok else 'disconnected',
        'pool': pool_status
    }


if __name__ == '__main__':
    # Testa isolamento ao iniciar
    print("\n🧪 Testando isolamento de tenants...\n")
    
    result = db.verify_tenant_isolation(tenant1_id=1, tenant2_id=2)
    
    for test in result['tests']:
        emoji = "✅" if test['passed'] else "❌"
        print(f"{emoji} {test['name']}: {test['message']}")
    
    print(f"\n{'✅ Todos os testes passaram!' if result['passed'] else '❌ Alguns testes falharam!'}\n")
    
    # Inicia app
    app.run(debug=True)
