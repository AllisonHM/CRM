from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, g
from flask_socketio import SocketIO, join_room
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
import requests
import logging
from flask_migrate import Migrate
from database_rls import db, tenant_db, init_db
from models import Cliente, MesaNegocio, Ocorrencia, WhatsAppMensagem, ChatbotRegra, Produto, Movimentacao, PlannerEvento, UsuarioCRM
from sqlalchemy import or_, and_

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "seusegredo"

# ------------------- BANCO COM RLS -------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Amovoce123%40@localhost:1222/crm'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # True para debug SQL

# Inicializa DB com suporte a RLS
db.init_app(app)
tenant_db.init_app(app)

# ------------------- FLASK-LOGIN -------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

@login_manager.user_loader
def load_user(user_id):
    return UsuarioCRM.query.get(int(user_id))

# Decorador para verificar permissões
def permission_required(modulo):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.tem_permissao(modulo):
                flash('Você não tem permissão para acessar este módulo.', 'danger')
                return redirect(url_for('menu'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Função auxiliar para filtrar dados por usuário
def get_usuario_filter():
    """Retorna o ID do usuário principal para filtrar dados
    
    NOTA: Com RLS ativo, esta função não é mais necessária para segurança,
    mas mantemos para compatibilidade com código legado.
    O PostgreSQL RLS automaticamente filtra os dados pelo tenant_id.
    """
    if current_user.tipo_usuario == 'super_admin':
        # Super admin pode ver tudo (RLS será desabilitado manualmente quando necessário)
        return None
    return current_user.get_usuario_principal_id()

socketio = SocketIO(app, cors_allowed_origins="*")

migrate = Migrate(app, db)

# ------------------- Z-API -------------------
instance = "3E70C9784E1060A6F423AE9094E04006"
token = "E4E83715DE9F517EFB9A28CA"
client_token = "Fc5c052a80080460b823a2e506d4d6167S"
headers = {'client-token': client_token, 'Content-Type': 'application/json'}

def enviar_whatsapp_zapi(numero, mensagem, instance_id=None, token_id=None):
    """Envia mensagem via Z-API usando a instância do cliente ou do admin"""
    # Se não fornecido, usar o número do usuário logado
    if not instance_id:
        instance_id = instance
    if not token_id:
        token_id = token
    
    url = f"https://api.z-api.io/instances/{instance_id}/token/{token_id}/send-text"
    payload = {"phone": numero, "message": mensagem}
    
    print(f"🌐 URL: {url}")
    print(f"📦 Payload: phone={numero}, message_length={len(mensagem)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text[:200]}...")  # Primeiros 200 caracteres
        
        if response.status_code == 200:
            return {"status": "Sucesso", "detalhe": response.text}
        return {"status": "Erro", "detalhe": f"Status {response.status_code}: {response.text}"}
    except Exception as e:
        print(f"❌ EXCEÇÃO ao enviar WhatsApp: {str(e)}")
        return {"status": "Erro", "detalhe": str(e)}
    
import threading, time

def verificar_eventos_proximos():
    with app.app_context():
        while True:
            agora = datetime.now()
            limite = agora + timedelta(minutes=30)

            eventos = PlannerEvento.query.filter(
                PlannerEvento.data_hora >= agora,
                PlannerEvento.data_hora <= limite
            ).all()

            for evento in eventos:
                socketio.emit('notificacao_evento', {
                    'titulo': evento.titulo,
                    'descricao': evento.descricao,
                    'hora': evento.data_hora.strftime('%H:%M'),
                    'cliente': evento.cliente.nome if evento.cliente else "N/A"
                })

            time.sleep(60)  # roda a cada 60 segundos

threading.Thread(target=verificar_eventos_proximos, daemon=True).start()


# ------------------- ROTAS DE AUTENTICAÇÃO -------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        usuario = UsuarioCRM.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(senha):
            if not usuario.ativo:
                flash('Seu usuário está inativo. Entre em contato com o administrador.', 'danger')
                return redirect(url_for('login'))
            
            login_user(usuario)
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            
            # Redirecionar para a página solicitada ou menu
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('menu'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

@app.route('/criar_super_admin')
def criar_super_admin():
    """Rota temporária para criar o primeiro super admin"""
    # Verificar se já existe um super admin
    super_admin_existe = UsuarioCRM.query.filter_by(tipo_usuario='super_admin').first()
    if super_admin_existe:
        return "Super Admin já existe!"
    
    # Criar super admin
    super_admin = UsuarioCRM(
        nome="Administrador",
        email="admin@crm.com",
        tipo_usuario="super_admin",
        ativo=True
    )
    super_admin.set_password("admin123")  # ALTERAR ESTA SENHA APÓS PRIMEIRO LOGIN!
    
    db.session.add(super_admin)
    db.session.commit()
    
    return "Super Admin criado com sucesso! Email: admin@crm.com | Senha: admin123"


# ------------------- GESTÃO DE USUÁRIOS (SUPER ADMIN) -------------------
@app.route('/usuarios')
@login_required
def listar_usuarios():
    """Lista todos os usuários do tipo admin (clientes)"""
    if current_user.tipo_usuario != 'super_admin':
        flash('Acesso negado. Apenas Super Admin pode acessar.', 'danger')
        return redirect(url_for('menu'))
    
    usuarios = UsuarioCRM.query.filter(UsuarioCRM.tipo_usuario.in_(['admin', 'colaborador'])).all()
    return render_template('listar_usuarios.html', usuarios=usuarios)

@app.route('/usuarios/add', methods=['GET', 'POST'])
@login_required
def add_usuario():
    """Adiciona novo usuário (cliente admin)"""
    if current_user.tipo_usuario != 'super_admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        numero_whatsapp = request.form.get('numero_whatsapp')
        api_instance = request.form.get('api_instance')
        api_token = request.form.get('api_token')
        
        # Módulos disponíveis
        modulos = ['clientes', 'mesas', 'ocorrencias', 'produtos', 'whatsapp', 'chatbot', 'planner', 'nps', 'relatorios']
        permissoes = {modulo: modulo in request.form.getlist('permissoes') for modulo in modulos}
        
        # Verificar se email já existe
        if UsuarioCRM.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'danger')
            return redirect(url_for('add_usuario'))
        
        # Criar novo usuário
        novo_usuario = UsuarioCRM(
            nome=nome,
            email=email,
            numero_whatsapp=numero_whatsapp,
            api_instance=api_instance,
            api_token=api_token,
            tipo_usuario='admin',
            permissoes=permissoes,
            ativo=True
        )
        novo_usuario.set_password(senha)
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash(f'Usuário {nome} criado com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))
    
    # Módulos disponíveis
    modulos_disponiveis = [
        {'id': 'clientes', 'nome': 'Clientes', 'icone': '👥'},
        {'id': 'mesas', 'nome': 'Mesas de Negócio', 'icone': '💼'},
        {'id': 'ocorrencias', 'nome': 'Ocorrências', 'icone': '⚠️'},
        {'id': 'produtos', 'nome': 'Produtos', 'icone': '📦'},
        {'id': 'whatsapp', 'nome': 'WhatsApp', 'icone': '💬'},
        {'id': 'chatbot', 'nome': 'Chatbot', 'icone': '🤖'},
        {'id': 'planner', 'nome': 'Planner', 'icone': '📅'},
        {'id': 'nps', 'nome': 'NPS', 'icone': '⭐'},
        {'id': 'relatorios', 'nome': 'Relatórios', 'icone': '📊'}
    ]
    
    return render_template('add_usuario.html', modulos=modulos_disponiveis)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    """Edita usuário existente"""
    if current_user.tipo_usuario != 'super_admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('menu'))
    
    usuario = UsuarioCRM.query.get_or_404(id)
    
    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        usuario.email = request.form.get('email')
        usuario.numero_whatsapp = request.form.get('numero_whatsapp')
        usuario.api_instance = request.form.get('api_instance')
        usuario.api_token = request.form.get('api_token')
        usuario.ativo = 'ativo' in request.form
        
        # Atualizar senha se fornecida
        nova_senha = request.form.get('senha')
        if nova_senha:
            usuario.set_password(nova_senha)
        
        # Atualizar permissões
        modulos = ['clientes', 'mesas', 'ocorrencias', 'produtos', 'whatsapp', 'chatbot', 'planner', 'nps', 'relatorios']
        permissoes = {modulo: modulo in request.form.getlist('permissoes') for modulo in modulos}
        usuario.permissoes = permissoes
        
        db.session.commit()
        flash(f'Usuário {usuario.nome} atualizado com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))
    
    # Módulos disponíveis
    modulos_disponiveis = [
        {'id': 'clientes', 'nome': 'Clientes', 'icone': '👥'},
        {'id': 'mesas', 'nome': 'Mesas de Negócio', 'icone': '💼'},
        {'id': 'ocorrencias', 'nome': 'Ocorrências', 'icone': '⚠️'},
        {'id': 'produtos', 'nome': 'Produtos', 'icone': '📦'},
        {'id': 'whatsapp', 'nome': 'WhatsApp', 'icone': '💬'},
        {'id': 'chatbot', 'nome': 'Chatbot', 'icone': '🤖'},
        {'id': 'planner', 'nome': 'Planner', 'icone': '📅'},
        {'id': 'nps', 'nome': 'NPS', 'icone': '⭐'},
        {'id': 'relatorios', 'nome': 'Relatórios', 'icone': '📊'}
    ]
    
    return render_template('editar_usuario.html', usuario=usuario, modulos=modulos_disponiveis)

@app.route('/usuarios/deletar/<int:id>', methods=['POST'])
@login_required
def deletar_usuario(id):
    """Deleta usuário"""
    if current_user.tipo_usuario != 'super_admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('menu'))
    
    usuario = UsuarioCRM.query.get_or_404(id)
    
    if usuario.tipo_usuario == 'super_admin':
        flash('Não é possível deletar um Super Admin!', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    nome = usuario.nome
    db.session.delete(usuario)
    db.session.commit()
    
    flash(f'Usuário {nome} deletado com sucesso!', 'success')
    return redirect(url_for('listar_usuarios'))


# ------------------- GESTÃO DE COLABORADORES (SUPER_ADMIN APENAS) -------------------
@app.route('/colaboradores')
@login_required
def listar_colaboradores():
    """Lista todos os colaboradores - APENAS SUPER_ADMIN"""
    if current_user.tipo_usuario != 'super_admin':
        flash('Acesso negado. Apenas o administrador master pode gerenciar colaboradores.', 'danger')
        return redirect(url_for('menu'))
    
    # Verificar se há filtro por cliente
    cliente_id = request.args.get('cliente_id', type=int)
    
    if cliente_id:
        # Filtrar colaboradores de um cliente específico
        colaboradores = UsuarioCRM.query.filter_by(
            tipo_usuario='colaborador',
            usuario_pai_id=cliente_id
        ).order_by(UsuarioCRM.nome).all()
        cliente = UsuarioCRM.query.get(cliente_id)
        cliente_nome = cliente.nome if cliente else None
    else:
        # Super admin vê todos os colaboradores
        colaboradores = UsuarioCRM.query.filter_by(tipo_usuario='colaborador').order_by(UsuarioCRM.nome).all()
        cliente_nome = None
    
    return render_template('listar_colaboradores.html', colaboradores=colaboradores, cliente_filtro=cliente_nome)

@app.route('/colaboradores/add', methods=['GET', 'POST'])
@login_required
def add_colaborador():
    """Adiciona novo colaborador - APENAS SUPER_ADMIN"""
    if current_user.tipo_usuario != 'super_admin':
        flash('Acesso negado. Apenas o administrador master pode gerenciar colaboradores.', 'danger')
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Permissões
        modulos = ['clientes', 'mesas', 'ocorrencias', 'produtos', 'whatsapp', 'chatbot', 'planner', 'nps', 'relatorios']
        permissoes = {modulo: modulo in request.form.getlist('permissoes') for modulo in modulos}
        
        # Verificar se email já existe
        if UsuarioCRM.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'danger')
            return redirect(url_for('add_colaborador'))
        
        # Obter o cliente (admin) a quem pertencerá o colaborador
        usuario_pai_id = request.form.get('usuario_pai_id')
        if not usuario_pai_id:
            flash('Selecione o cliente para este colaborador.', 'danger')
            return redirect(url_for('add_colaborador'))
        
        # Criar novo colaborador
        novo_colaborador = UsuarioCRM(
            nome=nome,
            email=email,
            tipo_usuario='colaborador',
            usuario_pai_id=int(usuario_pai_id),
            permissoes=permissoes,
            ativo=True
        )
        novo_colaborador.set_password(senha)
        
        db.session.add(novo_colaborador)
        db.session.commit()
        
        flash(f'Colaborador {nome} criado com sucesso!', 'success')
        return redirect(url_for('listar_colaboradores'))
    
    # Módulos disponíveis
    modulos_disponiveis = [
        {'id': 'clientes', 'nome': 'Clientes', 'icone': '👥'},
        {'id': 'mesas', 'nome': 'Mesas de Negócio', 'icone': '💼'},
        {'id': 'ocorrencias', 'nome': 'Ocorrências', 'icone': '⚠️'},
        {'id': 'produtos', 'nome': 'Produtos', 'icone': '📦'},
        {'id': 'whatsapp', 'nome': 'WhatsApp', 'icone': '💬'},
        {'id': 'chatbot', 'nome': 'Chatbot', 'icone': '🤖'},
        {'id': 'planner', 'nome': 'Planner', 'icone': '📅'},
        {'id': 'nps', 'nome': 'NPS', 'icone': '⭐'},
        {'id': 'relatorios', 'nome': 'Relatórios', 'icone': '📊'}
    ]
    
    # Buscar todos os clientes (admin) para selecionar
    clientes = UsuarioCRM.query.filter_by(tipo_usuario='admin', ativo=True).order_by(UsuarioCRM.nome).all()
    
    return render_template('add_colaborador.html', modulos=modulos_disponiveis, clientes=clientes)

@app.route('/colaboradores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_colaborador(id):
    """Edita colaborador existente - APENAS SUPER_ADMIN"""
    if current_user.tipo_usuario != 'super_admin':
        flash('Acesso negado. Apenas o administrador master pode gerenciar colaboradores.', 'danger')
        return redirect(url_for('menu'))
    
    colaborador = UsuarioCRM.query.get_or_404(id)
    
    if request.method == 'POST':
        colaborador.nome = request.form.get('nome')
        colaborador.email = request.form.get('email')
        colaborador.ativo = 'ativo' in request.form
        
        # Atualizar senha se fornecida
        nova_senha = request.form.get('senha')
        if nova_senha:
            colaborador.set_password(nova_senha)
        
        # Atualizar permissões
        modulos = ['clientes', 'mesas', 'ocorrencias', 'produtos', 'whatsapp', 'chatbot', 'planner', 'nps', 'relatorios']
        permissoes = {modulo: modulo in request.form.getlist('permissoes') for modulo in modulos}
        colaborador.permissoes = permissoes
        
        db.session.commit()
        flash(f'Colaborador {colaborador.nome} atualizado com sucesso!', 'success')
        return redirect(url_for('listar_colaboradores'))
    
    # Módulos disponíveis
    modulos_disponiveis = [
        {'id': 'clientes', 'nome': 'Clientes', 'icone': '👥'},
        {'id': 'mesas', 'nome': 'Mesas de Negócio', 'icone': '💼'},
        {'id': 'ocorrencias', 'nome': 'Ocorrências', 'icone': '⚠️'},
        {'id': 'produtos', 'nome': 'Produtos', 'icone': '📦'},
        {'id': 'whatsapp', 'nome': 'WhatsApp', 'icone': '💬'},
        {'id': 'chatbot', 'nome': 'Chatbot', 'icone': '🤖'},
        {'id': 'planner', 'nome': 'Planner', 'icone': '📅'},
        {'id': 'nps', 'nome': 'NPS', 'icone': '⭐'},
        {'id': 'relatorios', 'nome': 'Relatórios', 'icone': '📊'}
    ]
    
    return render_template('editar_colaborador.html', colaborador=colaborador, modulos=modulos_disponiveis)

@app.route('/colaboradores/deletar/<int:id>', methods=['POST'])
@login_required
def deletar_colaborador(id):
    """Deleta colaborador - APENAS SUPER_ADMIN"""
    if current_user.tipo_usuario != 'super_admin':
        flash('Acesso negado. Apenas o administrador master pode gerenciar colaboradores.', 'danger')
        return redirect(url_for('menu'))
    
    colaborador = UsuarioCRM.query.get_or_404(id)
    
    nome = colaborador.nome
    db.session.delete(colaborador)
    db.session.commit()
    
    flash(f'Colaborador {nome} deletado com sucesso!', 'success')
    return redirect(url_for('listar_colaboradores'))


# ------------------- FUNÇÕES AUXILIARES -------------------
def enviar_pesquisa_nps(cliente):
    """
    Envia pesquisa de NPS via WhatsApp quando uma mesa é ganha.
    """
    print(f"\n🔍 === INICIANDO ENVIO DE NPS ===")
    print(f"📋 Cliente: {cliente.nome}")
    print(f"📞 Telefone original: {cliente.telefone}")
    
    mensagem = f"""Olá {cliente.nome}! 👋

Obrigado por fechar negócio conosco! 🎉

Em uma escala de 0 a 10, o quanto você recomendaria nossa empresa para um amigo ou colega?

0️⃣ = Nunca recomendaria
🔟 = Recomendaria com certeza

Por favor, responda apenas com um número de 0 a 10."""

    numero_norm = normalize_phone(cliente.telefone)
    print(f"📞 Telefone normalizado: {numero_norm}")
    
    print(f"📤 Enviando mensagem via Z-API...")
    resultado = enviar_whatsapp_zapi(numero_norm, mensagem)
    
    print(f"📥 Resultado do envio: {resultado}")
    
    if resultado["status"] == "Sucesso":
        print(f"✅ Mensagem enviada com sucesso!")
        # Marcar que está aguardando resposta de NPS
        cliente.aguardando_nps = True
        db.session.commit()
        
        # Salvar mensagem enviada
        msg = WhatsAppMensagem(
            numero=numero_norm,
            remetente="Você",
            mensagem=mensagem,
            recebido_em=datetime.utcnow()
        )
        db.session.add(msg)
        db.session.commit()
        
        print(f"✅ Cliente marcado como aguardando NPS e mensagem salva no banco")
        return True
    else:
        print(f"❌ Falha no envio: {resultado.get('detalhe', 'Sem detalhes')}")
        return False


def processar_resposta_nps(cliente, texto):
    """
    Processa a resposta de NPS do cliente.
    Retorna True se foi uma resposta válida de NPS.
    """
    print(f"\n📊 === PROCESSANDO RESPOSTA NPS ===")
    print(f"👤 Cliente: {cliente.nome} (ID: {cliente.id})")
    print(f"📝 Texto recebido: {texto}")
    
    # Tentar extrair número de 0 a 10
    import re
    numeros = re.findall(r'\b(10|[0-9])\b', texto.strip())
    
    print(f"🔢 Números encontrados: {numeros}")
    
    if numeros:
        nota = int(numeros[0])
        if 0 <= nota <= 10:
            print(f"✅ Nota válida: {nota}")
            # Registrar NPS
            cliente.nps_nota = nota
            cliente.nps_data = datetime.utcnow()
            cliente.aguardando_nps = False
            db.session.commit()
            print(f"💾 NPS salvo no banco: nota={nota}, data={cliente.nps_data}")
            
            # Enviar mensagem de agradecimento
            numero_norm = normalize_phone(cliente.telefone)
            
            if nota >= 9:
                categoria = "Promotor"
                emoji = "🌟"
                msg_agradecimento = f"Obrigado pela nota {nota}! {emoji}\n\nFicamos muito felizes em saber que você recomendaria nossa empresa! Seu feedback é muito importante para nós. 💙"
            elif nota >= 7:
                categoria = "Neutro"
                emoji = "😊"
                msg_agradecimento = f"Obrigado pela nota {nota}! {emoji}\n\nEstamos sempre buscando melhorar. Se tiver alguma sugestão, ficaremos felizes em ouvir!"
            else:
                categoria = "Detrator"
                emoji = "😔"
                msg_agradecimento = f"Obrigado pela nota {nota}. {emoji}\n\nLamentamos não ter atendido suas expectativas. Poderia nos dizer o que podemos melhorar? Seu feedback é muito importante para nós."
            
            print(f"📤 Enviando agradecimento: categoria={categoria}")
            enviar_whatsapp_zapi(numero_norm, msg_agradecimento)
            print(f"✅ Agradecimento enviado")
            
            # Salvar agradecimento
            msg = WhatsAppMensagem(
                numero=numero_norm,
                remetente="Você",
                mensagem=msg_agradecimento,
                recebido_em=datetime.utcnow()
            )
            db.session.add(msg)
            db.session.commit()
            print(f"💾 Agradecimento salvo no banco")
            
            return True
    
    print(f"⚠️ Nenhum número válido (0-10) encontrado no texto")
    return False


# ------------------- ROTAS -------------------
@app.route("/")
@login_required
def home():
    return redirect(url_for("menu"))

@app.route('/menu')
@login_required
def menu():
    # Obter filtro de usuário
    user_id = get_usuario_filter()
    
    # Preparar filtros base
    if user_id:
        base_filter_cliente = Cliente.usuario_crm_id == user_id
        base_filter_mesa = MesaNegocio.usuario_crm_id == user_id
        base_filter_ocorrencia = Ocorrencia.usuario_crm_id == user_id
        base_filter_produto = Produto.usuario_crm_id == user_id
        base_filter_planner = PlannerEvento.usuario_crm_id == user_id
        base_filter_mensagem = WhatsAppMensagem.usuario_crm_id == user_id
    else:
        base_filter_cliente = True
        base_filter_mesa = True
        base_filter_ocorrencia = True
        base_filter_produto = True
        base_filter_planner = True
        base_filter_mensagem = True
    
    qtd_clientes = Cliente.query.filter(base_filter_cliente).count()
    qtd_mesas = MesaNegocio.query.filter(base_filter_mesa).count()
    qtd_ocorrencias = Ocorrencia.query.filter(base_filter_ocorrencia).count()

    # Contagem de agendas no dia de hoje
    hoje = datetime.today().date()
    qtd_agendas_hoje = PlannerEvento.query.filter(
        base_filter_planner,
        PlannerEvento.data == hoje
    ).count()

    # Agendas da semana (próximos 7 dias)
    data_inicio_semana = hoje
    data_fim_semana = hoje + timedelta(days=7)
    qtd_agendas_semana = PlannerEvento.query.filter(
        base_filter_planner,
        PlannerEvento.data >= data_inicio_semana,
        PlannerEvento.data < data_fim_semana
    ).count()

    # Agendas do mês (mes atual)
    primeiro_dia_mes = hoje.replace(day=1)
    if hoje.month == 12:
        ultimo_dia_mes = primeiro_dia_mes.replace(year=hoje.year + 1, month=1) - timedelta(days=1)
    else:
        ultimo_dia_mes = primeiro_dia_mes.replace(month=hoje.month + 1) - timedelta(days=1)
    qtd_agendas_mes = PlannerEvento.query.filter(
        base_filter_planner,
        PlannerEvento.data >= primeiro_dia_mes,
        PlannerEvento.data <= ultimo_dia_mes
    ).count()

    # Pessoas físicas / jurídicas
    qtd_pf = Cliente.query.filter(base_filter_cliente, Cliente.tipo_pessoa == 'Física').count()
    qtd_pj = Cliente.query.filter(base_filter_cliente, Cliente.tipo_pessoa == 'Jurídica').count()

    # Mesas de negócio por situação
    qtd_mesas_andamento = MesaNegocio.query.filter(base_filter_mesa, MesaNegocio.situacao == 'Em negociação').count()
    qtd_mesas_ganhas = MesaNegocio.query.filter(base_filter_mesa, MesaNegocio.situacao == 'Ganho').count()
    qtd_mesas_perdidas = MesaNegocio.query.filter(base_filter_mesa, MesaNegocio.situacao == 'Perdido').count()

    # Valor total por situação (funil de vendas)
    from sqlalchemy import func
    valor_mesas_andamento = db.session.query(func.sum(MesaNegocio.valor_total)).filter(
        base_filter_mesa,
        MesaNegocio.situacao == 'Em negociação'
    ).scalar() or 0
    valor_mesas_ganhas = db.session.query(func.sum(MesaNegocio.valor_total)).filter(
        base_filter_mesa,
        MesaNegocio.situacao == 'Ganho'
    ).scalar() or 0
    valor_mesas_perdidas = db.session.query(func.sum(MesaNegocio.valor_total)).filter(
        base_filter_mesa,
        MesaNegocio.situacao == 'Perdido'
    ).scalar() or 0

    # Valor de vendas por período (apenas mesas ganhas)
    # Vendas do dia
    valor_vendas_dia = db.session.query(func.sum(MesaNegocio.valor_total)).filter(
        base_filter_mesa,
        MesaNegocio.situacao == 'Ganho',
        MesaNegocio.data_registro == hoje
    ).scalar() or 0
    
    # Vendas da semana
    valor_vendas_semana = db.session.query(func.sum(MesaNegocio.valor_total)).filter(
        base_filter_mesa,
        MesaNegocio.situacao == 'Ganho',
        MesaNegocio.data_registro >= data_inicio_semana,
        MesaNegocio.data_registro < data_fim_semana
    ).scalar() or 0
    
    # Vendas do mês
    valor_vendas_mes = db.session.query(func.sum(MesaNegocio.valor_total)).filter(
        base_filter_mesa,
        MesaNegocio.situacao == 'Ganho',
        MesaNegocio.data_registro >= primeiro_dia_mes,
        MesaNegocio.data_registro <= ultimo_dia_mes
    ).scalar() or 0

    # Ocorrências por status
    qtd_ocorrencias_ativo = Ocorrencia.query.filter(base_filter_ocorrencia, Ocorrencia.status == 'Ativo').count()
    qtd_ocorrencias_resolvido = Ocorrencia.query.filter(base_filter_ocorrencia, Ocorrencia.status == 'Resolvido').count()
    qtd_ocorrencias_cancelado = Ocorrencia.query.filter(base_filter_ocorrencia, Ocorrencia.status == 'Cancelado').count()

    # Produtos cadastrados
    qtd_produtos = Produto.query.filter(base_filter_produto).count()

    # Mensagens pendentes: contar números únicos que têm mensagem de cliente não respondida
    # Buscar último remetente de cada conversa e contar quantas terminam com "Cliente"
    from sqlalchemy import func
    
    # Subquery para pegar a última mensagem de cada número
    ultima_msg_subq = db.session.query(
        WhatsAppMensagem.numero,
        func.max(WhatsAppMensagem.recebido_em).label('ultima_data')
    ).filter(base_filter_mensagem).group_by(WhatsAppMensagem.numero).subquery()
    
    # Contar conversas onde a última mensagem é do Cliente
    qtd_mensagens_pendentes = db.session.query(WhatsAppMensagem).join(
        ultima_msg_subq,
        db.and_(
            WhatsAppMensagem.numero == ultima_msg_subq.c.numero,
            WhatsAppMensagem.recebido_em == ultima_msg_subq.c.ultima_data
        )
    ).filter(base_filter_mensagem, WhatsAppMensagem.remetente == "Cliente").count()

    return render_template(
        "menu.html",
        qtd_clientes=qtd_clientes,
        qtd_mesas=qtd_mesas,
        qtd_ocorrencias=qtd_ocorrencias,
        qtd_agendas_hoje=qtd_agendas_hoje,
        qtd_agendas_semana=qtd_agendas_semana,
        qtd_agendas_mes=qtd_agendas_mes,
        qtd_pf=qtd_pf,
        qtd_pj=qtd_pj,
        qtd_mesas_andamento=qtd_mesas_andamento,
        qtd_mesas_ganhas=qtd_mesas_ganhas,
        qtd_mesas_perdidas=qtd_mesas_perdidas,
        qtd_ocorrencias_ativo=qtd_ocorrencias_ativo,
        qtd_ocorrencias_resolvido=qtd_ocorrencias_resolvido,
        qtd_ocorrencias_cancelado=qtd_ocorrencias_cancelado,
        qtd_produtos=qtd_produtos,
        valor_mesas_andamento=valor_mesas_andamento,
        valor_mesas_ganhas=valor_mesas_ganhas,
        valor_mesas_perdidas=valor_mesas_perdidas,
        valor_vendas_dia=valor_vendas_dia,
        valor_vendas_semana=valor_vendas_semana,
        valor_vendas_mes=valor_vendas_mes,
        qtd_mensagens_pendentes=qtd_mensagens_pendentes
    )


# --- NPS (NET PROMOTER SCORE)
@app.route("/nps")
@login_required
@permission_required('nps')
def nps():
    # Buscar todos os clientes que responderam NPS (filtrar por usuário)
    user_id = get_usuario_filter()
    if user_id:
        clientes_nps = Cliente.query.filter(
            Cliente.usuario_crm_id == user_id,
            Cliente.nps_nota.isnot(None)
        ).order_by(Cliente.nps_data.desc()).all()
    else:
        clientes_nps = Cliente.query.filter(Cliente.nps_nota.isnot(None)).order_by(Cliente.nps_data.desc()).all()
    
    total_respostas = len(clientes_nps)
    
    if total_respostas == 0:
        return render_template(
            "nps.html",
            nps_score=0,
            nps_classificacao="Sem dados",
            qtd_promotores=0,
            qtd_neutros=0,
            qtd_detratores=0,
            perc_promotores=0,
            perc_neutros=0,
            perc_detratores=0,
            clientes_nps=[],
            distribuicao_notas=[0]*11,
            evolucao_datas=[],
            evolucao_scores=[]
        )
    
    # Calcular NPS
    promotores = [c for c in clientes_nps if c.nps_nota >= 9]
    neutros = [c for c in clientes_nps if 7 <= c.nps_nota <= 8]
    detratores = [c for c in clientes_nps if c.nps_nota <= 6]
    
    qtd_promotores = len(promotores)
    qtd_neutros = len(neutros)
    qtd_detratores = len(detratores)
    
    perc_promotores = round((qtd_promotores / total_respostas) * 100, 1)
    perc_detratores = round((qtd_detratores / total_respostas) * 100, 1)
    perc_neutros = round((qtd_neutros / total_respostas) * 100, 1)
    
    nps_score = round(perc_promotores - perc_detratores, 1)
    
    # Classificação do NPS
    if nps_score >= 75:
        nps_classificacao = "Excelente 🌟"
    elif nps_score >= 50:
        nps_classificacao = "Muito Bom 👍"
    elif nps_score >= 0:
        nps_classificacao = "Razoável 😐"
    else:
        nps_classificacao = "Crítico ⚠️"
    
    # Distribuição de notas (0 a 10)
    distribuicao_notas = [0] * 11
    for cliente in clientes_nps:
        distribuicao_notas[cliente.nps_nota] += 1
    
    # Evolução do NPS (últimos 30 dias)
    from datetime import timedelta
    hoje = datetime.now()
    inicio = hoje - timedelta(days=30)
    
    evolucao_datas = []
    evolucao_scores = []
    
    for i in range(30):
        data = inicio + timedelta(days=i)
        # Clientes que responderam até essa data
        clientes_ate_data = [c for c in clientes_nps if c.nps_data and c.nps_data.date() <= data.date()]
        
        if clientes_ate_data:
            promo = len([c for c in clientes_ate_data if c.nps_nota >= 9])
            detra = len([c for c in clientes_ate_data if c.nps_nota <= 6])
            total = len(clientes_ate_data)
            
            score = round(((promo / total) - (detra / total)) * 100, 1)
            evolucao_scores.append(score)
        else:
            evolucao_scores.append(0)
        
        evolucao_datas.append(data.strftime('%d/%m'))
    
    return render_template(
        "nps.html",
        nps_score=nps_score,
        nps_classificacao=nps_classificacao,
        qtd_promotores=qtd_promotores,
        qtd_neutros=qtd_neutros,
        qtd_detratores=qtd_detratores,
        perc_promotores=perc_promotores,
        perc_neutros=perc_neutros,
        perc_detratores=perc_detratores,
        clientes_nps=clientes_nps,
        distribuicao_notas=distribuicao_notas,
        evolucao_datas=evolucao_datas,
        evolucao_scores=evolucao_scores
    )


# --- RELACIONAMENTO
@app.route("/relacionamento")
@login_required
@permission_required('clientes')
def relacionamento():
    user_id = get_usuario_filter()
    if user_id:
        clientes = Cliente.query.filter_by(usuario_crm_id=user_id).all()
    else:
        clientes = Cliente.query.all()
    return render_template("relacionamento.html", clientes=clientes)

@app.route("/cliente/<int:id>")
@login_required
@permission_required('clientes')
def detalhe_cliente(id): 
    cliente = Cliente.query.get_or_404(id)
    return render_template("detalhe_cliente.html", cliente=cliente)

@app.route("/cliente/<int:id>/novo")
@login_required
@permission_required('clientes')
def detalhe_cliente_novo(id):
    cliente = Cliente.query.get_or_404(id)
    
    # Calcular idade se tiver data de nascimento
    idade = None
    if cliente.data_nascimento:
        from datetime import date
        hoje = date.today()
        idade = hoje.year - cliente.data_nascimento.year
        # Ajustar se ainda não fez aniversário este ano
        if (hoje.month, hoje.day) < (cliente.data_nascimento.month, cliente.data_nascimento.day):
            idade -= 1
    
    return render_template("detalhe_cliente_novo.html", cliente=cliente, idade=idade)

@app.route("/cliente/<int:id>/editar", methods=["GET", "POST"])
@login_required
@permission_required('clientes')
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == "POST":
        cliente.nome = request.form.get('nome', cliente.nome)
        cliente.email = request.form.get('email', cliente.email)
        cliente.telefone = request.form.get('telefone', cliente.telefone)
        cliente.endereco = request.form.get('endereco', cliente.endereco)
        cliente.segmento = request.form.get('segmento', cliente.segmento)
        
        # Pessoa Física
        if 'data_nascimento' in request.form and request.form.get('data_nascimento'):
            try:
                cliente.data_nascimento = datetime.strptime(request.form.get('data_nascimento'), '%Y-%m-%d').date()
            except:
                pass
        
        if 'renda' in request.form and request.form.get('renda'):
            try:
                cliente.renda = float(request.form.get('renda'))
            except:
                pass
        
        cliente.segmento_trabalho = request.form.get('segmento_trabalho', cliente.segmento_trabalho)
        
        # Pessoa Jurídica
        if 'data_abertura' in request.form and request.form.get('data_abertura'):
            try:
                cliente.data_abertura = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d').date()
            except:
                pass
        
        if 'faturamento' in request.form and request.form.get('faturamento'):
            try:
                cliente.faturamento = float(request.form.get('faturamento'))
            except:
                pass
        
        if 'qtd_funcionarios' in request.form and request.form.get('qtd_funcionarios'):
            try:
                cliente.qtd_funcionarios = int(request.form.get('qtd_funcionarios'))
            except:
                pass
        
        # Observações gerais
        cliente.observacoes = request.form.get('observacoes', cliente.observacoes)
        
        db.session.commit()
        return redirect(url_for('detalhe_cliente_novo', id=cliente.id))
    
    return render_template("editar_cliente.html", cliente=cliente)

@app.route("/cliente/<int:id>/observacoes", methods=["POST"])
@login_required
@permission_required('clientes')
def atualizar_observacoes(id):
    cliente = Cliente.query.get_or_404(id)
    cliente.observacoes = request.form.get('observacoes', '')
    db.session.commit()
    flash('Observações atualizadas com sucesso!', 'success')
    return redirect(url_for('detalhe_cliente_novo', id=cliente.id))

# --- MESAS DE NEGÓCIO
@app.route("/cliente/<int:id>/add_mesa", methods=["GET", "POST"])
@login_required
@permission_required('mesas')
def add_mesa(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == "POST":
        situacao = request.form["situacao"]
        mesa = MesaNegocio(
            usuario_crm_id=current_user.get_usuario_principal_id(),
            cliente_id=id,
            topico=request.form["topico"],
            produtos=request.form["produtos"],
            situacao=situacao,
            valor_total=float(request.form["valor_total"]),
            descricao=request.form.get("descricao"),
            data_registro=datetime.today().date(),
            hora_registro=datetime.now().time()
        )
        db.session.add(mesa)
        db.session.commit()
        
        # Se criou a mesa já como "Ganho", enviar NPS
        if situacao == "Ganho":
            print(f"🔍 Mesa criada como Ganho. Enviando NPS para {cliente.nome}")
            try:
                resultado = enviar_pesquisa_nps(cliente)
                if resultado:
                    flash(f"✅ Mesa criada e pesquisa NPS enviada para {cliente.nome}!", "success")
                else:
                    flash("⚠️ Mesa criada, mas houve erro ao enviar pesquisa NPS.", "warning")
            except Exception as e:
                flash(f"⚠️ Mesa criada, mas erro ao enviar NPS: {str(e)}", "warning")
                print(f"❌ ERRO ao enviar NPS: {str(e)}")
        
        return redirect(url_for("mesas_negocio"))
    return render_template("add_mesa.html", cliente=cliente)

@app.route("/mesas_negocio")
@login_required
@permission_required('mesas')
def mesas_negocio():
    user_id = get_usuario_filter()
    if user_id:
        mesas = MesaNegocio.query.filter_by(usuario_crm_id=user_id).all()
    else:
        mesas = MesaNegocio.query.all()
    return render_template("mesas_negocio.html", mesas=mesas)

@app.route("/mesas/<int:id>")
@login_required
@permission_required('mesas')
def detalhe_mesa(id):
    mesa = MesaNegocio.query.get_or_404(id)
    return render_template("detalhe_mesa.html", mesa=mesa)

# --- OCORRÊNCIAS
@app.route("/cliente/<int:id>/add_ocorrencia", methods=["GET", "POST"])
@login_required
@permission_required('ocorrencias')
def add_ocorrencia(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == "POST":
        ocorrencia = Ocorrencia(
            usuario_crm_id=current_user.get_usuario_principal_id(),
            cliente_id=id,
            topico=request.form["topico"],
            status=request.form["status"],
            descricao=request.form["descricao"],
            data_registro=datetime.today().date(),
            hora_registro=datetime.now().time()
        )
        db.session.add(ocorrencia)
        db.session.commit()
        return redirect(url_for("ocorrencias"))
    return render_template("add_ocorrencia.html", cliente=cliente)

@app.route("/ocorrencias")
@login_required
@permission_required('ocorrencias')
def ocorrencias():
    user_id = get_usuario_filter()
    if user_id:
        ocorrencias = Ocorrencia.query.filter_by(usuario_crm_id=user_id).all()
    else:
        ocorrencias = Ocorrencia.query.all()
    return render_template("ocorrencias.html", ocorrencias=ocorrencias)

@app.route("/ocorrencia/<int:id>")
@login_required
@permission_required('ocorrencias')
def detalhe_ocorrencia(id):
    ocorrencia = Ocorrencia.query.get_or_404(id)
    # pega o cliente se houver relação
    cliente = ocorrencia.cliente if hasattr(ocorrencia, 'cliente') else None
    return render_template("detalhe_ocorrencia.html", ocorrencia=ocorrencia, cliente=cliente)

@app.route("/ocorrencia/<int:id>/atualizar", methods=["POST"])
@login_required
@permission_required('ocorrencias')
def atualizar_ocorrencia(id):
    ocorrencia = Ocorrencia.query.get_or_404(id)
    situacao = request.form.get("situacao")
    if situacao:
        ocorrencia.status = situacao
        db.session.commit()
    return redirect(url_for("ocorrencias"))

# --- CADASTRO CLIENTE
@app.route("/cadastro", methods=["GET", "POST"])
@login_required
@permission_required('clientes')
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        tipo_pessoa = request.form["tipo_pessoa"]

        cliente = Cliente(
            usuario_crm_id=current_user.get_usuario_principal_id(),
            nome=nome, 
            telefone=telefone, 
            email=email, 
            tipo_pessoa=tipo_pessoa
        )

        if tipo_pessoa == "Física":
            if request.form.get("data_nascimento"):
                cliente.data_nascimento = datetime.strptime(request.form["data_nascimento"], "%Y-%m-%d").date()
            cliente.renda = request.form.get("renda") or None
            cliente.segmento_trabalho = request.form.get("segmento_trabalho")
            cliente.endereco = request.form.get("endereco")
        else:
            if request.form.get("data_abertura"):
                cliente.data_abertura = datetime.strptime(request.form["data_abertura"], "%Y-%m-%d").date()
            cliente.faturamento = request.form.get("faturamento") or None
            cliente.segmento = request.form.get("segmento")
            cliente.endereco = request.form.get("endereco")
            cliente.qtd_funcionarios = request.form.get("qtd_funcionarios") or None

        db.session.add(cliente)
        db.session.commit()
        return redirect(url_for("cadastro"))

    # 🔹 Lista de clientes mostrada na página
    user_id = get_usuario_filter()
    if user_id:
        clientes = Cliente.query.filter_by(usuario_crm_id=user_id).all()
    else:
        clientes = Cliente.query.all()
    return render_template("cadastro.html", clientes=clientes)


@app.route("/cliente/<int:id>/excluir", methods=["POST"])
@login_required
@permission_required('clientes')
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    # Excluir todas as ocorrências vinculadas
    if cliente.ocorrencias:
        for ocorrencia in cliente.ocorrencias:
            db.session.delete(ocorrencia)
    
    # Excluir todas as mesas vinculadas
    if cliente.mesas:
        for mesa in cliente.mesas:
            db.session.delete(mesa)
    
    # Excluir o cliente
    db.session.delete(cliente)
    db.session.commit()
    
    flash(f"Cliente '{cliente.nome}' e todos os seus dados foram excluídos com sucesso!", "success")
    return redirect(url_for('cadastro'))

@app.route("/cliente/<int:id>/delete", methods=["POST"])
@login_required
@permission_required('clientes')
def deletar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash("Cliente excluído com sucesso!", "success")  # Mensagem verde
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir cliente: {str(e)}", "danger")  # Mensagem vermelha
    return redirect(url_for("cadastro"))

@app.route("/mesas/<int:id>/atualizar", methods=["POST"])
def atualizar_mesa(id):
    mesa = MesaNegocio.query.get_or_404(id)
    nova_situacao = request.form.get("situacao")

    if not nova_situacao:
        flash("Informe uma nova situação.", "danger")
        return redirect(url_for("detalhe_mesa", id=id))

    situacao_antiga = mesa.situacao
    mesa.situacao = nova_situacao
    db.session.commit()
    
    # Se a mesa foi marcada como "Ganho", enviar pesquisa de NPS
    if nova_situacao == "Ganho" and situacao_antiga != "Ganho":
        if mesa.cliente:
            print(f"🔍 DEBUG: Enviando NPS para cliente: {mesa.cliente.nome} - Tel: {mesa.cliente.telefone}")
            try:
                resultado = enviar_pesquisa_nps(mesa.cliente)
                if resultado:
                    flash(f"✅ Situação atualizada e pesquisa NPS enviada com sucesso para {mesa.cliente.nome}!", "success")
                    print(f"✅ NPS enviado com sucesso para {mesa.cliente.nome}")
                else:
                    flash("⚠️ Situação atualizada, mas houve erro ao enviar pesquisa NPS.", "warning")
                    print(f"❌ Erro ao enviar NPS para {mesa.cliente.nome}")
            except Exception as e:
                flash(f"⚠️ Situação atualizada, mas houve erro ao enviar pesquisa NPS: {str(e)}", "warning")
                print(f"❌ ERRO ao enviar NPS: {str(e)}")
        else:
            flash("⚠️ Situação atualizada, mas esta mesa não possui cliente vinculado para enviar NPS.", "warning")
            print("❌ Mesa sem cliente vinculado")
    else:
        flash("Situação atualizada com sucesso!", "success")

    return redirect(url_for("detalhe_mesa", id=id))

# --- WHATSAPP
@app.route("/whatsapp")
@login_required
@permission_required('whatsapp')
def whatsapp_index():
    # Verificar se o usuário tem API configurada
    usuario_principal_id = current_user.get_usuario_principal_id()
    usuario_principal = UsuarioCRM.query.get(usuario_principal_id)
    
    if not usuario_principal or not usuario_principal.tem_api_configurada():
        flash('As credenciais da API Z-API não foram configuradas. Entre em contato com o administrador.', 'warning')
        return render_template('api_nao_configurada.html', modulo='WhatsApp')
    
    user_id = get_usuario_filter()
    if user_id:
        mensagens = WhatsAppMensagem.query.filter_by(usuario_crm_id=user_id).all()
    else:
        mensagens = WhatsAppMensagem.query.all()
    return render_template("whatsapp.html", mensagens=mensagens)



@app.route("/whatsapp/enviar", methods=["POST"])
@login_required
@permission_required('whatsapp')
def whatsapp_enviar():
    data = request.get_json(silent=True)
    if data:
        numero = data.get("numero")
        mensagem = data.get("mensagem")
    else:
        numero = request.form.get("numero")
        mensagem = request.form.get("mensagem")

    if not numero or not mensagem:
        return render_template("mensagem_status.html", status="erro", voltar_url=url_for("whatsapp_index"))

    # Usar as credenciais do usuário principal (cliente)
    usuario_principal_id = current_user.get_usuario_principal_id()
    usuario_principal = UsuarioCRM.query.get(usuario_principal_id)
    
    if not usuario_principal or not usuario_principal.tem_api_configurada():
        return render_template("mensagem_status.html", status="erro", voltar_url=url_for("whatsapp_index"))
    
    resultado = enviar_whatsapp_zapi(numero, mensagem, usuario_principal.api_instance, usuario_principal.api_token)

    if resultado["status"] == "Sucesso":
        return render_template("mensagem_status.html", status="sucesso", voltar_url=url_for("whatsapp_index"))
    else:
        return render_template("mensagem_status.html", status="erro", voltar_url=url_for("whatsapp_index"))

@app.route("/canais/webhook", methods=["POST"])
@app.route("/webhook/messages", methods=["POST"])
def receber_mensagem_webhook():
    data = request.get_json(silent=True) or {}

    print("📩 Webhook recebido (raw):", data)

    # tenta extrair telefone a partir de várias chaves comuns
    phone = None
    # chaves diretas
    for k in ("phone", "from", "from_number", "sender", "contact", "wa_id", "number"):
        v = data.get(k)
        if v:
            phone = v
            break

    # se ainda não encontrou, procura recursivamente por campos que pareçam telefone
    def find_phone(obj):
        if isinstance(obj, dict):
            for kk, vv in obj.items():
                if kk.lower() in ("phone", "from", "number", "wa_id", "id", "contact") and vv:
                    return vv
                res = find_phone(vv)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = find_phone(item)
                if res:
                    return res
        return None

    if not phone:
        phone = find_phone(data)

    # tenta extrair texto em formatos comuns (apenas campos explícitos)
    text = None
    explicit_text = None
    txt = data.get("text")
    if isinstance(txt, dict):
        explicit_text = txt.get("message") or txt.get("body") or txt.get("text")
    elif isinstance(txt, str):
        explicit_text = txt
    explicit_text = explicit_text or data.get("message") or data.get("body") or data.get("text_message")

    # filtra callbacks que não são mensagens (presença/status) quando possível
    tipo = data.get("type", "").lower()
    non_message_types = ("presencechatcallback", "messagestatuscallback", "deliverycallback", "messagestatuscallback")

    # se for um tipo claramente não-mensagem e não houver texto explícito (campo text/message/body), ignorar
    if tipo in non_message_types and not explicit_text:
        print(f"Webhook ignorado (tipo {data.get('type')} sem texto explícito)")
        return {"status": "ignored"}, 200

    # agora tenta encontrar texto recursivamente, MAS apenas buscando campos nominais (message/body/text/caption)
    def find_text(obj):
        if isinstance(obj, dict):
            for kk, vv in obj.items():
                if kk.lower() in ("message", "body", "text", "caption") and isinstance(vv, str):
                    return vv
                res = find_text(vv)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = find_text(item)
                if res:
                    return res
        return None

    # prefer explicit_text quando existir, senão use find_text
    text = explicit_text or find_text(data)

    # filtra callbacks que não são mensagens (presença/status) quando possível
    tipo = data.get("type", "").lower()
    non_message_types = ("presencechatcallback", "messagestatuscallback", "deliverycallback", "messageStatusCallback")

    # se for um tipo claramente não-mensagem e não houver texto extraído, ignorar
    if tipo in non_message_types and not text:
        print(f"Webhook ignorado (tipo {data.get('type')} sem texto)")
        return {"status": "ignored"}, 200

    if not phone or not text:
        print("Webhook ignorado: phone/text não encontrados")
        return {"status": "ignored"}, 200

    # evita salvar valores como instanceId que foram capturados como 'text'
    if isinstance(text, str) and text == data.get("instanceId"):
        print("Webhook ignorado: texto igual a instanceId")
        return {"status": "ignored"}, 200

    # NORMALIZAR número usando a mesma função em todo o sistema
    numero = normalize_phone(phone)

    # salvar no banco (WhatsAppMensagem) com número NORMALIZADO
    msg = WhatsAppMensagem(
        numero=numero,
        remetente="Cliente",
        mensagem=text,
        recebido_em=datetime.utcnow()
    )
    db.session.add(msg)
    db.session.commit()

    # Verificar se é resposta de NPS
    print(f"\n🔍 === WEBHOOK: VERIFICANDO NPS ===")
    print(f"📞 Número recebido: {phone}")
    print(f"📞 Número normalizado: {numero}")
    
    # Usar função inteligente para buscar cliente
    cliente = find_cliente_by_phone(numero)
    
    if cliente:
        print(f"✅ Cliente encontrado: {cliente.nome} (Tel: {cliente.telefone})")
        print(f"⏳ Aguardando NPS? {cliente.aguardando_nps}")
        
        if cliente.aguardando_nps:
            print(f"📊 Processando resposta de NPS...")
            resultado = processar_resposta_nps(cliente, text)
            if resultado:
                print(f"✅ Resposta NPS processada com sucesso!")
            else:
                print(f"⚠️ Texto não era uma resposta válida de NPS")
        else:
            print(f"ℹ️ Cliente não está aguardando NPS")
    else:
        print(f"❌ Cliente não encontrado para o número {numero}")
        # Listar alguns clientes para debug
        alguns_clientes = Cliente.query.limit(5).all()
        print(f"📋 Primeiros clientes no banco:")
        for c in alguns_clientes:
            print(f"  - {c.nome}: {c.telefone}")

    # emitir para a sala correta
    # Buscar nome do cliente para enviar no payload
    cliente_found = find_cliente_by_phone(numero)
    nome_cliente = cliente_found.nome if cliente_found else numero
    
    payload = {
        "id": msg.id,
        "numero": numero,
        "nome": nome_cliente,
        "remetente": "Cliente",
        "mensagem": text,
        "hora": datetime.now().strftime("%H:%M")
    }

    # Emitir apenas para a sala do número normalizado (evita duplicação)
    try:
        socketio.emit("nova_mensagem", payload, room=numero)
        print(f"✅ Mensagem emitida para sala: {numero}")
    except Exception as e:
        print(f"❌ Erro ao emitir mensagem: {e}")

    return {"status": "ok"}, 200

@socketio.on('join')
def join_room_event(data):
    numero = data.get("numero")
    if not numero:
        return

    # Normalizar e entrar apenas na sala do número completo (evita duplicação)
    numero_norm = normalize_phone(numero)
    if not numero_norm:
        return
    
    join_room(numero_norm)
    print(f"🔵 Usuário entrou na sala: {numero_norm}")

@app.route("/canais/enviar", methods=["POST"])
@login_required
def enviar_mensagem_canais():
    data = request.get_json()
    numero = data.get("numero")
    mensagem = data.get("mensagem")

    if not numero or not mensagem:
        return jsonify({"status": "Erro"}), 400

    numero_norm = normalize_phone(numero)
    
    # Usar as credenciais do usuário principal (cliente)
    usuario_principal_id = current_user.get_usuario_principal_id()
    usuario_principal = UsuarioCRM.query.get(usuario_principal_id)
    
    if not usuario_principal or not usuario_principal.tem_api_configurada():
        return jsonify({"status": "Erro", "mensagem": "API não configurada"}), 400

    resultado = enviar_whatsapp_zapi(numero_norm, mensagem, usuario_principal.api_instance, usuario_principal.api_token)

    if resultado["status"] == "Sucesso":
        # salvar no banco vinculado ao usuario
        msg = WhatsAppMensagem(
            numero=numero_norm,
            remetente="Você",
            mensagem=mensagem,
            recebido_em=datetime.utcnow(),
            usuario_crm_id=usuario_principal_id
        )
        db.session.add(msg)
        db.session.commit()

        # emitir para a sala
        # Buscar nome do cliente para enviar no payload
        cliente_found = find_cliente_by_phone(numero_norm)
        nome_cliente = cliente_found.nome if cliente_found else numero_norm
        
        payload = {
            "id": msg.id,
            "numero": numero_norm,
            "nome": nome_cliente,
            "remetente": "Você",
            "mensagem": mensagem,
            "hora": datetime.now().strftime("%H:%M")
        }
        try:
            socketio.emit("nova_mensagem", payload, room=numero_norm)
            print(f"✅ Mensagem 'Você' emitida para sala: {numero_norm}")
        except Exception as e:
            print(f"❌ Erro ao emitir: {e}")

        return jsonify({"status": "Sucesso"})

    return jsonify({"status": "Erro"})


# --- CHATBOT
@app.route("/chatbot", methods=["GET", "POST"])
@login_required
@permission_required('chatbot')
def configurar_chatbot():
    if request.method == "POST":
        palavra = request.form["palavra_chave"]
        resposta = request.form["resposta"]
        user_id = get_usuario_filter()
        regra = ChatbotRegra(
            palavra_chave=palavra, 
            resposta=resposta,
            usuario_crm_id=user_id if user_id else current_user.id
        )
        db.session.add(regra)
        db.session.commit()

@app.route("/mensagens")
@login_required
@permission_required('whatsapp')
def mensagens():
    user_id = get_usuario_filter()
    if user_id:
        mensagens = WhatsAppMensagem.query.filter_by(usuario_crm_id=user_id).order_by(WhatsAppMensagem.recebido_em.desc()).all()
    else:
        mensagens = WhatsAppMensagem.query.order_by(WhatsAppMensagem.recebido_em.desc()).all()
    return render_template("mensagens.html", mensagens=mensagens)

@app.route("/configuracoes", methods=["GET", "POST"])
@login_required
@permission_required('chatbot')
def configuracoes():
    user_id = get_usuario_filter()
    
    if request.method == "POST":
        palavra = request.form["palavra"]
        resposta = request.form["resposta"]
        prioridade = request.form["prioridade"]
        regra = ChatbotRegra(
            palavra_chave=palavra, 
            resposta=resposta, 
            prioridade=prioridade,
            usuario_crm_id=user_id if user_id else current_user.id
        )
        db.session.add(regra)
        db.session.commit()
        flash("Regra adicionada com sucesso!")
        return redirect(url_for("configuracoes"))

    # Filtrar regras por usuário
    if user_id:
        regras = ChatbotRegra.query.filter_by(usuario_crm_id=user_id).all()
    else:
        regras = ChatbotRegra.query.all()
    
    return render_template("configuracoes.html", regras=regras)

@app.route("/canais")
@login_required
def canais():
    # Verificar se o usuário tem API configurada
    usuario_principal_id = current_user.get_usuario_principal_id()
    usuario_principal = UsuarioCRM.query.get(usuario_principal_id)
    
    if not usuario_principal or not usuario_principal.tem_api_configurada():
        flash('As credenciais da API Z-API não foram configuradas. Entre em contato com o administrador.', 'warning')
        return render_template('api_nao_configurada.html', modulo='Canais')
    
    user_id = get_usuario_filter()
    if user_id:
        clientes = Cliente.query.filter_by(usuario_crm_id=user_id).order_by(Cliente.nome).all()
    else:
        clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("canais.html", clientes=clientes)


def normalize_phone(phone):
    """
    Normaliza número de telefone removendo caracteres não-numéricos.
    Para números brasileiros com celular, garante que tenha o 9 dígito (padrão 13 dígitos total).
    Formato esperado: 55 (país) + DD (DDD) + 9XXXXXXXX (celular com 9 dígitos)
    """
    import re
    numero = re.sub(r'\D', '', str(phone)) if phone else ''
    
    # Se é número brasileiro (começa com 55) e tem 12 dígitos
    # Adiciona o 9 extra para padronizar em 13 dígitos
    if numero.startswith('55') and len(numero) == 12:
        # DDD começa na posição 2 (após '55')
        # Número do celular começa na posição 4
        # Celulares brasileiros devem ter 9 dígitos (9XXXX-XXXX)
        # Se tem 12 dígitos, está faltando um 9, então adiciona
        numero = numero[:4] + '9' + numero[4:]
        print(f"🔧 Número ajustado de 12 para 13 dígitos")
    
    return numero

def find_cliente_by_phone(numero_normalizado):
    """
    Busca cliente por telefone com lógica inteligente que considera variações:
    - Tenta match exato
    - Tenta comparar últimos 9 dígitos (número sem DDD)
    - Tenta comparar últimos 11 dígitos (DDD + número)
    - Tenta remover o código de país (55)
    - Tenta remover 9 extra no início
    - Tenta buscar número com 1 dígito a menos/mais
    """
    if not numero_normalizado:
        return None
    
    # Obter todos os clientes
    clientes = Cliente.query.all()
    
    for c in clientes:
        tel_norm = normalize_phone(c.telefone)
        
        # Match exato
        if tel_norm == numero_normalizado:
            return c
        
        # Tenta comparar últimos 9 dígitos (número puro sem DDD)
        if len(tel_norm) >= 9 and len(numero_normalizado) >= 9:
            if tel_norm[-9:] == numero_normalizado[-9:]:
                return c
        
        # Tenta comparar últimos 11 dígitos (DDD + número)
        if len(tel_norm) >= 11 and len(numero_normalizado) >= 11:
            if tel_norm[-11:] == numero_normalizado[-11:]:
                return c
        
        # Remove código de país (55) e compara
        tel_sem_55 = tel_norm[2:] if tel_norm.startswith('55') else tel_norm
        num_sem_55 = numero_normalizado[2:] if numero_normalizado.startswith('55') else numero_normalizado
        
        if tel_sem_55 and num_sem_55 and tel_sem_55 == num_sem_55:
            return c
        
        # Remove 9 extra no início (se houver)
        tel_sem_9 = tel_norm[1:] if tel_norm.startswith('9') and len(tel_norm) > 10 else tel_norm
        num_sem_9 = numero_normalizado[1:] if numero_normalizado.startswith('9') and len(numero_normalizado) > 10 else numero_normalizado
        
        if tel_sem_9 and num_sem_9 and tel_sem_9 == num_sem_9:
            return c
        
        # Tenta match com 1 dígito a menos (número está incompleto)
        # Ex: 554799471874 (12 dígitos) vs 5547999471874 (13 dígitos)
        if len(tel_norm) == len(numero_normalizado) + 1:
            # Tenta remover cada dígito do tel_norm e comparar
            for i in range(len(tel_norm)):
                tel_sem_um = tel_norm[:i] + tel_norm[i+1:]
                if tel_sem_um == numero_normalizado:
                    return c
        
        # Tenta match com 1 dígito a mais (número tem dígito extra)
        if len(numero_normalizado) == len(tel_norm) + 1:
            # Tenta remover cada dígito do numero_normalizado e comparar
            for i in range(len(numero_normalizado)):
                num_sem_um = numero_normalizado[:i] + numero_normalizado[i+1:]
                if num_sem_um == tel_norm:
                    return c
    
    return None

@app.route("/canais/ultimas")
@login_required
def ultimas_notificacoes():
    """
    Retorna as últimas mensagens recebidas agrupadas por número de telefone NORMALIZADO.
    Para cada número, retorna apenas a mensagem mais recente.
    Evita duplicações normalizando TODOS os números antes de agrupar.
    Filtrado por usuário.
    """
    from sqlalchemy import func
    
    user_id = get_usuario_filter()
    
    # Obter todas as mensagens filtradas por usuário
    if user_id:
        all_msgs = db.session.query(WhatsAppMensagem).filter_by(
            usuario_crm_id=user_id
        ).order_by(WhatsAppMensagem.recebido_em.desc()).all()
    else:
        all_msgs = db.session.query(WhatsAppMensagem).order_by(
            WhatsAppMensagem.recebido_em.desc()
        ).all()
    
    # Agrupar por número normalizado, mantendo apenas a mais recente
    conversas_dict = {}
    for msg in all_msgs:
        # SEMPRE normalizar o número
        numero_norm = normalize_phone(msg.numero)
        
        if not numero_norm:
            continue  # Pular se não conseguiu normalizar
        
        # Se este número normalizado ainda não foi visto, salvar
        if numero_norm not in conversas_dict:
            conversas_dict[numero_norm] = msg
    
    # Construir resultado
    resultado = []
    for numero_norm, msg in conversas_dict.items():
        # Buscar cliente usando a função inteligente
        cliente = find_cliente_by_phone(numero_norm)
        nome = cliente.nome if cliente else numero_norm
        
        # Verificar se a última mensagem é do cliente (não respondida)
        # Se remetente é "Cliente", significa que o cliente enviou e ainda não foi respondido
        nao_respondida = msg.remetente == "Cliente"
        
        resultado.append({
            "numero": numero_norm,  # SEMPRE usar número normalizado
            "nome": nome,
            "mensagem": msg.mensagem,
            "recebido_em": msg.recebido_em.strftime("%Y-%m-%d %H:%M:%S"),
            "nao_respondida": nao_respondida
        })
    
    # Ordenar por data (mais recentes primeiro)
    resultado.sort(key=lambda x: x['recebido_em'], reverse=True)
    
    print(f"📤 Retornando {len(resultado)} conversas únicas para o frontend")
    
    return jsonify(resultado[:20])  # Limitar a 20 conversas


@app.route("/api/clientes/busca")
@login_required
def buscar_clientes():
    q = request.args.get("q", "").strip()

    if len(q) < 2:
        return jsonify([])

    user_id = get_usuario_filter()
    
    # Filtrar clientes por usuário
    if user_id:
        clientes = Cliente.query.filter(
            and_(
                or_(
                    Cliente.nome.ilike(f"%{q}%"),
                    Cliente.telefone.ilike(f"%{q}%")
                ),
                Cliente.usuario_crm_id == user_id
            )
        ).limit(20).all()
    else:
        clientes = Cliente.query.filter(
            or_(
                Cliente.nome.ilike(f"%{q}%"),
                Cliente.telefone.ilike(f"%{q}%")
            )
        ).limit(20).all()

    return jsonify([
        {
            "id": c.id,
            "nome": c.nome,
            "telefone": c.telefone
        }
        for c in clientes
    ])

@app.route("/api/produtos/busca")
@login_required
def buscar_produtos():
    """API para buscar produtos com pesquisa - filtrado por usuario"""
    q = request.args.get("q", "").strip()
    user_id = get_usuario_filter()
    
    # Construir query base com filtro de usuário
    if user_id:
        query = Produto.query.filter_by(usuario_crm_id=user_id)
    else:
        query = Produto.query

    if len(q) >= 1:
        # Buscar por nome ou descrição
        query = query.filter(
            or_(
                Produto.nome.ilike(f"%{q}%"),
                Produto.descricao.ilike(f"%{q}%")
            )
        )
    
    produtos = query.limit(50).all()

    return jsonify([
        {
            "id": p.id,
            "nome": p.nome,
            "descricao": p.descricao,
            "quantidade": p.quantidade
        }
        for p in produtos
    ])

# busca histórico por número (usa numero como string)
@app.route("/canais/<string:numero>/mensagens")
@login_required
def carregar_mensagens(numero):
    # normalizar numero (remover espaços/+ e caracteres não numéricos)
    numero_norm = normalize_phone(numero)
    user_id = get_usuario_filter()
    
    # busca por número normalizado e filtrado por usuário
    if user_id:
        msgs = WhatsAppMensagem.query.filter_by(
            numero=numero_norm,
            usuario_crm_id=user_id
        ).order_by(WhatsAppMensagem.recebido_em.asc()).all()
    else:
        msgs = WhatsAppMensagem.query.filter_by(numero=numero_norm).order_by(
            WhatsAppMensagem.recebido_em.asc()
        ).all()
    
    mensagens_list = []
    for m in msgs:
        mensagens_list.append({
            "id": m.id,
            "remetente": m.remetente,
            "mensagem": m.mensagem,
            "hora": m.recebido_em.strftime("%Y-%m-%d %H:%M:%S")
        })
    # também devolve nome do cliente (se existir)
    cliente = Cliente.query.filter_by(telefone=numero_norm).first()
    nome = cliente.nome if cliente else numero_norm
    return jsonify({"cliente": {"numero": numero_norm, "nome": nome}, "mensagens": mensagens_list})

@app.route("/canais/<string:numero>/deletar", methods=["DELETE"])
@login_required
def deletar_conversa(numero):
    """
    Deleta todas as mensagens de uma conversa.
    """
    numero_norm = numero.replace("+", "").replace(" ", "").strip()
    user_id = get_usuario_filter()
    
    try:
        # Buscar todas as mensagens do número
        s6 = numero_norm[-6:] if len(numero_norm) >= 6 else None
        s8 = numero_norm[-8:] if len(numero_norm) >= 8 else None
        
        from sqlalchemy import or_, and_
        filters = [WhatsAppMensagem.numero == numero_norm]
        if s8:
            filters.append(WhatsAppMensagem.numero.like(f"%{s8}"))
        if s6:
            filters.append(WhatsAppMensagem.numero.like(f"%{s6}"))
        
        # Filtrar por usuário também
        if user_id:
            query = WhatsAppMensagem.query.filter(
                and_(
                    or_(*filters),
                    WhatsAppMensagem.usuario_crm_id == user_id
                )
            )
        else:
            query = WhatsAppMensagem.query.filter(or_(*filters))
        
        # Deletar mensagens
        query.delete()
        db.session.commit()
        
        return jsonify({"success": True, "message": "Conversa deletada com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/tickets/<int:ticket_id>/send", methods=["POST"])
def send_message(ticket_id):
    body = request.get_json()
    text = body.get("text")

    ticket = Ticket.query.get_or_404(ticket_id)

    response = requests.post(
        f"https://api.z-api.io/instances/SUA_INSTANCIA/token/SEU_TOKEN/send-text",
        json={
            "phone": ticket.contact_phone,
            "message": text
        }
    )

    msg_id = response.json().get("messageId")

    msg = Message(
        ticket_id=ticket.id,
        direction="out",
        body=text,
        external_id=msg_id
    )
    db.session.add(msg)
    db.session.commit()

    socketio.emit(
        "ticket_update",
        {"ticket_id": ticket.id},
        broadcast=True
    )

    return {"sent": True}


@app.route("/produtos")
@login_required
@permission_required('produtos')
def produtos():
    # página principal do controle de produtos
    return render_template("produtos.html")

# Endpoint para listar produtos (JSON) - usado pelo frontend para atualizar lista
@app.route("/api/produtos")
@login_required
def api_listar_produtos():
    user_id = get_usuario_filter()
    q = request.args.get("q", "").strip()
    
    if user_id:
        query = Produto.query.filter_by(usuario_crm_id=user_id)
    else:
        query = Produto.query
    
    if q:
        query = query.filter(Produto.nome.ilike(f"%{q}%"))
    produtos = query.order_by(Produto.nome).all()
    data = []
    for p in produtos:
        data.append({
            "id": p.id,
            "nome": p.nome,
            "descricao": p.descricao,
            "quantidade": p.quantidade,
            "ultima_movimentacao_data": p.ultima_movimentacao_data.strftime("%Y-%m-%d %H:%M:%S") if p.ultima_movimentacao_data else None,
            "ultima_movimentacao_descricao": p.ultima_movimentacao_descricao
        })
    return jsonify({"produtos": data})

# Cadastrar produto (via fetch / form)
@app.route("/api/produtos/add", methods=["POST"])
@login_required
def api_add_produto():
    dados = request.get_json() or {}
    nome = (dados.get("nome") or "").strip()
    descricao = (dados.get("descricao") or "").strip()
    if not nome:
        return jsonify({"status": "erro", "detalhe": "Nome é obrigatório"}), 400
    if not descricao:
        return jsonify({"status": "erro", "detalhe": "Descrição é obrigatória"}), 400

    # evita duplicados
    user_id = get_usuario_filter()
    if user_id:
        if Produto.query.filter_by(usuario_crm_id=user_id, nome=nome).first():
            return jsonify({"status": "erro", "detalhe": "Produto com esse nome já existe"}), 400
    else:
        if Produto.query.filter_by(nome=nome).first():
            return jsonify({"status": "erro", "detalhe": "Produto com esse nome já existe"}), 400

    p = Produto(
        usuario_crm_id=current_user.get_usuario_principal_id(),
        nome=nome, 
        descricao=descricao, 
        quantidade=0
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"status": "sucesso", "produto": {"id": p.id, "nome": p.nome}}), 201

# Realizar movimentação (entrada/saída)
@app.route("/api/produtos/<int:produto_id>/movimentar", methods=["POST"])
@login_required
def api_movimentar(produto_id):
    dados = request.get_json() or {}
    tipo = dados.get("tipo")  # 'entrada' ou 'saida'
    quantidade = dados.get("quantidade")
    descricao = (dados.get("descricao") or "").strip()

    if tipo not in ("entrada", "saida"):
        return jsonify({"status": "erro", "detalhe": "Tipo inválido"}), 400
    try:
        quantidade = int(quantidade)
    except Exception:
        return jsonify({"status": "erro", "detalhe": "Quantidade inválida"}), 400
    if quantidade <= 0:
        return jsonify({"status": "erro", "detalhe": "Quantidade deve ser maior que zero"}), 400
    if not descricao:
        return jsonify({"status": "erro", "detalhe": "Descrição (justificativa) é obrigatória"}), 400

    produto = Produto.query.get_or_404(produto_id)

    # valida saída
    if tipo == "saida" and produto.quantidade - quantidade < 0:
        return jsonify({"status": "erro", "detalhe": "Estoque insuficiente"}), 400

    # atualiza quantidade
    if tipo == "entrada":
        produto.quantidade += quantidade
    else:
        produto.quantidade -= quantidade

    # atualiza ultima movimentação
    produto.ultima_movimentacao_data = datetime.utcnow()
    produto.ultima_movimentacao_descricao = descricao

    # registra movimentacao
    mov = Movimentacao(
        produto=produto,
        tipo=tipo,
        quantidade=quantidade,
        descricao=descricao,
        data_registro=datetime.utcnow()
    )
    db.session.add(mov)
    db.session.commit()

    return jsonify({
        "status": "sucesso",
        "produto": {"id": produto.id, "quantidade": produto.quantidade},
        "movimentacao": {"id": mov.id}
    }), 200

# Histórico de movimentações de um produto (GET)
@app.route("/api/produtos/<int:produto_id>/historico")
def api_historico(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    movs = Movimentacao.query.filter_by(produto_id=produto.id).order_by(Movimentacao.data_registro.desc()).all()
    data = []
    for m in movs:
        data.append({
            "id": m.id,
            "tipo": m.tipo,
            "quantidade": m.quantidade,
            "descricao": m.descricao,
            "data_registro": m.data_registro.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"produto": {"id": produto.id, "nome": produto.nome}, "movimentacoes": data})

# Excluir produto
@app.route("/api/produtos/<int:produto_id>", methods=["DELETE"])
def api_deletar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    nome_produto = produto.nome
    
    # Deleta movimentações associadas (cascade)
    Movimentacao.query.filter_by(produto_id=produto_id).delete()
    
    # Deleta produto
    db.session.delete(produto)
    db.session.commit()
    
    return jsonify({"status": "sucesso", "mensagem": f"Produto '{nome_produto}' excluído com sucesso"}), 200

@app.route("/produtos/<int:produto_id>/movimentacoes")
@login_required
@permission_required('produtos')
def historico_movimentacoes(produto_id):
    user_id = get_usuario_filter()
    
    # Verificar se o produto pertence ao usuário
    if user_id:
        produto = Produto.query.filter_by(id=produto_id, usuario_crm_id=user_id).first_or_404()
    else:
        produto = Produto.query.get_or_404(produto_id)
    
    movimentacoes = Movimentacao.query.filter_by(produto_id=produto.id).order_by(Movimentacao.data.desc()).all()
    return render_template("movimentacoes.html", produto=produto, movimentacoes=movimentacoes)

@app.route("/planner")
@login_required
@permission_required('planner')
def planner():
    # Semana desejada
    week_offset = int(request.args.get("week", 0))
    today = datetime.now().date() + timedelta(weeks=week_offset)

    # Segunda da semana
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    # Horários
    horarios = []
    hora_atual = datetime.strptime("08:00", "%H:%M")
    hora_limite = datetime.strptime("20:00", "%H:%M")

    while hora_atual <= hora_limite:
        horarios.append(hora_atual.time())
        hora_atual += timedelta(minutes=30)

    # Eventos da semana filtrados por usuário
    user_id = get_usuario_filter()
    
    if user_id:
        eventos = PlannerEvento.query.filter(
            PlannerEvento.data >= monday,
            PlannerEvento.data <= monday + timedelta(days=6),
            PlannerEvento.usuario_crm_id == user_id
        ).all()
    else:
        eventos = PlannerEvento.query.filter(
            PlannerEvento.data >= monday,
            PlannerEvento.data <= monday + timedelta(days=6)
        ).all()

    return render_template(
        "planner.html",
        dias=days,
        horarios=horarios,
        eventos=eventos,
        semana_offset=week_offset
    )

@app.route("/planner/salvar", methods=["POST"])
def salvar_evento():
    tipo = request.form["tipo"]
    cliente = request.form.get("cliente")
    data_str = request.form["data"]
    hora_str = request.form["hora"]
    descricao = request.form.get("descricao")

    # Junta a data + hora corretamente
    data_hora = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")

    novo = PlannerEvento(
        tipo=tipo,
        cliente=cliente,
        data=datetime.strptime(data_str, "%Y-%m-%d").date(),
        hora=datetime.strptime(hora_str, "%H:%M").time(),
        data_hora=data_hora,   # <- AQUI ESTÁ O QUE FALTAVA
        descricao=descricao
    )

    db.session.add(novo)
    db.session.commit()

    return redirect(url_for("planner"))

@app.route("/planner/excluir/<int:id>", methods=["POST"])
def excluir_evento(id):
    evento = PlannerEvento.query.get(id)

    if not evento:
        return "Evento não encontrado", 404

    db.session.delete(evento)
    db.session.commit()

    return redirect(url_for("planner"))

@app.route("/tickets")
def list_tickets():
    tickets = Ticket.query.filter_by(status="open").all()
    return jsonify([
        {
            "id": t.id,
            "contact": t.contact_phone,
            "lastMessage": t.messages[-1].body if t.messages else "",
            "unread": count_unread(t.id)
        }
        for t in tickets
    ])

@app.route("/tickets/<int:ticket_id>/messages")
def ticket_messages(ticket_id):
    msgs = Message.query.filter_by(ticket_id=ticket_id).all()
    return jsonify([
        {
            "direction": m.direction,
            "body": m.body,
            "time": m.created_at.strftime("%H:%M")
        }
        for m in msgs
    ])


# quando criar cliente, emitir novo_contato para atualizar lista (opcional)
def emitir_novo_contato(cliente):
    socketio.emit('novo_contato', {
        'id': cliente.id,
        'nome': cliente.nome,
        'telefone': cliente.telefone
    }, broadcast=True)

requests.post(
  "https://proaristocracy-breathtakingly-indira.ngrok-free.dev/webhook/messages",
  json={"phone":"+5547999471874","text":{"message":"Teste via ngrok"}}
)

if __name__ == "__main__":
    # Inicializa o banco de dados
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Banco de dados inicializado com sucesso")
            logger.info("✅ RLS (Row Level Security) ativo")
            logger.info("✅ Isolamento multi-tenant configurado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco: {e}")
    
    print("=" * 60)
    print("✅ CRM Multi-Tenant com RLS Ativo")
    print("✅ Servidor rodando em: http://127.0.0.1:5000")
    print("=" * 60)
    
    # Use socketio.run para suportar corretamente socket.io
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)



