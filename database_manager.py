# database_manager.py
"""
Gerenciador de Múltiplos Bancos de Dados
Cada cliente (UsuarioCRM admin) tem seu próprio banco PostgreSQL
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from contextlib import contextmanager
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Banco de dados central (para autenticação e controle)
db_central = SQLAlchemy()

class DatabaseManager:
    """Gerencia conexões dinâmicas com múltiplos bancos de dados"""
    
    def __init__(self):
        self.engines = {}  # Cache de engines por usuario_crm_id
        self.sessions = {}  # Cache de sessões
        
        # Configuração base do PostgreSQL
        self.pg_host = 'localhost'
        self.pg_port = 1222
        self.pg_user = 'postgres'
        self.pg_password = 'Amovoce123@'
        
    def get_database_name(self, usuario_crm_id):
        """Retorna o nome do banco de dados para um cliente específico"""
        return f"crm_cliente_{usuario_crm_id}"
    
    def get_connection_string(self, db_name):
        """Gera a string de conexão para um banco específico"""
        return f"postgresql+psycopg2://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{db_name}"
    
    def criar_banco_cliente(self, usuario_crm_id, usuario_nome=""):
        """
        Cria um novo banco de dados PostgreSQL para um cliente
        
        Args:
            usuario_crm_id: ID do UsuarioCRM (admin)
            usuario_nome: Nome do usuário (para logging)
            
        Returns:
            tuple: (sucesso: bool, mensagem: str)
        """
        db_name = self.get_database_name(usuario_crm_id)
        
        try:
            # Conecta ao postgres para criar o novo banco
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Verifica se o banco já existe
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return False, f"Banco {db_name} já existe"
            
            # Cria o banco
            cursor.execute(f'CREATE DATABASE "{db_name}" ENCODING "UTF8"')
            cursor.close()
            conn.close()
            
            # Inicializa as tabelas no novo banco
            self._inicializar_tabelas(db_name)
            
            print(f"✅ Banco criado: {db_name} (Cliente: {usuario_nome})")
            return True, f"Banco {db_name} criado com sucesso"
            
        except Exception as e:
            print(f"❌ Erro ao criar banco {db_name}: {str(e)}")
            return False, f"Erro ao criar banco: {str(e)}"
    
    def _inicializar_tabelas(self, db_name):
        """Cria todas as tabelas necessárias no banco do cliente"""
        from models import Cliente, MesaNegocio, Ocorrencia, WhatsAppMensagem, ChatbotRegra, Produto, Movimentacao, PlannerEvento
        
        engine = create_engine(self.get_connection_string(db_name))
        
        # Importa metadata e cria tabelas (exceto UsuarioCRM que fica no central)
        from database import db
        Cliente.__table__.create(engine, checkfirst=True)
        MesaNegocio.__table__.create(engine, checkfirst=True)
        Ocorrencia.__table__.create(engine, checkfirst=True)
        WhatsAppMensagem.__table__.create(engine, checkfirst=True)
        ChatbotRegra.__table__.create(engine, checkfirst=True)
        Produto.__table__.create(engine, checkfirst=True)
        Movimentacao.__table__.create(engine, checkfirst=True)
        PlannerEvento.__table__.create(engine, checkfirst=True)
        
        print(f"  📊 Tabelas criadas em {db_name}")
    
    def get_engine(self, usuario_crm_id):
        """Retorna ou cria um engine para o banco do cliente"""
        if usuario_crm_id not in self.engines:
            db_name = self.get_database_name(usuario_crm_id)
            connection_string = self.get_connection_string(db_name)
            self.engines[usuario_crm_id] = create_engine(connection_string, pool_pre_ping=True)
        
        return self.engines[usuario_crm_id]
    
    def get_session(self, usuario_crm_id):
        """Retorna uma sessão para o banco do cliente"""
        engine = self.get_engine(usuario_crm_id)
        Session = scoped_session(sessionmaker(bind=engine))
        return Session()
    
    @contextmanager
    def session_scope(self, usuario_crm_id):
        """
        Context manager para gerenciar sessões de banco
        
        Uso:
            with db_manager.session_scope(usuario_id) as session:
                cliente = session.query(Cliente).filter_by(id=1).first()
        """
        session = self.get_session(usuario_crm_id)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def excluir_banco_cliente(self, usuario_crm_id):
        """
        Remove o banco de dados de um cliente (usar com CUIDADO!)
        
        Args:
            usuario_crm_id: ID do cliente
            
        Returns:
            tuple: (sucesso: bool, mensagem: str)
        """
        db_name = self.get_database_name(usuario_crm_id)
        
        try:
            # Remove engine do cache
            if usuario_crm_id in self.engines:
                self.engines[usuario_crm_id].dispose()
                del self.engines[usuario_crm_id]
            
            # Conecta ao postgres para dropar o banco
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Encerra conexões ativas
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid()
            """)
            
            # Dropa o banco
            cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            cursor.close()
            conn.close()
            
            print(f"🗑️ Banco removido: {db_name}")
            return True, f"Banco {db_name} removido"
            
        except Exception as e:
            print(f"❌ Erro ao remover banco {db_name}: {str(e)}")
            return False, f"Erro: {str(e)}"
    
    def listar_bancos_clientes(self):
        """Lista todos os bancos de clientes criados"""
        try:
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                user=self.pg_user,
                password=self.pg_password,
                database='postgres'
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT datname 
                FROM pg_database 
                WHERE datname LIKE 'crm_cliente_%'
                ORDER BY datname
            """)
            
            bancos = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            return bancos
            
        except Exception as e:
            print(f"❌ Erro ao listar bancos: {str(e)}")
            return []
    
    def migrar_banco_cliente(self, usuario_crm_id):
        """
        Executa migrações/atualizações em um banco específico
        Útil quando adiciona novas tabelas ou colunas
        """
        try:
            self._inicializar_tabelas(self.get_database_name(usuario_crm_id))
            return True, "Migração concluída"
        except Exception as e:
            return False, f"Erro na migração: {str(e)}"

# Instância global do gerenciador
db_manager = DatabaseManager()
