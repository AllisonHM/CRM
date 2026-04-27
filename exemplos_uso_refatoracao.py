"""
Exemplo de uso das novas funcionalidades
"""

# ==================== VALIDATORS ====================

from utils.validators import Validator, ValidationError, validate_cliente_data

# Validar email
try:
    email = Validator.email("usuario@example.com", "email")
    print(f"Email válido: {email}")
except ValidationError as e:
    print(f"Erro no campo {e.field}: {e.message}")

# Validar telefone
try:
    telefone = Validator.telefone("(11) 98765-4321", "telefone")
    print(f"Telefone válido: {telefone}")  # Retorna apenas dígitos
except ValidationError as e:
    print(f"Erro: {e.message}")

# Validar dados completos de cliente
try:
    data = {
        'nome': 'João Silva',
        'telefone': '11987654321',
        'email': 'joao@example.com',
        'tipo_pessoa': 'Física',
        'renda': '5000.00'
    }
    validated = validate_cliente_data(data)
    print(f"Dados validados: {validated}")
except ValidationError as e:
    print(f"Campo {e.field}: {e.message}")


# ==================== EXCEPTIONS ====================

from utils.exceptions import (
    safe_commit,
    DatabaseError,
    ExternalAPIError,
    ResourceNotFoundError,
    handle_exception
)
from database_rls import db

# Uso do safe_commit (commit com rollback automático)
from models import Cliente

try:
    with safe_commit(db.session, "criar cliente"):
        cliente = Cliente(
            nome="João Silva",
            telefone="11987654321",
            usuario_crm_id=1
        )
        db.session.add(cliente)
        # Commit automático aqui
        # Se der erro, rollback automático
except DatabaseError as e:
    print(f"Erro ao salvar: {e.message}")

# Lançar exceção customizada
try:
    raise ResourceNotFoundError("Cliente", 123)
except ResourceNotFoundError as e:
    print(f"Erro: {e.message}")  # "Cliente não encontrado (ID: 123)"


# ==================== LOGGING ====================

from utils.logger import setup_logger, log_api_call, log_database_operation, mask_sensitive_data

# Configurar logger
logger = setup_logger(__name__, log_file='logs/crm.log', level=logging.INFO)

# Logar mensagem (dados sensíveis são mascarados automaticamente)
logger.info("Cliente criado: João Silva, telefone: 11987654321, email: joao@example.com")
# Output: Cliente criado: João Silva, telefone: 5511******, email: joao***@example.com

# Logar chamada de API
response_data = {
    "status": "Sucesso",
    "detalhe": "Mensagem enviada",
    "token": "abc123xyz"
}
log_api_call(logger, "Z-API", "send-text", response_data)

# Logar operação de banco
log_database_operation(logger, "CREATE", "Cliente", 123)

# Mascarar dados manualmente
texto_sensivel = "Cliente: João, telefone: 11987654321, email: joao@example.com"
texto_mascarado = mask_sensitive_data(texto_sensivel)
print(texto_mascarado)  # "Cliente: João, telefone: 5511******, email: joao***@example.com"


# ==================== SERVICES ====================

from services import ClienteService, MesaService, WhatsAppService

# ===== CLIENTE SERVICE =====

# Criar cliente
try:
    data_cliente = {
        'nome': 'Maria Oliveira',
        'telefone': '11998765432',
        'email': 'maria@example.com',
        'tipo_pessoa': 'Física',
        'renda': 8000.00
    }
    cliente = ClienteService.criar_cliente(data_cliente, usuario_crm_id=1)
    print(f"Cliente criado: ID {cliente.id}")
except ValidationError as e:
    print(f"Erro de validação: {e.field} - {e.message}")

# Buscar cliente
try:
    cliente = ClienteService.get_cliente_por_id(1, usuario_crm_id=1)
    print(f"Cliente encontrado: {cliente.nome}")
except ResourceNotFoundError as e:
    print(f"Cliente não encontrado: {e.message}")

# Listar clientes com paginação
clientes, total = ClienteService.listar_clientes(
    usuario_crm_id=1,
    page=1,
    per_page=10,
    search="Maria"  # Busca por nome, telefone ou email
)
print(f"Encontrados {total} clientes, página 1: {len(clientes)} resultados")

# Atualizar NPS
cliente = ClienteService.atualizar_nps(
    cliente_id=1,
    nota=10,
    comentario="Excelente!",
    usuario_crm_id=1
)


# ===== MESA SERVICE =====

# Criar mesa
try:
    data_mesa = {
        'topico': 'Venda de Sistema CRM',
        'produtos': 'Licença + Suporte',
        'situacao': 'Em negociação',
        'valor_total': 15000.00,
        'descricao': 'Cliente interessado em implementação completa'
    }
    mesa = MesaService.criar_mesa(
        data=data_mesa,
        cliente_id=1,
        usuario_crm_id=1
    )
    print(f"Mesa criada: #{mesa.numero}")
except ValidationError as e:
    print(f"Erro: {e.message}")

# Atualizar situação
mesa = MesaService.atualizar_situacao(
    mesa_id=1,
    nova_situacao='Ganho',
    usuario_crm_id=1
)

# Calcular estatísticas
stats = MesaService.calcular_estatisticas(usuario_crm_id=1)
print(f"Total de mesas: {stats['total']}")
print(f"Taxa de conversão: {stats['taxa_conversao']}%")
print(f"Valor ganho: R$ {stats['valor_ganho']}")


# ===== WHATSAPP SERVICE =====

from models import UsuarioCRM

# Enviar mensagem
usuario = UsuarioCRM.query.get(1)
try:
    resultado = WhatsAppService.enviar_mensagem_texto(
        numero='5511987654321',
        mensagem='Olá! Como podemos ajudar?',
        usuario_crm=usuario,
        delay_typing=2  # Mostra "digitando..." por 2 segundos
    )
    if resultado['status'] == 'Sucesso':
        print("Mensagem enviada!")
    else:
        print(f"Erro: {resultado['detalhe']}")
except ExternalAPIError as e:
    print(f"Erro na API: {e.message}")

# Enviar arquivo via URL
resultado = WhatsAppService.enviar_arquivo_url(
    numero='5511987654321',
    file_url='https://exemplo.com/arquivo.pdf',
    filename='documento.pdf',
    usuario_crm=usuario,
    caption='Segue o documento solicitado'
)


# ==================== CONSTANTS ====================

from config.constants import (
    UserType,
    SituacaoMesa,
    DEFAULT_DELAY_SECONDS,
    RATE_LIMIT_LOGIN,
    EXTENSOES_PERMITIDAS
)

# Usar enums em vez de strings hardcoded
if usuario.tipo_usuario == UserType.SUPER_ADMIN.value:
    print("Usuário é super admin")

# Usar constantes
import time
time.sleep(DEFAULT_DELAY_SECONDS)  # Em vez de time.sleep(2)

# Validar extensão de arquivo
file_ext = '.pdf'
if file_ext in EXTENSOES_PERMITIDAS:
    print("Extensão permitida")


# ==================== USANDO NAS ROTAS ====================

from flask import Flask, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from utils import ValidationError, handle_exception

app = Flask(__name__)

@app.route('/clientes', methods=['POST'])
@login_required
def criar_cliente():
    """Exemplo de rota usando os services"""
    try:
        # Criar cliente usando service (com validação automática)
        cliente = ClienteService.criar_cliente(
            data=request.form.to_dict(),
            usuario_crm_id=current_user.get_usuario_principal_id()
        )
        
        flash(f'Cliente {cliente.nome} criado com sucesso!', 'success')
        return redirect(url_for('listar_clientes'))
        
    except ValidationError as e:
        # Erro de validação (422)
        flash(f'Erro no campo {e.field}: {e.message}', 'danger')
        return redirect(url_for('form_cliente'))
    
    except Exception as e:
        # Outros erros (handler centralizado)
        return handle_exception(e)


@app.route('/api/clientes', methods=['POST'])
def api_criar_cliente():
    """Exemplo de rota API usando services"""
    try:
        data = request.get_json()
        
        cliente = ClienteService.criar_cliente(
            data=data,
            usuario_crm_id=current_user.get_usuario_principal_id()
        )
        
        return jsonify({
            'success': True,
            'cliente_id': cliente.id,
            'nome': cliente.nome
        }), 201
        
    except ValidationError as e:
        # Retorna JSON com erro de validação
        return jsonify({
            'success': False,
            'campo': e.field,
            'erro': e.message
        }), 422
    
    except Exception as e:
        # Handler centralizado retorna JSON automaticamente
        return handle_exception(e)


# ==================== ERROR HANDLERS GLOBAIS ====================

from utils.exceptions import handle_exception
from utils.validators import ValidationError

@app.errorhandler(Exception)
def handle_all_exceptions(error):
    """Handler global de exceções"""
    return handle_exception(error)

@app.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handler específico para erros de validação"""
    return jsonify({
        'erro': 'Dados inválidos',
        'campo': error.field,
        'mensagem': error.message
    }), 422


# ==================== RATE LIMITING ====================

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config.constants import RATE_LIMIT_DEFAULT, RATE_LIMIT_LOGIN

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT_DEFAULT],  # "100 per hour"
    storage_uri="memory://"
)

@app.route('/login', methods=['POST'])
@limiter.limit(RATE_LIMIT_LOGIN)  # "5 per minute"
def login():
    # ... código de login
    pass


# ==================== CSRF PROTECTION ====================

from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# Excluir webhooks do CSRF
@csrf.exempt
@app.route('/canais/webhook/received', methods=['POST'])
def webhook_received():
    # ... processar webhook
    pass


# Template HTML com CSRF token:
"""
<form method="POST" action="/clientes">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <input type="text" name="nome" required>
    <input type="tel" name="telefone" required>
    <button type="submit">Salvar</button>
</form>
"""


print("\n✅ Exemplos carregados! Use as funções acima como referência.")
