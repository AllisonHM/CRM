# models.py
from database import db
from datetime import datetime

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
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

    # Observações Gerais
    observacoes = db.Column(db.Text, nullable=True)  # Campo para anotações e observações gerais

    mesas = db.relationship('MesaNegocio', backref='cliente', lazy=True)
    ocorrencias = db.relationship('Ocorrencia', backref='cliente', lazy=True)

class MesaNegocio(db.Model):
    __tablename__ = 'mesa_negocio'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    topico = db.Column(db.String(150), nullable=False)
    produtos = db.Column(db.String(250), nullable=True)
    valor_total = db.Column(db.Float, nullable=True)
    situacao = db.Column(db.String(50), nullable=False, default="Em negociação")
    descricao = db.Column(db.Text, nullable=True)
    data_registro = db.Column(db.Date, nullable=False)
    hora_registro = db.Column(db.Time, nullable=False)

class Ocorrencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    topico = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_registro = db.Column(db.Date, nullable=False, default=datetime.today().date)
    hora_registro = db.Column(db.Time, nullable=False, default=datetime.now().time)

class WhatsAppMensagem(db.Model):
    __tablename__ = 'whatsapp_mensagem'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), nullable=False)
    remetente = db.Column(db.String(100))  # <-- esta linha é obrigatória
    mensagem = db.Column(db.Text, nullable=False)
    recebido_em = db.Column(db.DateTime, nullable=False)

class ChatbotRegra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    palavra_chave = db.Column(db.String(50), nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(20), default="Normal")

# Modelo Produto
class Produto(db.Model):
    __tablename__ = "produto"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
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
    tipo = db.Column(db.String(50), nullable=False)  # agendamento, contato, periodo
    cliente = db.Column(db.String(120), nullable=True)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)  # <-- NOVO CAMPO
    descricao = db.Column(db.Text, nullable=True)


