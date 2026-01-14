# models_central.py
"""
Modelos para o Banco Central (autenticação e controle)
Apenas UsuarioCRM fica aqui
"""
from database_manager import db_central
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class UsuarioCRM(UserMixin, db_central.Model):
    """
    Representa cada instância/cliente do CRM
    Armazenado no BANCO CENTRAL
    """
    __tablename__ = 'usuario_crm'
    __bind_key__ = 'central'  # Indica que vai no banco central
    
    id = db_central.Column(db_central.Integer, primary_key=True)
    nome = db_central.Column(db_central.String(200), nullable=False)
    email = db_central.Column(db_central.String(200), nullable=False, unique=True)
    senha_hash = db_central.Column(db_central.String(255), nullable=False)
    numero_whatsapp = db_central.Column(db_central.String(50), nullable=True)
    
    # Credenciais da API Z-API
    api_instance = db_central.Column(db_central.String(255), nullable=True)
    api_token = db_central.Column(db_central.String(255), nullable=True)
    
    dias_quarentena_nps = db_central.Column(db_central.Integer, default=30)
    
    # Hierarquia de usuários
    tipo_usuario = db_central.Column(db_central.String(20), nullable=False, default='colaborador')
    usuario_pai_id = db_central.Column(db_central.Integer, db_central.ForeignKey('usuario_crm.id'), nullable=True)
    
    # Nome do banco de dados específico deste cliente
    database_name = db_central.Column(db_central.String(100), nullable=True)  # Ex: crm_cliente_1
    database_criado = db_central.Column(db_central.Boolean, default=False)
    
    # Permissões
    permissoes = db_central.Column(db_central.JSON, nullable=True)
    
    ativo = db_central.Column(db_central.Boolean, default=True)
    data_cadastro = db_central.Column(db_central.DateTime, default=datetime.utcnow)
    
    # Relacionamentos (só para navegação)
    colaboradores = db_central.relationship('UsuarioCRM', 
                                           backref=db_central.backref('usuario_pai', remote_side=[id]), 
                                           lazy=True)
    
    def set_password(self, senha):
        """Define a senha do usuário (hash)"""
        self.senha_hash = generate_password_hash(senha)
    
    def check_password(self, senha):
        """Verifica se a senha está correta"""
        return check_password_hash(self.senha_hash, senha)
    
    def tem_permissao(self, modulo):
        """Verifica se o usuário tem permissão para acessar um módulo"""
        if self.tipo_usuario == 'super_admin':
            return True
        if self.tipo_usuario == 'admin':
            return True
        if self.permissoes and isinstance(self.permissoes, dict):
            return self.permissoes.get(modulo, False)
        return False
    
    def get_usuario_principal_id(self):
        """Retorna o ID do usuário principal (admin)"""
        if self.tipo_usuario in ['super_admin', 'admin']:
            return self.id
        return self.usuario_pai_id if self.usuario_pai_id else self.id
    
    def tem_api_configurada(self):
        """Verifica se tem API configurada"""
        return bool(self.api_instance and self.api_token)
    
    def get_database_name(self):
        """Retorna o nome do banco de dados deste cliente"""
        if not self.database_name:
            from database_manager import db_manager
            self.database_name = db_manager.get_database_name(self.get_usuario_principal_id())
        return self.database_name
