# =============================================
# 🌐 API PÚBLICA PARA CAPTAÇÃO DE LEADS DO SITE
# =============================================
# 
# INSTRUÇÕES DE INSTALAÇÃO:
# 1. Instalar dependências: pip install flask-cors flask-limiter python-dotenv
# 2. Criar arquivo .env na raiz do projeto com:
#    - API_KEY_SITE=sua-chave-secreta-aqui-123456
#    - ALLOWED_ORIGINS=https://seu-site.github.io,http://localhost:3000
#    - USUARIO_CRM_LEADS=1
# 3. Adicionar este código ao CRM.py (antes do if __name__ == '__main__')
# 4. Atualizar site/script.js com a URL do backend e API Key
#
# =============================================

import os
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar rate limiting (prevenir spam)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configurar CORS apenas para rotas públicas
CORS(app, resources={
    r"/api/public/*": {
        "origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["POST", "OPTIONS", "GET"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})

# =============================================
# 🔑 VALIDAÇÕES
# =============================================

def validar_api_key():
    """Valida API Key enviada no header"""
    api_key = request.headers.get('X-API-Key')
    api_key_correta = os.getenv('API_KEY_SITE', 'chave-padrao-alterar')
    
    if not api_key or api_key != api_key_correta:
        return False
    return True

def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_telefone(telefone):
    """Valida e formata telefone (apenas números)"""
    telefone_limpo = re.sub(r'\D', '', telefone)
    return telefone_limpo if len(telefone_limpo) >= 10 else None

# =============================================
# 🌐 ROTAS PÚBLICAS
# =============================================

@app.route('/api/public/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar se a API está online
    
    Retorna:
        200: API está funcionando
    """
    return jsonify({
        "status": "online",
        "servico": "CRM API Pública",
        "versao": "1.0",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route('/api/public/lead', methods=['POST', 'OPTIONS'])
@limiter.limit("5 per minute")
def captar_lead_site():
    """
    API pública para captar leads do site institucional
    
    Body JSON esperado:
    {
        "nome": "João Silva",
        "email": "joao@email.com",
        "telefone": "(11) 98888-7777",
        "mensagem": "Gostaria de saber mais sobre o CRM" (opcional)
    }
    
    Headers obrigatórios:
    - Content-Type: application/json
    - X-API-Key: <chave configurada em .env>
    
    Retorna:
    - 201: Lead criado com sucesso
    - 400: Dados inválidos
    - 401: API Key inválida
    - 429: Muitas requisições (rate limit)
    - 500: Erro interno
    """
    
    # Permitir preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    # Validar API Key
    if not validar_api_key():
        logger.warning(f"⚠️ Tentativa de acesso com API Key inválida de {request.remote_addr}")
        return jsonify({
            "erro": "API Key inválida",
            "codigo": "API_KEY_INVALIDA"
        }), 401
    
    try:
        # Obter dados do JSON
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                "erro": "Corpo da requisição vazio ou inválido",
                "codigo": "DADOS_INVALIDOS"
            }), 400
        
        # Validar campos obrigatórios
        nome = dados.get('nome', '').strip()
        email = dados.get('email', '').strip()
        telefone = dados.get('telefone', '').strip()
        mensagem = dados.get('mensagem', '').strip()
        
        erros = []
        
        # Validar nome
        if not nome or len(nome) < 3:
            erros.append("Nome deve ter no mínimo 3 caracteres")
        
        # Validar email
        if not email or not validar_email(email):
            erros.append("Email inválido")
        
        # Validar telefone
        telefone_limpo = validar_telefone(telefone)
        if not telefone_limpo:
            erros.append("Telefone inválido (mínimo 10 dígitos)")
        
        # Se houver erros, retornar
        if erros:
            return jsonify({
                "erro": "Dados inválidos",
                "detalhes": erros,
                "codigo": "VALIDACAO_FALHOU"
            }), 400
        
        # Verificar se email já existe (evitar duplicatas)
        cliente_existente = Cliente.query.filter_by(email=email).first()
        if cliente_existente:
            logger.info(f"ℹ️ Email já cadastrado: {email}")
            return jsonify({
                "erro": "Este email já está cadastrado em nosso sistema",
                "codigo": "EMAIL_DUPLICADO"
            }), 400
        
        # Obter ID do usuário CRM padrão para leads do site
        usuario_padrao_id = int(os.getenv('USUARIO_CRM_LEADS', '1'))
        
        # Verificar se o usuário padrão existe
        usuario_padrao = UsuarioCRM.query.get(usuario_padrao_id)
        if not usuario_padrao:
            logger.error(f"❌ Usuário CRM padrão não encontrado: ID {usuario_padrao_id}")
            return jsonify({
                "erro": "Configuração inválida do sistema",
                "codigo": "USUARIO_NAO_ENCONTRADO"
            }), 500
        
        # Criar novo cliente (lead)
        novo_cliente = Cliente(
            usuario_crm_id=usuario_padrao_id,
            nome=nome,
            email=email,
            telefone=telefone_limpo,
            tipo_pessoa="Lead Site",  # Identificar origem
            observacoes=f"📌 Lead capturado do site institucional em {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n"
                       f"{'Mensagem: ' + mensagem if mensagem else 'Sem mensagem adicional'}"
        )
        
        db.session.add(novo_cliente)
        db.session.commit()
        
        logger.info(f"✅ Lead capturado do site: {nome} ({email}) - ID {novo_cliente.id}")
        
        return jsonify({
            "sucesso": True,
            "mensagem": "Cadastro realizado com sucesso! Em breve entraremos em contato.",
            "lead_id": novo_cliente.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erro ao captar lead do site: {str(e)}")
        return jsonify({
            "erro": "Erro interno ao processar cadastro",
            "codigo": "ERRO_INTERNO",
            "detalhes": str(e) if app.debug else None
        }), 500

# =============================================
# 📊 ROTA PARA ESTATÍSTICAS (OPCIONAL - REQUER AUTH)
# =============================================

@app.route('/api/leads/stats', methods=['GET'])
@login_required
@permission_required('clientes')
def estatisticas_leads():
    """
    Retorna estatísticas dos leads captados do site
    Requer autenticação
    """
    user_id = get_usuario_filter()
    
    # Filtrar leads do site
    query = Cliente.query.filter_by(tipo_pessoa="Lead Site")
    
    if user_id:
        query = query.filter_by(usuario_crm_id=user_id)
    
    total_leads = query.count()
    leads_ultimos_30_dias = query.filter(
        Cliente.id >= datetime.now() - timedelta(days=30)
    ).count()
    
    return jsonify({
        "total_leads": total_leads,
        "ultimos_30_dias": leads_ultimos_30_dias
    }), 200
