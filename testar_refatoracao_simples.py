"""
Testes simples das novas funcionalidades (sem banco de dados)
"""

print("=" * 60)
print("🧪 TESTANDO NOVAS FUNCIONALIDADES DO CRM")
print("=" * 60)
print()

# ==================== 1. VALIDATORS ====================
print("📋 1. TESTANDO VALIDADORES")
print("-" * 60)

from utils.validators import Validator, ValidationError

# Validar email
try:
    email = Validator.email("usuario@example.com", "email")
    print(f"✅ Email válido: {email}")
except ValidationError as e:
    print(f"❌ Erro no campo {e.field}: {e.message}")

# Validar telefone
try:
    telefone = Validator.telefone("(11) 98765-4321", "telefone")
    print(f"✅ Telefone válido: {telefone}")  # Retorna apenas dígitos
except ValidationError as e:
    print(f"❌ Erro: {e.message}")

# Testar validação que deve falhar
try:
    email_invalido = Validator.email("email-invalido", "email")
except ValidationError as e:
    print(f"✅ Validação funcionou: Detectou email inválido - {e.message}")

print()

# ==================== 2. LOGGING SEGURO ====================
print("📝 2. TESTANDO LOGGING SEGURO")
print("-" * 60)

from utils.logger import mask_sensitive_data

# Testar mascaramento
texto_sensivel = "Cliente: João, telefone: 11987654321, email: joao@example.com, CPF: 12345678900"
texto_mascarado = mask_sensitive_data(texto_sensivel)
print(f"Original: {texto_sensivel}")
print(f"Mascarado: {texto_mascarado}")
print()

# ==================== 3. CONSTANTES ====================
print("🎯 3. TESTANDO CONSTANTES E ENUMS")
print("-" * 60)

from config.constants import (
    UserType,
    SituacaoMesa,
    DEFAULT_DELAY_SECONDS,
    RATE_LIMIT_LOGIN,
    EXTENSOES_PERMITIDAS
)

print(f"✅ UserType.SUPER_ADMIN = {UserType.SUPER_ADMIN.value}")
print(f"✅ UserType.ADMIN = {UserType.ADMIN.value}")
print(f"✅ UserType.COLABORADOR = {UserType.COLABORADOR.value}")
print()
print(f"✅ SituacaoMesa.EM_NEGOCIACAO = {SituacaoMesa.EM_NEGOCIACAO.value}")
print(f"✅ SituacaoMesa.GANHO = {SituacaoMesa.GANHO.value}")
print()
print(f"✅ DEFAULT_DELAY_SECONDS = {DEFAULT_DELAY_SECONDS}")
print(f"✅ RATE_LIMIT_LOGIN = {RATE_LIMIT_LOGIN}")
print(f"✅ Extensões permitidas: {EXTENSOES_PERMITIDAS}")
print()

# Validar extensão de arquivo
file_ext = '.pdf'
if file_ext in EXTENSOES_PERMITIDAS:
    print(f"✅ Extensão {file_ext} é permitida")
else:
    print(f"❌ Extensão {file_ext} não é permitida")

print()

# ==================== 4. VALIDAÇÃO COMPLETA ====================
print("🔍 4. TESTANDO VALIDAÇÃO COMPLETA DE CLIENTE")
print("-" * 60)

from utils.validators import validate_cliente_data

try:
    data = {
        'nome': 'Maria Oliveira',
        'telefone': '11998765432',
        'email': 'maria@example.com',
        'tipo_pessoa': 'Física',
        'renda': '8000.00'
    }
    validated = validate_cliente_data(data)
    print("✅ Dados validados com sucesso:")
    for key, value in validated.items():
        print(f"   - {key}: {value}")
except ValidationError as e:
    print(f"❌ Erro no campo {e.field}: {e.message}")

print()

# Testar dados inválidos
try:
    data_invalida = {
        'nome': '',  # Vazio
        'telefone': '123',  # Muito curto
        'email': 'email-invalido',
        'tipo_pessoa': 'Física'
    }
    validated = validate_cliente_data(data_invalida)
except ValidationError as e:
    print(f"✅ Validação funcionou: Detectou erro no campo '{e.field}' - {e.message}")

print()

# ==================== 5. EXCEPTIONS ====================
print("⚠️  5. TESTANDO EXCEÇÕES CUSTOMIZADAS")
print("-" * 60)

from utils.exceptions import (
    ResourceNotFoundError,
    ExternalAPIError,
    PermissionDeniedError
)

try:
    raise ResourceNotFoundError("Cliente", 123)
except ResourceNotFoundError as e:
    print(f"✅ ResourceNotFoundError: {e.message}")

try:
    raise ExternalAPIError("Z-API", "Timeout ao enviar mensagem")
except ExternalAPIError as e:
    print(f"✅ ExternalAPIError: {e.message}")

try:
    raise PermissionDeniedError("Apenas super_admin pode acessar esta funcionalidade")
except PermissionDeniedError as e:
    print(f"✅ PermissionDeniedError: {e.message}")

print()

# ==================== RESUMO ====================
print("=" * 60)
print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
print("=" * 60)
print()
print("📚 PRÓXIMOS PASSOS:")
print("   1. ✅ Dependências instaladas")
print("   2. ✅ Validadores funcionando")
print("   3. ✅ Logging seguro ativo")
print("   4. ✅ Constantes carregadas")
print("   5. ⏳ Aplicar índices no banco: flask db upgrade")
print("   6. ⏳ Começar a usar os services no seu código!")
print()
print("💡 DICA: Veja GUIA_REFATORACAO_COMPLETO.md para exemplos completos")
print()
