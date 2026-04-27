"""
Constantes do Sistema CRM
Define valores fixos usados em toda a aplicação
"""
from enum import Enum


# ==================== ENUMS ====================

class UserType(Enum):
    """Tipos de usuário do sistema"""
    SUPER_ADMIN = 'super_admin'
    ADMIN = 'admin'
    COLABORADOR = 'colaborador'


class TipoPessoa(Enum):
    """Tipos de pessoa (cliente)"""
    FISICA = 'Física'
    JURIDICA = 'Jurídica'
    CLIENTE = 'Cliente'


class SituacaoMesa(Enum):
    """Situações possíveis de uma mesa de negócio"""
    EM_NEGOCIACAO = 'Em negociação'
    GANHO = 'Ganho'
    PERDIDO = 'Perdido'
    FECHADO = 'Fechado'


class StatusOcorrencia(Enum):
    """Status de ocorrências"""
    ATIVO = 'Ativo'
    RESOLVIDO = 'Resolvido'
    CANCELADO = 'Cancelado'


class PrioridadeTarefa(Enum):
    """Prioridades de tarefas"""
    BAIXA = 'Baixa'
    NORMAL = 'Normal'
    ALTA = 'Alta'


class StatusTarefa(Enum):
    """Status de tarefas"""
    PENDENTE = 'Pendente'
    CONCLUIDA = 'Concluída'


class TipoArquivo(Enum):
    """Tipos de arquivo para upload"""
    IMAGE = 'image'
    AUDIO = 'audio'
    VIDEO = 'video'
    DOCUMENT = 'document'


# ==================== CONFIGURAÇÕES ====================

# Timing e Delays
DEFAULT_DELAY_SECONDS = 2.0
MIN_DELAY_SECONDS = 1.0
MAX_DELAY_SECONDS = 15.0
DEFAULT_QUARENTENA_NPS_DIAS = 30
JOB_CHECK_INTERVAL_SECONDS = 60
TOKEN_RENEWAL_INTERVAL_DAYS = 30

# Limites
MAX_UPLOAD_SIZE_MB = 16
MAX_TENTATIVAS_DISPARO = 3
MAX_RESULTS_PER_PAGE = 50
DEFAULT_PAGE_SIZE = 20

# Rate Limiting
RATE_LIMIT_DEFAULT = "100 per hour"
RATE_LIMIT_LOGIN = "5 per minute"
RATE_LIMIT_API = "1000 per hour"

# Arquivos permitidos
EXTENSOES_PERMITIDAS = {
    # Imagens
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    # Áudio
    '.mp3', '.wav', '.ogg', '.m4a',
    # Vídeo
    '.mp4', '.webm', '.mov',
    # Documentos
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.zip'
}

# Mapeamento de extensão para tipo
EXTENSAO_PARA_TIPO = {
    # Imagens
    '.jpg': TipoArquivo.IMAGE,
    '.jpeg': TipoArquivo.IMAGE,
    '.png': TipoArquivo.IMAGE,
    '.gif': TipoArquivo.IMAGE,
    '.webp': TipoArquivo.IMAGE,
    # Áudio
    '.mp3': TipoArquivo.AUDIO,
    '.wav': TipoArquivo.AUDIO,
    '.ogg': TipoArquivo.AUDIO,
    '.m4a': TipoArquivo.AUDIO,
    # Vídeo
    '.mp4': TipoArquivo.VIDEO,
    '.webm': TipoArquivo.VIDEO,
    '.mov': TipoArquivo.VIDEO,
    # Documentos (default)
}

# Mensagens padrão
MENSAGENS_DEFAULT = {
    'boas_vindas': 'Olá! Bem-vindo ao nosso atendimento. Como posso ajudá-lo?',
    'ausencia': 'No momento estamos ausentes. Retornaremos em breve!',
    'encerramento': 'Obrigado pelo contato! Até breve.',
    'nps': 'Em uma escala de 0 a 10, o quanto você recomendaria nossos serviços?',
}

# Validação
TELEFONE_REGEX = r'^\d{10,15}$'
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
CNPJ_REGEX = r'^\d{14}$'
CPF_REGEX = r'^\d{11}$'

# Módulos do sistema (para permissões)
MODULOS_SISTEMA = [
    'clientes',
    'mesas',
    'ocorrencias',
    'produtos',
    'estoque',
    'planner',
    'tarefas',
    'disparos',
    'canais',
    'relatorios',
    'fornecedores',
    'inbox',
    'configuracoes',
]

# Status HTTP customizados
HTTP_UNPROCESSABLE_ENTITY = 422
