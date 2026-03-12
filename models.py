# models.py
from database_rls import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class UsuarioCRM(UserMixin, db.Model):
    """Representa cada instância/usuário do CRM com seu próprio número de WhatsApp"""
    __tablename__ = 'usuario_crm'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)  # Login
    senha_hash = db.Column(db.String(255), nullable=False)
    numero_whatsapp = db.Column(db.String(50), nullable=True)
    
    # Credenciais da API Z-API (configuradas pelo super_admin)
    api_instance = db.Column(db.String(255), nullable=True)  # Instance ID da Z-API
    api_token = db.Column(db.String(255), nullable=True)  # Token da API de WhatsApp
    
    dias_quarentena_nps = db.Column(db.Integer, default=30)  # Intervalo mínimo em dias para envio de NPS
    
    # Hierarquia de usuários
    tipo_usuario = db.Column(db.String(20), nullable=False, default='colaborador')  # super_admin, admin, colaborador
    usuario_pai_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)  # Admin do colaborador
    
    # Permissões (JSON com módulos permitidos)
    permissoes = db.Column(db.JSON, nullable=True)  # Ex: {"clientes": true, "produtos": false, ...}
    
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Recuperação de senha
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expira = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    clientes = db.relationship('Cliente', backref='usuario_crm', lazy=True, foreign_keys='Cliente.usuario_crm_id')
    colaboradores = db.relationship('UsuarioCRM', backref=db.backref('usuario_pai', remote_side=[id]), lazy=True)
    
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
        """Retorna o ID do usuário principal (admin ou próprio ID se for admin/super_admin)"""
        if self.tipo_usuario in ['super_admin', 'admin']:
            return self.id
        return self.usuario_pai_id if self.usuario_pai_id else self.id
    
    def tem_api_configurada(self):
        """Verifica se o usuário tem as credenciais da API Z-API configuradas"""
        return bool(self.api_instance and self.api_token)

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)  # Vincula cliente à instância do CRM
    nome = db.Column(db.String(100), nullable=False)
    tipo_pessoa = db.Column(db.String(50), nullable=False, default='Cliente')
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20), nullable=False)

    # Pessoa Física
    data_nascimento = db.Column(db.Date, nullable=True)
    renda = db.Column(db.Float, nullable=True)
    segmento_trabalho = db.Column(db.String(120), nullable=True)
    endereco = db.Column(db.String(200), nullable=True)

    # Pessoa Jurídica
    data_abertura = db.Column(db.Date, nullable=True)
    faturamento = db.Column(db.Float, nullable=True)
    segmento = db.Column(db.String(120), nullable=True)
    qtd_funcionarios = db.Column(db.Integer, nullable=True)

    # NPS (Net Promoter Score)
    nps_nota = db.Column(db.Integer, nullable=True)  # 0-10
    nps_data = db.Column(db.DateTime, nullable=True)
    nps_comentario = db.Column(db.Text, nullable=True)
    aguardando_nps = db.Column(db.Boolean, default=False)  # Flag para saber se está aguardando resposta
    data_ultimo_nps_envio = db.Column(db.DateTime, nullable=True)  # Data do último envio de solicitação NPS

    # Observações Gerais
    observacoes = db.Column(db.Text, nullable=True)  # Campo para anotações e observações gerais

    mesas = db.relationship('MesaNegocio', backref='cliente', lazy=True)
    ocorrencias = db.relationship('Ocorrencia', backref='cliente', lazy=True)

class MesaNegocio(db.Model):
    __tablename__ = 'mesa_negocio'

    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    topico = db.Column(db.String(150), nullable=False)
    produtos = db.Column(db.String(250), nullable=True)
    produtos_quantidades = db.Column(db.JSON, nullable=True)  # Armazena {produto_id: quantidade}
    valor_total = db.Column(db.Float, nullable=True)
    situacao = db.Column(db.String(50), nullable=False, default="Em negociação")
    descricao = db.Column(db.Text, nullable=True)
    data_registro = db.Column(db.Date, nullable=False)
    hora_registro = db.Column(db.Time, nullable=False)
    data_fechamento = db.Column(db.Date, nullable=True)

class Ocorrencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    topico = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_registro = db.Column(db.Date, nullable=False, default=datetime.today().date)
    hora_registro = db.Column(db.Time, nullable=False, default=datetime.now().time)

class WhatsAppMensagem(db.Model):
    __tablename__ = 'whatsapp_mensagem'
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)
    numero = db.Column(db.String(50), nullable=False)
    remetente = db.Column(db.String(100))  # <-- esta linha é obrigatória
    mensagem = db.Column(db.Text, nullable=False)
    recebido_em = db.Column(db.DateTime, nullable=False)
    # Campos de estado/mídia
    lida = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(30), nullable=True)   # enviado, entregue, lido, erro
    tipo_midia = db.Column(db.String(30), nullable=True)  # image, audio, video, document
    arquivo_url = db.Column(db.Text, nullable=True)

class ChatbotRegra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)
    palavra_chave = db.Column(db.String(50), nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(20), default="Normal")

# Modelo Produto
class Produto(db.Model):
    __tablename__ = "produto"
    __table_args__ = (
        db.UniqueConstraint('usuario_crm_id', 'nome', name='uq_produto_usuario_nome'),
    )
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    ultima_movimentacao_data = db.Column(db.DateTime, nullable=True)
    ultima_movimentacao_descricao = db.Column(db.String(255), nullable=True)

    movimentacoes = db.relationship("Movimentacao", back_populates="produto", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Produto {self.nome}>"

# Modelo Movimentacao
class Movimentacao(db.Model):
    __tablename__ = "movimentacao"
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id", ondelete="CASCADE"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
    quantidade = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.String(255), nullable=False)  # justificativa obrigatória
    data_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    produto = db.relationship("Produto", back_populates="movimentacoes")

    def __repr__(self):
        return f"<Movimentacao {self.tipo} {self.quantidade} produto_id={self.produto_id}>"
    
class PlannerEvento(db.Model):
    __tablename__ = "planner_evento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)  # agendamento, contato, periodo
    cliente = db.Column(db.String(120), nullable=True)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)  # <-- NOVO CAMPO
    descricao = db.Column(db.Text, nullable=True)


class Tarefa(db.Model):
    __tablename__ = "tarefa"

    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    mesa_negocio_id = db.Column(db.Integer, db.ForeignKey('mesa_negocio.id'), nullable=True)

    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    prioridade = db.Column(db.String(20), nullable=False, default="Normal")  # Baixa, Normal, Alta
    status = db.Column(db.String(20), nullable=False, default="Pendente")  # Pendente, Concluída

    data_vencimento = db.Column(db.Date, nullable=True)
    hora_vencimento = db.Column(db.Time, nullable=True)
    lembrete_em = db.Column(db.DateTime, nullable=True)
    lembrete_enviado = db.Column(db.Boolean, default=False)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    concluido_em = db.Column(db.DateTime, nullable=True)

    cliente = db.relationship('Cliente', backref='tarefas')
    mesa = db.relationship('MesaNegocio', backref='tarefas')


class ConfiguracaoUsuario(db.Model):
    """Configurações pessoais do usuário (tema, preferências, etc.)"""
    __tablename__ = 'configuracao_usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Preferências de interface
    tema = db.Column(db.String(20), default='claro')  # claro, escuro
    idioma = db.Column(db.String(10), default='pt-br')
    
    # Notificações
    notificacoes_email = db.Column(db.Boolean, default=True)
    notificacoes_sistema = db.Column(db.Boolean, default=True)
    
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    usuario = db.relationship('UsuarioCRM', backref=db.backref('configuracao', uselist=False, cascade='all, delete-orphan'))


class Parametrizacao(db.Model):
    """Parametrizações do sistema (mensagens automáticas, templates, etc.)"""
    __tablename__ = 'parametrizacao'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id', ondelete='CASCADE'), nullable=False)
    
    # Mensagens automáticas
    mensagem_boas_vindas = db.Column(db.Text, default='Olá! Bem-vindo ao nosso atendimento. Como posso ajudá-lo?')
    mensagem_ausencia = db.Column(db.Text, default='No momento estamos ausentes. Retornaremos em breve!')
    mensagem_encerramento = db.Column(db.Text, default='Obrigado pelo contato! Até breve.')
    mensagem_nps = db.Column(db.Text, default='Em uma escala de 0 a 10, o quanto você recomendaria nossos serviços?')
    
    # Configurações gerais
    horario_atendimento_inicio = db.Column(db.Time, nullable=True)
    horario_atendimento_fim = db.Column(db.Time, nullable=True)
    resposta_automatica_ativa = db.Column(db.Boolean, default=False)

    # Integração Meta Graph API (dados por cliente/tenant)
    meta_graph_access_token = db.Column(db.Text, nullable=True)
    meta_graph_verify_token = db.Column(db.String(255), nullable=True)
    meta_graph_app_id = db.Column(db.String(120), nullable=True)
    meta_graph_phone_number_id = db.Column(db.String(120), nullable=True)
    
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    usuario = db.relationship('UsuarioCRM', backref=db.backref('parametrizacoes', cascade='all, delete-orphan'))


class Fornecedor(db.Model):
    """Modelo para gerenciamento de fornecedores"""
    __tablename__ = 'fornecedor'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=True)
    
    # Dados básicos
    nome = db.Column(db.String(200), nullable=False)
    nome_fantasia = db.Column(db.String(200), nullable=True)
    cnpj_cpf = db.Column(db.String(20), nullable=True)
    inscricao_estadual = db.Column(db.String(50), nullable=True)
    
    # Contato
    email = db.Column(db.String(200), nullable=True)
    telefone = db.Column(db.String(50), nullable=True)
    celular = db.Column(db.String(50), nullable=True)
    site = db.Column(db.String(200), nullable=True)
    
    # Endereço
    cep = db.Column(db.String(10), nullable=True)
    logradouro = db.Column(db.String(200), nullable=True)
    numero = db.Column(db.String(20), nullable=True)
    complemento = db.Column(db.String(100), nullable=True)
    bairro = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    
    # Informações comerciais
    produtos_servicos = db.Column(db.Text, nullable=True)  # Produtos/serviços fornecidos
    prazo_entrega = db.Column(db.String(100), nullable=True)  # Prazo médio de entrega
    prazo_pagamento = db.Column(db.String(100), nullable=True)  # Condições de pagamento
    
    # Dados bancários
    banco = db.Column(db.String(100), nullable=True)
    agencia = db.Column(db.String(20), nullable=True)
    conta = db.Column(db.String(30), nullable=True)
    pix = db.Column(db.String(100), nullable=True)
    
    # Contato principal
    contato_nome = db.Column(db.String(100), nullable=True)
    contato_cargo = db.Column(db.String(100), nullable=True)
    contato_telefone = db.Column(db.String(50), nullable=True)
    contato_email = db.Column(db.String(200), nullable=True)
    
    # Avaliação e status
    avaliacao = db.Column(db.Integer, nullable=True)  # 1 a 5 estrelas
    status = db.Column(db.String(20), default='Ativo')  # Ativo, Inativo, Bloqueado
    observacoes = db.Column(db.Text, nullable=True)
    
    # Metadados
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Fornecedor {self.nome}>"


class FacebookPage(db.Model):
    """
    Páginas do Facebook e contas do Instagram Business conectadas
    por cada cliente/tenant via OAuth da Meta.
    Um mesmo usuário pode ter várias páginas; cada linha é uma página.
    """
    __tablename__ = 'facebook_pages'

    __table_args__ = (
        # Garante que a combinação (usuário + page_id) seja única
        # para permitir upsert sem duplicatas na reconexão.
        db.UniqueConstraint('usuario_crm_id', 'page_id', name='uq_fb_page_usuario'),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(
        db.Integer,
        db.ForeignKey('usuario_crm.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Identificação da página
    page_id = db.Column(db.String(100), nullable=False)
    page_name = db.Column(db.String(255), nullable=False)

    # Token de acesso específico da página (page_access_token)
    # Diferente do user_access_token — tem permissões limitadas à página
    page_access_token = db.Column(db.Text, nullable=False)

    # Instagram Business Account vinculado à página (pode ser NULL)
    instagram_id = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamento reverso no UsuarioCRM disponível como .facebook_pages
    usuario = db.relationship(
        'UsuarioCRM',
        backref=db.backref('facebook_pages', cascade='all, delete-orphan'),
    )

    def __repr__(self) -> str:
        insta = f" / IG:{self.instagram_id}" if self.instagram_id else ""
        return f"<FacebookPage {self.page_name}{insta}>"


class Conversation(db.Model):
    """
    Representa uma conversa entre um contato externo e uma das páginas do cliente.
    Uma mesma conversa agrupa todas as mensagens entre page_id e contact_id.
    """
    __tablename__ = 'conversations'

    __table_args__ = (
        # Índice composto para consultas ordenadas por recência (inbox)
        db.Index('ix_conv_usuario_last', 'usuario_crm_id', 'last_message_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(
        db.Integer,
        db.ForeignKey('usuario_crm.id', ondelete='CASCADE'),
        nullable=False,
    )
    page_id = db.Column(db.String(100), nullable=False)
    contact_id = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(20), nullable=False, default='facebook')  # 'facebook' | 'instagram'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship(
        'Message',
        backref='conversation',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='Message.created_at',
    )
    usuario = db.relationship(
        'UsuarioCRM',
        backref=db.backref('conversations', lazy=True),
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.platform}/{self.contact_id}>"


class Message(db.Model):
    """
    Mensagem individual dentro de uma Conversation.
    O campo platform_message_id garante deduplicação — a Meta pode reenviar
    o mesmo evento mais de uma vez; o UNIQUE constraint impede duplicatas.
    """
    __tablename__ = 'messages'

    __table_args__ = (
        db.Index('ix_msg_conv_created', 'conversation_id', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey('conversations.id', ondelete='CASCADE'),
        nullable=False,
    )
    # 'customer' = recebida do contato externo
    # 'agent'    = enviada pelo atendente pelo CRM
    # 'bot'      = enviada por automação
    sender_type = db.Column(db.String(20), nullable=False, default='customer')
    message_text = db.Column(db.Text, nullable=False)
    # ID da mensagem fornecido pela Meta – NULL para mensagens enviadas pelo agente
    platform_message_id = db.Column(db.String(255), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Message [{self.sender_type}] {self.message_text[:40]!r}>"


class ConversaConfig(db.Model):
    """Configurações por conversa (fixar, arquivar) para o canal WhatsApp."""
    __tablename__ = 'conversa_config'

    __table_args__ = (
        db.UniqueConstraint('usuario_crm_id', 'telefone', name='uq_conversa_config'),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(
        db.Integer,
        db.ForeignKey('usuario_crm.id', ondelete='CASCADE'),
        nullable=False,
    )
    telefone = db.Column(db.String(50), nullable=False)
    fixada = db.Column(db.Boolean, default=False, nullable=False)
    arquivada = db.Column(db.Boolean, default=False, nullable=False)
    data_config = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = db.relationship(
        'UsuarioCRM',
        backref=db.backref('conversas_config', lazy=True),
    )

    def __repr__(self) -> str:
        return f"<ConversaConfig {self.telefone} fixada={self.fixada} arquivada={self.arquivada}>"
