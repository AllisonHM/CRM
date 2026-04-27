"""
Configurações para ambiente de produção
"""
import os
from datetime import timedelta

class ProductionConfig:
    """Configuração para produção (Locaweb)"""
    
    # ===================
    # BANCO DE DADOS
    # ===================
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verifica conexão antes de usar
        'pool_recycle': 300,     # Recicla conexões a cada 5min
        'pool_size': 10,         # Pool de 10 conexões
        'max_overflow': 20       # Até 20 extras se necessário
    }
    
    # ===================
    # SEGURANÇA
    # ===================
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Token não expira
    
    # Session Security
    SESSION_COOKIE_SECURE = True      # Apenas HTTPS
    SESSION_COOKIE_HTTPONLY = True    # Não acessível via JS
    SESSION_COOKIE_SAMESITE = 'Lax'   # Proteção CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # ===================
    # UPLOAD DE ARQUIVOS
    # ===================
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt',
        'jpg', 'jpeg', 'png', 'gif', 'webp',
        'mp3', 'mp4', 'wav', 'ogg', 'webm',
        'zip'
    }
    
    # ===================
    # FLASK
    # ===================
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # ===================
    # LOGS
    # ===================
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/tmp/crm.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # ===================
    # EMAIL (se configurado)
    # ===================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.locaweb.com.br')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # ===================
    # DOMÍNIO
    # ===================
    DOMAIN = os.environ.get('DOMAIN', 'https://localhost')
    
    # ===================
    # RATE LIMITING
    # ===================
    RATELIMIT_STORAGE_URL = 'memory://'  # Ou Redis se disponível
    RATELIMIT_ENABLED = True
    
    # ===================
    # CACHE (se usar Redis)
    # ===================
    CACHE_TYPE = 'simple'  # Ou 'redis' se disponível
    # CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    
    @staticmethod
    def init_app(app):
        """Inicialização específica para produção"""
        # Criar diretórios necessários
        import os
        
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and not os.path.exists(upload_folder):
            os.makedirs(upload_folder, mode=0o755, exist_ok=True)
        
        log_file = app.config.get('LOG_FILE')
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, mode=0o755, exist_ok=True)
