from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, g
from flask_socketio import SocketIO, join_room
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from functools import wraps
import requests
import logging
import json
import csv
import io
import os
import secrets
from dotenv import load_dotenv
from flask_migrate import Migrate
from database_rls import db, tenant_db, init_db
from models import Cliente, MesaNegocio, Ocorrencia, WhatsAppMensagem, ChatbotRegra, Produto, Movimentacao, PlannerEvento, UsuarioCRM, ConfiguracaoUsuario, Parametrizacao, Tarefa, Fornecedor, FacebookPage, Conversation, Message, ConversaConfig
from sqlalchemy import or_, and_

# Carrega variáveis do arquivo .env (se existir)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
_secret_key = os.getenv('SECRET_KEY')
if not _secret_key:
    raise RuntimeError('SECRET_KEY não definida no .env — defina antes de iniciar.')
app.secret_key = _secret_key

# ------------------- BANCO COM RLS -------------------
_database_url = os.getenv('DATABASE_URL')
if not _database_url:
    raise RuntimeError('DATABASE_URL não definida no .env — defina antes de iniciar.')
app.config['SQLALCHEMY_DATABASE_URI'] = _database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False  # True para debug SQL

# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME', ''))

# Inicializa DB com suporte a RLS
db.init_app(app)
tenant_db.init_app(app)

# ------------------- FLASK-MAIL -------------------
mail = Mail(app)

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
    """Retorna o ID do usuário para filtrar dados.

    Todos os tipos de usuário (incluindo super_admin) enxergam apenas os
    próprios registros. Isso garante o isolamento correto entre tenants.

    Para acesso administrativo irrestrito (visão geral de todos os usuários),
    use a rota /admin/painel que faz queries explícitas sem filtro.
    """
    return current_user.get_usuario_principal_id()

def get_usuario_filter_admin_global():
    """Retorna None se o usuário for super_admin (acesso irrestrito).
    Usado apenas em rotas administrativas explícitas.
    """
    if current_user.tipo_usuario == 'super_admin':
        return None
    return current_user.get_usuario_principal_id()

socketio = SocketIO(app, cors_allowed_origins="*")

migrate = Migrate(app, db)

# ------------------- INTEGRAÇÃO META (FACEBOOK / INSTAGRAM) -------------------
from routes.meta_auth import meta_auth_bp
from routes.meta_webhook import meta_webhook_bp
from routes.conversations import conversations_bp
from routes.messages import messages_bp

app.register_blueprint(meta_auth_bp)
app.register_blueprint(meta_webhook_bp)
app.register_blueprint(conversations_bp)
app.register_blueprint(messages_bp)

# ------------------- Z-API -------------------
instance = os.getenv('ZAPI_INSTANCE', '')
token = os.getenv('ZAPI_TOKEN', '')
client_token = os.getenv('ZAPI_CLIENT_TOKEN', '')
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
                    'titulo': f"{evento.tipo} - {evento.cliente or 'Sem cliente'}",
                    'descricao': evento.descricao,
                    'hora': evento.data_hora.strftime('%H:%M'),
                    'cliente': evento.cliente or 'N/A'
                })

            time.sleep(60)  # roda a cada 60 segundos

threading.Thread(target=verificar_eventos_proximos, daemon=True).start()

def verificar_tarefas_proximas():
    with app.app_context():
        while True:
            agora = datetime.now()

            tarefas = Tarefa.query.filter(
                Tarefa.lembrete_em.isnot(None),
                Tarefa.lembrete_em <= agora,
                Tarefa.lembrete_enviado.is_(False),
                Tarefa.status != "Concluída"
            ).all()

            for tarefa in tarefas:
                cliente_nome = tarefa.cliente.nome if tarefa.cliente else "—"
                payload = {
                    "id": tarefa.id,
                    "titulo": tarefa.titulo,
                    "descricao": tarefa.descricao or "",
                    "cliente": cliente_nome,
                    "hora": tarefa.lembrete_em.strftime('%H:%M') if tarefa.lembrete_em else "",
                    "prioridade": tarefa.prioridade,
                    "usuario_crm_id": tarefa.usuario_crm_id
                }
                socketio.emit('notificacao_tarefa', payload, broadcast=True)
                tarefa.lembrete_enviado = True

            if tarefas:
                db.session.commit()

            time.sleep(60)

threading.Thread(target=verificar_tarefas_proximas, daemon=True).start()


# ------------------- JOB: RENOVAÇÃO AUTOMÁTICA DE TOKENS META (30 dias) ---
def _renovar_tokens_meta_job():
    """Roda a cada 30 dias e renova os page_access_tokens de todas as páginas."""
    time.sleep(120)  # aguarda 2 min para o app inicializar completamente
    while True:
        with app.app_context():
            try:
                app_id = os.getenv('META_APP_ID')
                app_secret = os.getenv('META_APP_SECRET')
                if app_id and app_secret:
                    from services.message_service import renovar_tokens_expirados
                    n = renovar_tokens_expirados(app_id, app_secret)
                    logger.info(f'Renovação de tokens Meta concluída: {n} token(s) renovado(s).')
                else:
                    logger.debug('META_APP_ID/SECRET não configurados — job de renovação ignorado.')
            except Exception as _exc:
                logger.error(f'Erro no job de renovação de tokens Meta: {_exc}')
        time.sleep(30 * 24 * 3600)  # aguarda 30 dias

threading.Thread(target=_renovar_tokens_meta_job, daemon=True).start()


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

# ------------------- RECUPERAÇÃO DE SENHA -------------------
def verificar_configuracao_email():
    """Verifica se o email está configurado corretamente"""
    username = app.config.get('MAIL_USERNAME', '')
    password = app.config.get('MAIL_PASSWORD', '')

    if not username or not password:
        return False, "Configurações de email não foram definidas. Configure MAIL_USERNAME e MAIL_PASSWORD no .env"

    return True, None

def enviar_email_recuperacao(usuario, token):
    """Envia email com link de recuperação de senha"""
    try:
        # Verifica configuração antes de tentar enviar
        config_ok, erro_msg = verificar_configuracao_email()
        if not config_ok:
            logger.error(f"Configuração de email inválida: {erro_msg}")
            return False, erro_msg
        
        # Gera o link de recuperação
        link_recuperacao = url_for('resetar_senha', token=token, _external=True)
        
        logger.info(f"Tentando enviar email de recuperação para: {usuario.email}")
        
        # Cria a mensagem
        msg = Message(
            subject='Recuperação de Senha - CRM',
            recipients=[usuario.email]
        )
        
        # Corpo do email em HTML
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4a90e2;">Recuperação de Senha</h2>
                    <p>Olá, <strong>{usuario.nome}</strong>!</p>
                    <p>Recebemos uma solicitação de recuperação de senha para sua conta.</p>
                    <p>Clique no botão abaixo para redefinir sua senha:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{link_recuperacao}" 
                           style="background-color: #4a90e2; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Redefinir Senha
                        </a>
                    </div>
                    <p>Ou copie e cole o link abaixo no seu navegador:</p>
                    <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">
                        {link_recuperacao}
                    </p>
                    <p><strong>Este link expirará em 1 hora.</strong></p>
                    <p>Se você não solicitou a recuperação de senha, ignore este email.</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px;">
                        Vitriun CRM - Não responda este email
                    </p>
                </div>
            </body>
        </html>
        """
        
        mail.send(msg)
        logger.info(f"Email de recuperação enviado com sucesso para: {usuario.email}")
        return True, None
    except Exception as e:
        erro_detalhado = str(e)
        logger.error(f"Erro ao enviar email de recuperação: {erro_detalhado}")
        logger.error(f"Tipo do erro: {type(e).__name__}")
        
        # Mensagem mais específica baseada no tipo de erro
        if 'Authentication' in erro_detalhado or 'Username and Password' in erro_detalhado:
            return False, "Credenciais de email inválidas. Verifique MAIL_USERNAME e MAIL_PASSWORD."
        elif 'getaddrinfo' in erro_detalhado or 'Name or service not known' in erro_detalhado:
            return False, "Não foi possível conectar ao servidor de email. Verifique MAIL_SERVER."
        elif 'Connection refused' in erro_detalhado:
            return False, "Conexão recusada. Verifique MAIL_PORT e configurações de firewall."
        else:
            return False, f"Erro ao enviar email: {erro_detalhado[:100]}"

@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    """Página para solicitar recuperação de senha"""
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Por favor, informe seu email.', 'warning')
            return redirect(url_for('esqueci_senha'))
        
        usuario = UsuarioCRM.query.filter_by(email=email).first()
        
        # Sempre retorna a mesma mensagem para não revelar se o email existe
        if usuario:
            # Gera token único
            token = secrets.token_urlsafe(32)
            
            # Define token e expiração (1 hora)
            usuario.reset_token = token
            usuario.reset_token_expira = datetime.utcnow() + timedelta(hours=1)
            
            try:
                db.session.commit()
                
                # Envia email
                sucesso, erro_msg = enviar_email_recuperacao(usuario, token)
                if sucesso:
                    flash('Se o email informado estiver cadastrado, você receberá instruções para recuperar sua senha.', 'info')
                else:
                    # Se for erro de configuração, mostra mensagem específica
                    if 'não foram definidas' in erro_msg or 'Credenciais' in erro_msg or 'conectar' in erro_msg:
                        flash(f'⚠️ Sistema de email não configurado. Contate o administrador.', 'warning')
                        logger.error(f"ATENÇÃO: Configure o email no arquivo CRM.py! Detalhes: {erro_msg}")
                    else:
                        flash('Erro ao enviar email. Tente novamente mais tarde.', 'danger')
                        logger.error(f"Erro no envio: {erro_msg}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erro ao salvar token de recuperação: {e}")
                flash('Erro ao processar solicitação. Tente novamente.', 'danger')
        else:
            # Mesma mensagem para não revelar se o email existe
            flash('Se o email informado estiver cadastrado, você receberá instruções para recuperar sua senha.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('esqueci_senha.html')

@app.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def resetar_senha(token):
    """Página para redefinir senha com token"""
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    
    # Busca usuário com o token
    usuario = UsuarioCRM.query.filter_by(reset_token=token).first()
    
    # Verifica se o token é válido e não expirou
    if not usuario or not usuario.reset_token_expira or usuario.reset_token_expira < datetime.utcnow():
        flash('Link de recuperação inválido ou expirado. Solicite um novo link.', 'danger')
        return redirect(url_for('esqueci_senha'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('senha', '')
        confirma_senha = request.form.get('confirma_senha', '')
        
        # Validações
        if not nova_senha or not confirma_senha:
            flash('Por favor, preencha todos os campos.', 'warning')
            return redirect(url_for('resetar_senha', token=token))
        
        if len(nova_senha) < 6:
            flash('A senha deve ter no mínimo 6 caracteres.', 'warning')
            return redirect(url_for('resetar_senha', token=token))
        
        if nova_senha != confirma_senha:
            flash('As senhas não coincidem.', 'warning')
            return redirect(url_for('resetar_senha', token=token))
        
        # Atualiza a senha
        usuario.set_password(nova_senha)
        usuario.reset_token = None
        usuario.reset_token_expira = None
        
        try:
            db.session.commit()
            flash('Senha redefinida com sucesso! Você já pode fazer login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao redefinir senha: {e}")
            flash('Erro ao redefinir senha. Tente novamente.', 'danger')
    
    return render_template('resetar_senha.html', token=token)



# ------------------- CONFIGURAÇÕES DO USUÁRIO -------------------
@app.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    """Página de configurações pessoais do usuário"""
    # Buscar ou criar configuração do usuário
    config = ConfiguracaoUsuario.query.filter_by(usuario_crm_id=current_user.id).first()
    if not config:
        config = ConfiguracaoUsuario(usuario_crm_id=current_user.id)
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'alterar_senha':
            senha_atual = request.form.get('senha_atual')
            nova_senha = request.form.get('nova_senha')
            confirmar_senha = request.form.get('confirmar_senha')
            
            # Verificar senha atual
            if not current_user.check_password(senha_atual):
                flash('Senha atual incorreta!', 'danger')
                return redirect(url_for('configuracoes'))
            
            # Verificar se as senhas novas coincidem
            if nova_senha != confirmar_senha:
                flash('As senhas não coincidem!', 'danger')
                return redirect(url_for('configuracoes'))
            
            # Verificar comprimento mínimo
            if len(nova_senha) < 6:
                flash('A senha deve ter no mínimo 6 caracteres!', 'danger')
                return redirect(url_for('configuracoes'))
            
            # Alterar senha
            current_user.set_password(nova_senha)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('configuracoes'))
    
    return render_template('configuracoes_conta.html', config=config)


@app.route('/parametrizacoes', methods=['GET', 'POST'])
@login_required
def parametrizacoes():
    """Página de parametrizações do sistema (apenas para admin e super_admin)"""
    if current_user.tipo_usuario not in ['super_admin', 'admin']:
        flash('Acesso negado. Apenas administradores podem acessar parametrizações.', 'danger')
        return redirect(url_for('menu'))
    
    # Buscar ou criar parametrização do usuário
    param = Parametrizacao.query.filter_by(usuario_crm_id=current_user.id).first()
    if not param:
        param = Parametrizacao(usuario_crm_id=current_user.id)
        db.session.add(param)
        db.session.commit()
    
    if request.method == 'POST':
        def normalizar_campo(campo):
            valor = request.form.get(campo, '')
            valor = valor.strip()
            return valor if valor else None

        # Atualizar mensagens automáticas
        param.mensagem_boas_vindas = request.form.get('mensagem_boas_vindas', '')
        param.mensagem_ausencia = request.form.get('mensagem_ausencia', '')
        param.mensagem_encerramento = request.form.get('mensagem_encerramento', '')
        param.mensagem_nps = request.form.get('mensagem_nps', '')
        
        # Atualizar configurações
        param.resposta_automatica_ativa = 'resposta_automatica_ativa' in request.form
        
        # Horários de atendimento
        horario_inicio = request.form.get('horario_atendimento_inicio')
        horario_fim = request.form.get('horario_atendimento_fim')
        
        if horario_inicio:
            param.horario_atendimento_inicio = datetime.strptime(horario_inicio, '%H:%M').time()
        if horario_fim:
            param.horario_atendimento_fim = datetime.strptime(horario_fim, '%H:%M').time()

        # Dados de integração da Meta Graph API (salvos por cliente)
        param.meta_graph_app_id = normalizar_campo('meta_graph_app_id')
        param.meta_graph_phone_number_id = normalizar_campo('meta_graph_phone_number_id')

        if 'limpar_tokens_meta' in request.form:
            param.meta_graph_access_token = None
            param.meta_graph_verify_token = None
        else:
            novo_access_token = normalizar_campo('meta_graph_access_token')
            novo_verify_token = normalizar_campo('meta_graph_verify_token')

            # Campo vazio nao sobrescreve token existente para evitar apagar acidentalmente.
            if novo_access_token is not None:
                param.meta_graph_access_token = novo_access_token
            if novo_verify_token is not None:
                param.meta_graph_verify_token = novo_verify_token
        
        db.session.commit()
        flash('Parametrizações salvas com sucesso!', 'success')
        return redirect(url_for('parametrizacoes'))
    
    # Busca páginas do Facebook/Instagram conectadas por este usuário
    paginas_meta = FacebookPage.query.filter_by(
        usuario_crm_id=current_user.id
    ).order_by(FacebookPage.page_name).all()

    return render_template('parametrizacoes.html', param=param, paginas_meta=paginas_meta)


@app.route('/inbox')
@login_required
def inbox():
    """Inbox de mensagens Facebook/Instagram."""
    if not current_user.tem_permissao('whatsapp'):
        flash('Você não tem acesso ao Inbox.', 'danger')
        return redirect(url_for('menu'))
    return render_template('inbox.html')



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
        modulos = ['clientes', 'mesas', 'ocorrencias', 'produtos', 'whatsapp', 'chatbot', 'planner', 'tarefas', 'nps']
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
        {'id': 'tarefas', 'nome': 'Tarefas', 'icone': '✅'},
        {'id': 'nps', 'nome': 'NPS', 'icone': '⭐'}
        # {'id': 'relatorios', 'nome': 'Relatórios', 'icone': '📊'}  # DESATIVADO
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
        modulos = ['clientes', 'mesas', 'ocorrencias', 'produtos', 'whatsapp', 'chatbot', 'planner', 'tarefas', 'nps']
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
        {'id': 'tarefas', 'nome': 'Tarefas', 'icone': '✅'},
        {'id': 'nps', 'nome': 'NPS', 'icone': '⭐'}
        # {'id': 'relatorios', 'nome': 'Relatórios', 'icone': '📊'}  # DESATIVADO
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
    
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash(f'Usuário {nome} deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar usuário: {str(e)}', 'danger')
    
    return redirect(url_for('listar_usuarios'))


# ------------------- GESTÃO DE COLABORADORES (SUPER_ADMIN E ADMIN) -------------------
@app.route('/colaboradores')
@login_required
def listar_colaboradores():
    """Lista todos os colaboradores - SUPER_ADMIN vê todos, ADMIN vê apenas os seus"""
    if current_user.tipo_usuario not in ['super_admin', 'admin']:
        flash('Acesso negado. Apenas administradores podem gerenciar colaboradores.', 'danger')
        return redirect(url_for('menu'))
    
    # Verificar se há filtro por cliente (apenas para super_admin)
    cliente_id = request.args.get('cliente_id', type=int)
    
    if current_user.tipo_usuario == 'super_admin':
        # Super admin pode ver todos os colaboradores ou filtrar por cliente
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
    else:
        # Admin vê apenas seus próprios colaboradores
        colaboradores = UsuarioCRM.query.filter_by(
            tipo_usuario='colaborador',
            usuario_pai_id=current_user.id
        ).order_by(UsuarioCRM.nome).all()
        cliente_nome = None
    
    return render_template('listar_colaboradores.html', colaboradores=colaboradores, cliente_filtro=cliente_nome)

@app.route('/colaboradores/add', methods=['GET', 'POST'])
@login_required
def add_colaborador():
    """Adiciona novo colaborador - SUPER_ADMIN pode escolher o admin, ADMIN cria vinculado a si mesmo"""
    if current_user.tipo_usuario not in ['super_admin', 'admin']:
        flash('Acesso negado. Apenas administradores podem gerenciar colaboradores.', 'danger')
        return redirect(url_for('menu'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Permissões
        modulos = ['clientes', 'mesas', 'ocorrencias', 'produtos', 'whatsapp', 'chatbot', 'planner', 'tarefas', 'nps']
        permissoes = {modulo: modulo in request.form.getlist('permissoes') for modulo in modulos}
        
        # Verificar se email já existe
        if UsuarioCRM.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'danger')
            return redirect(url_for('add_colaborador'))
        
        # Determinar o usuario_pai_id
        if current_user.tipo_usuario == 'super_admin':
            # Super admin pode escolher o cliente
            usuario_pai_id = request.form.get('usuario_pai_id')
            if not usuario_pai_id:
                flash('Selecione o cliente para este colaborador.', 'danger')
                return redirect(url_for('add_colaborador'))
            usuario_pai_id = int(usuario_pai_id)
        else:
            # Admin cria colaborador vinculado a si mesmo
            usuario_pai_id = current_user.id
        
        # Criar novo colaborador
        novo_colaborador = UsuarioCRM(
            nome=nome,
            email=email,
            tipo_usuario='colaborador',
            usuario_pai_id=usuario_pai_id,
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
        {'id': 'tarefas', 'nome': 'Tarefas', 'icone': '✅'},
        {'id': 'nps', 'nome': 'NPS', 'icone': '⭐'}
        # {'id': 'relatorios', 'nome': 'Relatórios', 'icone': '📊'}  # DESATIVADO
    ]
    
    # Buscar todos os clientes (admin) para selecionar (apenas para super_admin)
    if current_user.tipo_usuario == 'super_admin':
        clientes = UsuarioCRM.query.filter_by(tipo_usuario='admin', ativo=True).order_by(UsuarioCRM.nome).all()
    else:
        clientes = None
    
    return render_template('add_colaborador.html', modulos=modulos_disponiveis, clientes=clientes)

@app.route('/colaboradores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_colaborador(id):
    """Edita colaborador existente - SUPER_ADMIN edita qualquer um, ADMIN edita apenas os seus"""
    if current_user.tipo_usuario not in ['super_admin', 'admin']:
        flash('Acesso negado. Apenas administradores podem gerenciar colaboradores.', 'danger')
        return redirect(url_for('menu'))
    
    colaborador = UsuarioCRM.query.get_or_404(id)
    
    # Admin só pode editar seus próprios colaboradores
    if current_user.tipo_usuario == 'admin' and colaborador.usuario_pai_id != current_user.id:
        flash('Acesso negado. Você só pode editar seus próprios colaboradores.', 'danger')
        return redirect(url_for('listar_colaboradores'))
    
    if request.method == 'POST':
        colaborador.nome = request.form.get('nome')
        colaborador.email = request.form.get('email')
        colaborador.ativo = 'ativo' in request.form
        
        # Atualizar senha se fornecida
        nova_senha = request.form.get('senha')
        if nova_senha:
            colaborador.set_password(nova_senha)
        
        # Atualizar permissões
        modulos = ['clientes', 'mesas', 'ocorrencias', 'produtos', 'whatsapp', 'chatbot', 'planner', 'tarefas', 'nps']
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
        {'id': 'tarefas', 'nome': 'Tarefas', 'icone': '✅'},
        {'id': 'nps', 'nome': 'NPS', 'icone': '⭐'}
        # {'id': 'relatorios', 'nome': 'Relatórios', 'icone': '📊'}  # DESATIVADO
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
    Respeita quarentena configurada no usuário dono do cliente.
    """
    # --- Quarentena NPS ---
    if cliente.data_ultimo_nps_envio:
        usuario_dono = UsuarioCRM.query.get(cliente.usuario_crm_id)
        dias_quarentena = (usuario_dono.dias_quarentena_nps or 30) if usuario_dono else 30
        proximo_envio = cliente.data_ultimo_nps_envio + timedelta(days=dias_quarentena)
        if datetime.utcnow() < proximo_envio:
            logger.info(
                f"NPS ignorado para {cliente.nome}: em quarentena até "
                f"{proximo_envio.strftime('%d/%m/%Y')}"
            )
            return False

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
        # Marcar que está aguardando resposta de NPS e registrar data de envio
        cliente.aguardando_nps = True
        cliente.data_ultimo_nps_envio = datetime.utcnow()
        db.session.commit()
        
        # Salvar mensagem enviada
        msg = WhatsAppMensagem(
            numero=numero_norm,
            remetente="Você",
            mensagem=mensagem,
            recebido_em=datetime.utcnow(),
            usuario_crm_id=cliente.usuario_crm_id
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
                recebido_em=datetime.utcnow(),
                usuario_crm_id=cliente.usuario_crm_id
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
        produtos_quantidades_json = request.form.get("produtos_quantidades", "{}")
        
        # Parse das quantidades
        try:
            produtos_quantidades = json.loads(produtos_quantidades_json) if produtos_quantidades_json else {}
        except:
            produtos_quantidades = {}
        
        mesa = MesaNegocio(
            usuario_crm_id=current_user.get_usuario_principal_id(),
            cliente_id=id,
            topico=request.form["topico"],
            produtos=request.form["produtos"],
            produtos_quantidades=produtos_quantidades,
            situacao=situacao,
            valor_total=float(request.form["valor_total"]),
            descricao=request.form.get("descricao"),
            data_registro=datetime.today().date(),
            hora_registro=datetime.now().time(),
            data_fechamento=datetime.today().date() if situacao in ["Ganho", "Perdido"] else None
        )
        db.session.add(mesa)
        db.session.flush()  # Para obter o ID da mesa antes do commit
        
        # Se criou a mesa como "Ganho", dar baixa no estoque
        if situacao == "Ganho" and produtos_quantidades:
            try:
                for produto_id_str, quantidade in produtos_quantidades.items():
                    produto_id = int(produto_id_str)
                    quantidade = int(quantidade)
                    
                    # Buscar produto
                    produto = Produto.query.get(produto_id)
                    if produto and quantidade > 0:
                        # Verificar se há estoque suficiente
                        if produto.quantidade < quantidade:
                            db.session.rollback()
                            flash(f'⚠️ Estoque insuficiente para o produto "{produto.nome}". Disponível: {produto.quantidade}, Solicitado: {quantidade}', 'warning')
                            return redirect(url_for('add_mesa', id=id))
                        
                        # Dar baixa no estoque
                        produto.quantidade -= quantidade
                        produto.ultima_movimentacao_data = datetime.utcnow()
                        produto.ultima_movimentacao_descricao = f"Venda - Mesa #{mesa.id}"
                        
                        # Registrar movimentação
                        movimentacao = Movimentacao(
                            produto_id=produto_id,
                            tipo='saida',
                            quantidade=quantidade,
                            descricao=f"Venda fechada - Mesa #{mesa.id} - Cliente: {cliente.nome}"
                        )
                        db.session.add(movimentacao)
                        
                flash(f'✅ Mesa criada e baixa no estoque realizada com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'⚠️ Erro ao dar baixa no estoque: {str(e)}', 'warning')
                logger.error(f"Erro ao dar baixa no estoque: {str(e)}")
                return redirect(url_for('add_mesa', id=id))
        
        db.session.commit()
        
        # Se criou a mesa já como "Ganho", enviar NPS
        if situacao == "Ganho":
            print(f"🔍 Mesa criada como Ganho. Enviando NPS para {cliente.nome}")
            try:
                resultado = enviar_pesquisa_nps(cliente)
                if resultado:
                    flash(f"✅ Pesquisa NPS enviada para {cliente.nome}!", "success")
                else:
                    flash("⚠️ Houve erro ao enviar pesquisa NPS.", "warning")
            except Exception as e:
                flash(f"⚠️ Erro ao enviar NPS: {str(e)}", "warning")
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
        telefone_bruto = request.form["telefone"]
        telefone = normalize_phone(telefone_bruto)
        email = request.form["email"]
        tipo_pessoa = request.form["tipo_pessoa"]

        if not telefone:
            flash("Número de telefone inválido. Informe com DDD.", "danger")
            return redirect(url_for("cadastro"))

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


@app.route("/clientes/modelo-importacao")
@login_required
def modelo_importacao_clientes():
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from flask import send_file

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Clientes"

    headers = [
        "Nome", "Telefone", "Email", "Tipo de Pessoa",
        "Data de Nascimento", "Data de Abertura", "Renda", "Faturamento",
        "Segmento de Trabalho", "Segmento", "Qtd. Funcionários", "Endereço", "Observações"
    ]
    obrigatorios = {"Nome", "Telefone", "Email", "Tipo de Pessoa"}

    fill_obrig = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
    fill_opc   = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    font_branca = Font(color="FFFFFF", bold=True)
    font_escura = Font(color="333333", bold=True)

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        if header in obrigatorios:
            cell.fill = fill_obrig
            cell.font = font_branca
        else:
            cell.fill = fill_opc
            cell.font = font_escura
        cell.alignment = Alignment(horizontal="center")

    # Linha de exemplo
    ws.append([
        "Maria Silva", "+5547999999999", "maria@email.com", "Física",
        "1990-01-15", "", "", "", "Tecnologia", "TI", "10", "Rua das Flores, 123", ""
    ])

    # Ajuste automático de largura
    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = max_len + 4

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="modelo_importacao_clientes.xlsx"
    )


@app.route("/clientes/importar", methods=["GET", "POST"])
@login_required
@permission_required('clientes')
def importar_clientes():
    user_id = current_user.get_usuario_principal_id()
    erros = []

    if request.method == "POST":
        arquivo = request.files.get("arquivo")
        modo = request.form.get("modo", "pular")  # pular ou atualizar

        if not arquivo or not arquivo.filename:
            flash("Selecione um arquivo CSV ou Excel (.xlsx) para importar.", "warning")
            return redirect(url_for("importar_clientes"))

        conteudo = arquivo.read()
        filename_lower = arquivo.filename.lower()

        def normalizar_header(h):
            import re
            import unicodedata
            h = (h or "").strip().lower()
            h = unicodedata.normalize('NFKD', h).encode('ascii', 'ignore').decode('ascii')
            h = re.sub(r"\s+", "_", h)
            h = re.sub(r"[^a-z0-9_]+", "", h)
            return h

        # Leitura do arquivo (CSV ou XLSX)
        rows_para_importar = []
        if filename_lower.endswith('.xlsx'):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
            ws = wb.active
            linhas = list(ws.iter_rows(values_only=True))
            wb.close()
            if not linhas:
                flash("Arquivo Excel vazio.", "danger")
                return redirect(url_for("importar_clientes"))
            cabecalhos = [str(h) if h is not None else "" for h in linhas[0]]
            for linha in linhas[1:]:
                if any(v is not None and str(v).strip() for v in linha):
                    rows_para_importar.append(
                        dict(zip(cabecalhos, [str(v) if v is not None else "" for v in linha]))
                    )
        else:
            try:
                texto = conteudo.decode("utf-8-sig")
            except Exception:
                texto = conteudo.decode("latin-1", errors="ignore")
            amostra = texto[:2048]
            delimitador = ";" if amostra.count(";") > amostra.count(",") else ","
            reader = csv.DictReader(io.StringIO(texto), delimiter=delimitador)
            if not reader.fieldnames:
                flash("Arquivo CSV sem cabeçalho.", "danger")
                return redirect(url_for("importar_clientes"))
            rows_para_importar = list(reader)

        # Mapeamento de colunas aceitas (snake_case e nomes legíveis normalizados)
        mapa = {
            "nome": "nome",
            "email": "email",
            "telefone": "telefone",
            "celular": "telefone",
            "tipo_pessoa": "tipo_pessoa",
            "tipopessoa": "tipo_pessoa",
            "tipo_de_pessoa": "tipo_pessoa",
            "data_nascimento": "data_nascimento",
            "datanascimento": "data_nascimento",
            "data_de_nascimento": "data_nascimento",
            "data_abertura": "data_abertura",
            "dataabertura": "data_abertura",
            "data_de_abertura": "data_abertura",
            "renda": "renda",
            "faturamento": "faturamento",
            "segmento_trabalho": "segmento_trabalho",
            "segmentotrabalho": "segmento_trabalho",
            "segmento_de_trabalho": "segmento_trabalho",
            "segmento": "segmento",
            "qtd_funcionarios": "qtd_funcionarios",
            "qtdfuncionarios": "qtd_funcionarios",
            "qtd_funcionarios": "qtd_funcionarios",
            "endereco": "endereco",
            "observacoes": "observacoes"
        }

        # Carregar clientes existentes para deduplicação
        clientes_existentes = Cliente.query.filter_by(usuario_crm_id=user_id).all()
        mapa_email = { (c.email or "").strip().lower(): c for c in clientes_existentes if c.email }
        mapa_telefone = { normalize_phone(c.telefone): c for c in clientes_existentes if c.telefone }

        inseridos = 0
        atualizados = 0
        duplicados = 0
        ignorados = 0

        for idx, row in enumerate(rows_para_importar, start=2):
            dados = {}
            for chave, valor in row.items():
                destino = mapa.get(normalizar_header(chave))
                if destino:
                    dados[destino] = (valor or "").strip()

            nome = dados.get("nome")
            telefone_bruto = dados.get("telefone")
            telefone = normalize_phone(telefone_bruto)
            email = (dados.get("email") or "").strip().lower()

            tipo_pessoa_val = dados.get("tipo_pessoa")
            campos_faltando = []
            if not nome: campos_faltando.append("Nome")
            if not telefone: campos_faltando.append("Telefone")
            if not email: campos_faltando.append("Email")
            if not tipo_pessoa_val: campos_faltando.append("Tipo de Pessoa")
            if campos_faltando:
                ignorados += 1
                erros.append(f"Linha {idx}: campo(s) obrigatório(s) ausente(s): {', '.join(campos_faltando)}")
                continue

            cliente_existente = None
            if email and email in mapa_email:
                cliente_existente = mapa_email[email]
            elif telefone and telefone in mapa_telefone:
                cliente_existente = mapa_telefone[telefone]

            def aplicar_dados(cliente):
                cliente.nome = nome
                cliente.telefone = telefone_bruto or cliente.telefone
                if email:
                    cliente.email = email
                if dados.get("tipo_pessoa"):
                    cliente.tipo_pessoa = dados.get("tipo_pessoa")

                if dados.get("data_nascimento"):
                    try:
                        cliente.data_nascimento = datetime.strptime(dados.get("data_nascimento"), "%Y-%m-%d").date()
                    except Exception:
                        pass
                if dados.get("data_abertura"):
                    try:
                        cliente.data_abertura = datetime.strptime(dados.get("data_abertura"), "%Y-%m-%d").date()
                    except Exception:
                        pass

                if dados.get("renda"):
                    try:
                        cliente.renda = float(dados.get("renda"))
                    except Exception:
                        pass
                if dados.get("faturamento"):
                    try:
                        cliente.faturamento = float(dados.get("faturamento"))
                    except Exception:
                        pass

                cliente.segmento_trabalho = dados.get("segmento_trabalho") or cliente.segmento_trabalho
                cliente.segmento = dados.get("segmento") or cliente.segmento
                cliente.endereco = dados.get("endereco") or cliente.endereco
                if dados.get("qtd_funcionarios"):
                    try:
                        cliente.qtd_funcionarios = int(dados.get("qtd_funcionarios"))
                    except Exception:
                        pass
                if dados.get("observacoes"):
                    if cliente.observacoes:
                        cliente.observacoes = f"{cliente.observacoes}\n{dados.get('observacoes')}"
                    else:
                        cliente.observacoes = dados.get("observacoes")

            if cliente_existente:
                if modo == "atualizar":
                    aplicar_dados(cliente_existente)
                    atualizados += 1
                else:
                    duplicados += 1
                continue

            novo = Cliente(
                usuario_crm_id=user_id,
                nome=nome,
                telefone=telefone_bruto,
                email=email or None,
                tipo_pessoa=dados.get("tipo_pessoa") or "Cliente"
            )
            aplicar_dados(novo)
            db.session.add(novo)
            inseridos += 1

            if email:
                mapa_email[email] = novo
            if telefone:
                mapa_telefone[telefone] = novo

        db.session.commit()

        flash(
            f"Importação concluída. Inseridos: {inseridos}, Atualizados: {atualizados}, "
            f"Duplicados: {duplicados}, Ignorados: {ignorados}.",
            "success"
        )

    return render_template("importar_clientes.html", erros=erros)


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
    if nova_situacao in ["Ganho", "Perdido"]:
        mesa.data_fechamento = datetime.today().date()
    elif nova_situacao == "Em negociação":
        mesa.data_fechamento = None
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

@app.route("/webhook/test", methods=["POST", "GET"])
def webhook_test():
    """Endpoint de teste para debug do webhook"""
    if request.method == "GET":
        return jsonify({"status": "Webhook test endpoint ativo", "timestamp": datetime.now().isoformat()})
    
    data = request.get_json(silent=True) or {}
    print("🧪 WEBHOOK TEST - Payload recebido:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    return jsonify({
        "status": "received",
        "payload": data,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/canais/webhook", methods=["POST", "OPTIONS"])
@app.route("/webhook/messages", methods=["POST", "OPTIONS"])
def receber_mensagem_webhook():
    # Suporte CORS para OPTIONS (preflight)
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200
    
    data = request.get_json(silent=True) or {}
    
    print("\n" + "="*60)
    print("📩 WEBHOOK RECEBIDO")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Payload completo:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("="*60 + "\n")

    # ========== ETAPA 1: EXTRAIR TELEFONE ==========
    phone = None
    # Busca direta por chaves comuns
    for k in ("phone", "from", "from_number", "sender", "contact", "wa_id", "number", "chatId", "author"):
        v = data.get(k)
        if v and isinstance(v, str):
            phone = v
            print(f"✅ Telefone encontrado (chave: {k}): {phone}")
            break

    # Busca recursiva se não encontrou
    if not phone:
        def find_phone(obj, path=""):
            if isinstance(obj, dict):
                for kk, vv in obj.items():
                    current_path = f"{path}.{kk}" if path else kk
                    if kk.lower() in ("phone", "from", "number", "wa_id", "chatid", "author") and isinstance(vv, str) and len(str(vv).replace("+", "").replace(" ", "")) >= 10:
                        return vv, current_path
                    res = find_phone(vv, current_path)
                    if res[0]:
                        return res
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    res = find_phone(item, f"{path}[{idx}]")
                    if res[0]:
                        return res
            return None, None

        phone, found_path = find_phone(data)
        if phone:
            print(f"✅ Telefone encontrado recursivamente ({found_path}): {phone}")

    # ========== ETAPA 2: EXTRAIR TEXTO ==========
    text = None
    
    # Busca em campos diretos comuns do Z-API
    txt = data.get("text")
    if isinstance(txt, dict):
        text = txt.get("message") or txt.get("body") or txt.get("text")
    elif isinstance(txt, str):
        text = txt
    
    if not text:
        text = data.get("message") or data.get("body") or data.get("text_message") or data.get("content")
    
    if text:
        print(f"✅ Texto encontrado (direto): {text[:50]}...")
    
    # Busca recursiva se não encontrou
    if not text:
        def find_text(obj, path=""):
            if isinstance(obj, dict):
                for kk, vv in obj.items():
                    current_path = f"{path}.{kk}" if path else kk
                    if kk.lower() in ("message", "body", "text", "caption", "content") and isinstance(vv, str) and len(vv) > 0:
                        # Evita pegar IDs ou valores técnicos
                        if "id" not in kk.lower() and "token" not in kk.lower() and "key" not in kk.lower():
                            return vv, current_path
                    res = find_text(vv, current_path)
                    if res[0]:
                        return res
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    res = find_text(item, f"{path}[{idx}]")
                    if res[0]:
                        return res
            return None, None

        text, found_path = find_text(data)
        if text:
            print(f"✅ Texto encontrado recursivamente ({found_path}): {text[:50]}...")

    # ========== ETAPA 3: VALIDAÇÕES ==========
    
    # Ignorar callbacks de status/presença APENAS se for explicitamente apenas isso
    tipo = data.get("type", "").lower()
    event = data.get("event", "").lower()
    
    # Lista de tipos que devemos ignorar APENAS se não tiverem mensagem
    status_only_types = ("presence", "ack", "messagestatuscallback", "deliverycallback")
    
    is_status_only = any(t in tipo or t in event for t in status_only_types) and not text
    
    if is_status_only:
        print(f"ℹ️ Webhook ignorado: callback de status/presença (tipo: {tipo or event})")
        return {"status": "ignored", "reason": "status_callback"}, 200

    # Validar telefone e texto
    if not phone:
        print(f"⚠️ Webhook ignorado: telefone não encontrado")
        return {"status": "ignored", "reason": "no_phone"}, 200
    
    if not text:
        print(f"⚠️ Webhook ignorado: texto não encontrado")
        return {"status": "ignored", "reason": "no_text"}, 200

    # Evita salvar valores técnicos capturados como 'text'
    if isinstance(text, str) and (text == data.get("instanceId") or len(text) > 5000):
        print(f"⚠️ Webhook ignorado: texto inválido ou muito longo")
        return {"status": "ignored", "reason": "invalid_text"}, 200

    # ========== ETAPA 4: NORMALIZAR E SALVAR ==========
    numero = normalize_phone(phone)
    print(f"📞 Número normalizado: {numero}")

    # Descobrir a qual usuário CRM essa mensagem pertence
    usuario_crm_id = None
    cliente_temp = find_cliente_by_phone(numero)
    if cliente_temp and cliente_temp.usuario_crm_id:
        usuario_crm_id = cliente_temp.usuario_crm_id
        print(f"✅ Mensagem associada ao usuário CRM ID: {usuario_crm_id}")
    else:
        print(f"⚠️ Cliente não encontrado ou sem usuário associado - mensagem será visível para todos")

    # Salvar no banco
    msg = WhatsAppMensagem(
        numero=numero,
        remetente="Cliente",
        mensagem=text,
        recebido_em=datetime.utcnow(),
        usuario_crm_id=usuario_crm_id
    )
    db.session.add(msg)
    db.session.commit()
    print(f"💾 Mensagem salva no banco (ID: {msg.id})")

    # ========== ETAPA 5: VERIFICAR NPS ==========
    cliente = find_cliente_by_phone(numero)
    
    if cliente:
        print(f"✅ Cliente encontrado: {cliente.nome} (Tel: {cliente.telefone})")
        
        if hasattr(cliente, 'aguardando_nps') and cliente.aguardando_nps:
            print(f"📊 Cliente aguardando NPS - processando resposta...")
            try:
                resultado = processar_resposta_nps(cliente, text)
                if resultado:
                    print(f"✅ Resposta NPS processada com sucesso!")
                else:
                    print(f"⚠️ Texto não era uma resposta válida de NPS")
            except Exception as e:
                print(f"❌ Erro ao processar NPS: {e}")
    else:
        print(f"ℹ️ Cliente não encontrado para o número {numero}")

    # ========== ETAPA 5.5: RESPOSTA AUTOMÁTICA PARAMETRIZADA ==========
    if usuario_crm_id:
        try:
            param_auto = Parametrizacao.query.filter_by(usuario_crm_id=usuario_crm_id).first()
            if param_auto and param_auto.resposta_automatica_ativa:
                usuario_dono = UsuarioCRM.query.get(usuario_crm_id)
                agora_time = datetime.now().time()

                # Verificar se está fora do horário de atendimento
                horario_configurado = bool(param_auto.horario_atendimento_inicio and param_auto.horario_atendimento_fim)
                fora_do_horario = False
                if horario_configurado:
                    h_inicio = param_auto.horario_atendimento_inicio
                    h_fim = param_auto.horario_atendimento_fim
                    if h_inicio <= h_fim:
                        fora_do_horario = not (h_inicio <= agora_time <= h_fim)
                    else:
                        # Horário que ultrapassa meia-noite (ex: 22:00 a 06:00)
                        fora_do_horario = not (agora_time >= h_inicio or agora_time <= h_fim)

                mensagem_auto = None
                tipo_resposta = None

                if fora_do_horario and param_auto.mensagem_ausencia:
                    # Fora do horário configurado → mensagem de ausência
                    mensagem_auto = param_auto.mensagem_ausencia
                    tipo_resposta = "ausência"
                    print(f"⏰ Fora do horário de atendimento - preparando mensagem de ausência")
                elif not horario_configurado and param_auto.mensagem_ausencia:
                    # Sem horário definido e mensagem de ausência configurada → sempre envia ausência
                    mensagem_auto = param_auto.mensagem_ausencia
                    tipo_resposta = "ausência (sem horário definido)"
                    print(f"⏰ Sem horário configurado - preparando mensagem de ausência")
                elif horario_configurado and not fora_do_horario and param_auto.mensagem_boas_vindas:
                    # Dentro do horário → mensagem de boas-vindas na primeira mensagem do cliente
                    qtd_msgs_anteriores = WhatsAppMensagem.query.filter(
                        WhatsAppMensagem.numero == numero,
                        WhatsAppMensagem.id != msg.id
                    ).count()
                    if qtd_msgs_anteriores == 0:
                        mensagem_auto = param_auto.mensagem_boas_vindas
                        tipo_resposta = "boas-vindas"
                        print(f"👋 Primeira mensagem do cliente - preparando mensagem de boas-vindas")

                if mensagem_auto:
                    if usuario_dono and usuario_dono.api_instance and usuario_dono.api_token:
                        resultado_auto = enviar_whatsapp_zapi(
                            numero, mensagem_auto,
                            instance_id=usuario_dono.api_instance,
                            token_id=usuario_dono.api_token
                        )
                        print(f"📤 Resposta automática ({tipo_resposta}) enviada: {resultado_auto.get('status')}")
                    else:
                        print(f"⚠️ Resposta automática ({tipo_resposta}) não enviada: usuário sem Z-API configurada (api_instance/api_token ausentes)")
        except Exception as e:
            print(f"❌ Erro ao processar resposta automática: {e}")

    # ========== ETAPA 6: EMITIR VIA WEBSOCKET ==========
    cliente_found = find_cliente_by_phone(numero)
    nome_cliente = cliente_found.nome if cliente_found else numero
    
    payload = {
        "id": msg.id,
        "numero": numero,
        "nome": nome_cliente,
        "remetente": "Cliente",
        "mensagem": text,
        "hora": datetime.now().strftime("%H:%M"),
        "timestamp": msg.recebido_em.isoformat(),
        "status": "recebida"
    }

    try:
        socketio.emit("nova_mensagem", payload, room=numero)
        socketio.emit("nova_mensagem", payload, broadcast=True)
        print(f"✅ Mensagem emitida via WebSocket para sala: {numero}")
        print(f"✅ Mensagem emitida via broadcast para todos")
    except Exception as e:
        print(f"❌ Erro ao emitir mensagem: {e}")

    print("="*60)
    print("✅ WEBHOOK PROCESSADO COM SUCESSO")
    print("="*60 + "\n")

    return {"status": "ok", "message_id": msg.id}, 200

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

# ==================== NOVOS ENDPOINTS CANAIS AVANÇADOS ====================

@socketio.on('indicador_digitando')
def handle_indicador_digitando(data):
    """Emite indicador de digitando para outros usuários"""
    numero = data.get('numero')
    digitando = data.get('digitando', False)
    
    if numero:
        numero_norm = normalize_phone(numero)
        socketio.emit('usuario_digitando', {
            'numero': numero_norm,
            'digitando': digitando
        }, room=numero_norm, skip_sid=request.sid)

@app.route("/canais/mensagem/<int:msg_id>/status", methods=["PUT"])
@login_required
def atualizar_status_mensagem(msg_id):
    """Atualiza status de mensagem (enviada/entregue/lida)"""
    data = request.get_json()
    status = data.get('status')  # enviada, entregue, lida
    
    msg = WhatsAppMensagem.query.get(msg_id)
    if not msg:
        return jsonify({"erro": "Mensagem não encontrada"}), 404
    
    # Adicionar campo status se não existir (será necessário migração do banco)
    if hasattr(msg, 'status'):
        msg.status = status
        db.session.commit()
    
    return jsonify({"status": "ok", "message_id": msg_id})

@app.route("/canais/conversa/<string:numero>/marcar_lida", methods=["POST"])
@login_required
def marcar_conversa_lida(numero):
    """Marca todas as mensagens de uma conversa como lida"""
    numero_norm = normalize_phone(numero)
    
    # Marcar todas as mensagens não lidas como lidas
    WhatsAppMensagem.query.filter_by(
        numero=numero_norm,
        remetente="Cliente"
    ).update({"lida": True})
    
    db.session.commit()
    
    # Emitir evento para atualizar badge
    socketio.emit('conversa_lida', {'numero': numero_norm}, broadcast=True)
    
    return jsonify({"status": "ok"})

@app.route("/canais/conversa/<string:numero>/fixar", methods=["POST"])
@login_required
def fixar_conversa(numero):
    """Fixa uma conversa no topo"""
    data = request.get_json() or {}
    fixada = data.get('fixada', True)
    numero_norm = normalize_phone(numero)
    user_id = current_user.get_usuario_principal_id()

    config = ConversaConfig.query.filter_by(usuario_crm_id=user_id, telefone=numero_norm).first()
    if not config:
        config = ConversaConfig(usuario_crm_id=user_id, telefone=numero_norm)
        db.session.add(config)
    config.fixada = fixada
    db.session.commit()

    return jsonify({"status": "ok", "fixada": fixada})

@app.route("/canais/conversa/<string:numero>/arquivar", methods=["POST"])
@login_required
def arquivar_conversa(numero):
    """Arquiva uma conversa"""
    data = request.get_json() or {}
    arquivada = data.get('arquivada', True)
    numero_norm = normalize_phone(numero)
    user_id = current_user.get_usuario_principal_id()

    config = ConversaConfig.query.filter_by(usuario_crm_id=user_id, telefone=numero_norm).first()
    if not config:
        config = ConversaConfig(usuario_crm_id=user_id, telefone=numero_norm)
        db.session.add(config)
    config.arquivada = arquivada
    db.session.commit()

    return jsonify({"status": "ok", "arquivada": arquivada})

@app.route("/canais/mensagem/<int:msg_id>/excluir", methods=["DELETE"])
@login_required
def excluir_mensagem(msg_id):
    """Exclui uma mensagem"""
    msg = WhatsAppMensagem.query.get(msg_id)
    if not msg:
        return jsonify({"erro": "Mensagem não encontrada"}), 404
    
    numero = msg.numero
    
    # Deletar do banco
    db.session.delete(msg)
    db.session.commit()
    
    # Notificar via WebSocket
    socketio.emit('mensagem_excluida', {
        'id': msg_id,
        'numero': numero
    }, room=numero)
    
    return jsonify({"status": "ok"})

@app.route("/canais/upload", methods=["POST"])
@login_required
def upload_arquivo_canais():
    """Upload de arquivo (imagem, documento, áudio)"""
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    numero = request.form.get('numero')
    
    if file.filename == '':
        return jsonify({"erro": "Nome de arquivo inválido"}), 400
    
    if not numero:
        return jsonify({"erro": "Número não fornecido"}), 400
    
    # Criar diretório se não existir
    upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'canais')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Gerar nome único para o arquivo
    import uuid
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_folder, unique_filename)
    
    # Salvar arquivo
    file.save(file_path)
    
    # URL relativa para acessar o arquivo
    file_url = f"/static/uploads/canais/{unique_filename}"
    
    # Determinar tipo de arquivo
    file_type = 'document'
    if file_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        file_type = 'image'
    elif file_ext.lower() in ['.mp3', '.wav', '.ogg', '.m4a']:
        file_type = 'audio'
    elif file_ext.lower() in ['.mp4', '.webm', '.mov']:
        file_type = 'video'
    
    numero_norm = normalize_phone(numero)
    
    # Salvar referência no banco
    msg = WhatsAppMensagem(
        numero=numero_norm,
        remetente="Você",
        mensagem=f"[{file_type.upper()}] {file.filename}",
        recebido_em=datetime.utcnow(),
        usuario_crm_id=current_user.get_usuario_principal_id()
    )
    
    # Se tiver campo para tipo de mídia, adicione aqui
    if hasattr(msg, 'tipo_midia'):
        msg.tipo_midia = file_type
        msg.arquivo_url = file_url
    
    db.session.add(msg)
    db.session.commit()
    
    # Emitir via WebSocket
    cliente_found = find_cliente_by_phone(numero_norm)
    nome_cliente = cliente_found.nome if cliente_found else numero_norm
    
    payload = {
        "id": msg.id,
        "numero": numero_norm,
        "nome": nome_cliente,
        "remetente": "Você",
        "mensagem": msg.mensagem,
        "tipo_midia": file_type,
        "arquivo_url": file_url,
        "hora": datetime.now().strftime("%H:%M")
    }
    
    socketio.emit("nova_mensagem", payload, room=numero_norm)
    
    return jsonify({
        "status": "ok",
        "file_url": file_url,
        "file_type": file_type,
        "message_id": msg.id
    })

@app.route("/canais/conversas/nao_lidas", methods=["GET"])
@login_required
def contar_nao_lidas():
    """Retorna contagem de mensagens não lidas por conversa"""
    usuario_principal_id = current_user.get_usuario_principal_id()
    
    # Contar mensagens não lidas por número
    from sqlalchemy import func
    resultado = db.session.query(
        WhatsAppMensagem.numero,
        func.count(WhatsAppMensagem.id).label('count')
    ).filter(
        WhatsAppMensagem.remetente == "Cliente",
        WhatsAppMensagem.usuario_crm_id == usuario_principal_id
    )
    
    # Se tiver campo 'lida', adicionar filtro
    if hasattr(WhatsAppMensagem, 'lida'):
        resultado = resultado.filter(WhatsAppMensagem.lida == False)
    
    resultado = resultado.group_by(WhatsAppMensagem.numero).all()
    
    nao_lidas = {numero: count for numero, count in resultado}
    
    return jsonify(nao_lidas)


# --- CHATBOT
@app.route("/chatbot", methods=["GET", "POST"])
@login_required
@permission_required('chatbot')
def configurar_chatbot():
    if request.method == "POST":
        palavra = request.form.get("palavra_chave", "").strip()
        resposta = request.form.get("resposta", "").strip()
        if not palavra or not resposta:
            return jsonify({"status": "error", "message": "palavra_chave e resposta são obrigatórios"}), 400
        user_id = get_usuario_filter()
        regra = ChatbotRegra(
            palavra_chave=palavra,
            resposta=resposta,
            usuario_crm_id=user_id if user_id else current_user.id
        )
        try:
            db.session.add(regra)
            db.session.commit()
            return jsonify({"status": "success", "message": "Regra criada", "id": regra.id})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar regra chatbot: {e}")
            return jsonify({"status": "error", "message": "Erro ao salvar regra"}), 500
    return redirect(url_for('configuracoes_chatbot'))

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

@app.route("/configuracoes_chatbot", methods=["GET", "POST"])
@login_required
@permission_required('chatbot')
def configuracoes_chatbot():
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
        return redirect(url_for("configuracoes_chatbot"))

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
    - Prioriza clientes com usuario_crm_id definido
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
    
    # Separar clientes com e sem usuario_crm_id
    clientes_com_usuario = [c for c in clientes if c.usuario_crm_id]
    clientes_sem_usuario = [c for c in clientes if not c.usuario_crm_id]
    
    # Buscar primeiro nos clientes com usuario_crm_id, depois nos sem
    for lista_clientes in [clientes_com_usuario, clientes_sem_usuario]:
        for c in lista_clientes:
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
    try:
        dados = request.get_json() or {}
        nome = (dados.get("nome") or "").strip()
        descricao = (dados.get("descricao") or "").strip()
        
        if not nome:
            return jsonify({"status": "erro", "detalhe": "Nome é obrigatório"}), 400
        if not descricao:
            return jsonify({"status": "erro", "detalhe": "Descrição é obrigatória"}), 400

        # Obtém o ID do usuário principal (admin ou super_admin)
        usuario_principal_id = current_user.get_usuario_principal_id()
        
        # Verifica se já existe produto com esse nome para este usuário
        produto_existente = Produto.query.filter_by(
            usuario_crm_id=usuario_principal_id, 
            nome=nome
        ).first()
        
        if produto_existente:
            return jsonify({"status": "erro", "detalhe": "Você já possui um produto com esse nome"}), 400

        # Cria o novo produto
        p = Produto(
            usuario_crm_id=usuario_principal_id,
            nome=nome, 
            descricao=descricao, 
            quantidade=0
        )
        db.session.add(p)
        db.session.commit()
        
        return jsonify({"status": "sucesso", "produto": {"id": p.id, "nome": p.nome}}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao cadastrar produto: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "erro", "detalhe": f"Erro ao salvar produto: {str(e)}"}), 500

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
    
    movimentacoes = Movimentacao.query.filter_by(produto_id=produto.id).order_by(Movimentacao.data_registro.desc()).all()
    return render_template("movimentacoes.html", produto=produto, movimentacoes=movimentacoes)

# ==================== ROTAS DE FORNECEDORES ====================

@app.route("/fornecedores")
@login_required
@permission_required('produtos')
def fornecedores():
    """Lista todos os fornecedores"""
    user_id = get_usuario_filter()
    
    if user_id:
        fornecedores = Fornecedor.query.filter_by(usuario_crm_id=user_id).order_by(Fornecedor.nome).all()
    else:
        fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()
    
    return render_template("fornecedores.html", fornecedores=fornecedores)

@app.route("/api/fornecedores", methods=["GET"])
@login_required
@permission_required('produtos')
def api_listar_fornecedores():
    """Retorna lista de fornecedores em JSON"""
    user_id = get_usuario_filter()
    
    if user_id:
        fornecedores = Fornecedor.query.filter_by(usuario_crm_id=user_id).order_by(Fornecedor.nome).all()
    else:
        fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()
    
    return jsonify([{
        'id': f.id,
        'nome': f.nome,
        'nome_fantasia': f.nome_fantasia,
        'cnpj_cpf': f.cnpj_cpf,
        'email': f.email,
        'telefone': f.telefone,
        'celular': f.celular,
        'cidade': f.cidade,
        'estado': f.estado,
        'status': f.status,
        'avaliacao': f.avaliacao,
        'produtos_servicos': f.produtos_servicos
    } for f in fornecedores])

@app.route("/api/fornecedores/add", methods=["POST"])
@login_required
@permission_required('produtos')
def api_add_fornecedor():
    """Adiciona um novo fornecedor"""
    try:
        data = request.get_json()
        user_id = get_usuario_filter()
        
        novo_fornecedor = Fornecedor(
            usuario_crm_id=user_id,
            nome=data.get('nome'),
            nome_fantasia=data.get('nome_fantasia'),
            cnpj_cpf=data.get('cnpj_cpf'),
            inscricao_estadual=data.get('inscricao_estadual'),
            email=data.get('email'),
            telefone=data.get('telefone'),
            celular=data.get('celular'),
            site=data.get('site'),
            cep=data.get('cep'),
            logradouro=data.get('logradouro'),
            numero=data.get('numero'),
            complemento=data.get('complemento'),
            bairro=data.get('bairro'),
            cidade=data.get('cidade'),
            estado=data.get('estado'),
            produtos_servicos=data.get('produtos_servicos'),
            prazo_entrega=data.get('prazo_entrega'),
            prazo_pagamento=data.get('prazo_pagamento'),
            banco=data.get('banco'),
            agencia=data.get('agencia'),
            conta=data.get('conta'),
            pix=data.get('pix'),
            contato_nome=data.get('contato_nome'),
            contato_cargo=data.get('contato_cargo'),
            contato_telefone=data.get('contato_telefone'),
            contato_email=data.get('contato_email'),
            avaliacao=data.get('avaliacao'),
            status=data.get('status', 'Ativo'),
            observacoes=data.get('observacoes')
        )
        
        db.session.add(novo_fornecedor)
        db.session.commit()
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': 'Fornecedor cadastrado com sucesso',
            'id': novo_fornecedor.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400

@app.route("/api/fornecedores/<int:fornecedor_id>", methods=["GET"])
@login_required
@permission_required('produtos')
def api_get_fornecedor(fornecedor_id):
    """Retorna dados de um fornecedor específico"""
    user_id = get_usuario_filter()
    
    if user_id:
        fornecedor = Fornecedor.query.filter_by(id=fornecedor_id, usuario_crm_id=user_id).first_or_404()
    else:
        fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
    
    return jsonify({
        'id': fornecedor.id,
        'nome': fornecedor.nome,
        'nome_fantasia': fornecedor.nome_fantasia,
        'cnpj_cpf': fornecedor.cnpj_cpf,
        'inscricao_estadual': fornecedor.inscricao_estadual,
        'email': fornecedor.email,
        'telefone': fornecedor.telefone,
        'celular': fornecedor.celular,
        'site': fornecedor.site,
        'cep': fornecedor.cep,
        'logradouro': fornecedor.logradouro,
        'numero': fornecedor.numero,
        'complemento': fornecedor.complemento,
        'bairro': fornecedor.bairro,
        'cidade': fornecedor.cidade,
        'estado': fornecedor.estado,
        'produtos_servicos': fornecedor.produtos_servicos,
        'prazo_entrega': fornecedor.prazo_entrega,
        'prazo_pagamento': fornecedor.prazo_pagamento,
        'banco': fornecedor.banco,
        'agencia': fornecedor.agencia,
        'conta': fornecedor.conta,
        'pix': fornecedor.pix,
        'contato_nome': fornecedor.contato_nome,
        'contato_cargo': fornecedor.contato_cargo,
        'contato_telefone': fornecedor.contato_telefone,
        'contato_email': fornecedor.contato_email,
        'avaliacao': fornecedor.avaliacao,
        'status': fornecedor.status,
        'observacoes': fornecedor.observacoes,
        'data_cadastro': fornecedor.data_cadastro.strftime('%d/%m/%Y %H:%M') if fornecedor.data_cadastro else None
    })

@app.route("/api/fornecedores/<int:fornecedor_id>", methods=["PUT"])
@login_required
@permission_required('produtos')
def api_update_fornecedor(fornecedor_id):
    """Atualiza dados de um fornecedor"""
    try:
        user_id = get_usuario_filter()
        
        if user_id:
            fornecedor = Fornecedor.query.filter_by(id=fornecedor_id, usuario_crm_id=user_id).first_or_404()
        else:
            fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
        
        data = request.get_json()
        
        # Atualiza os campos
        fornecedor.nome = data.get('nome', fornecedor.nome)
        fornecedor.nome_fantasia = data.get('nome_fantasia', fornecedor.nome_fantasia)
        fornecedor.cnpj_cpf = data.get('cnpj_cpf', fornecedor.cnpj_cpf)
        fornecedor.inscricao_estadual = data.get('inscricao_estadual', fornecedor.inscricao_estadual)
        fornecedor.email = data.get('email', fornecedor.email)
        fornecedor.telefone = data.get('telefone', fornecedor.telefone)
        fornecedor.celular = data.get('celular', fornecedor.celular)
        fornecedor.site = data.get('site', fornecedor.site)
        fornecedor.cep = data.get('cep', fornecedor.cep)
        fornecedor.logradouro = data.get('logradouro', fornecedor.logradouro)
        fornecedor.numero = data.get('numero', fornecedor.numero)
        fornecedor.complemento = data.get('complemento', fornecedor.complemento)
        fornecedor.bairro = data.get('bairro', fornecedor.bairro)
        fornecedor.cidade = data.get('cidade', fornecedor.cidade)
        fornecedor.estado = data.get('estado', fornecedor.estado)
        fornecedor.produtos_servicos = data.get('produtos_servicos', fornecedor.produtos_servicos)
        fornecedor.prazo_entrega = data.get('prazo_entrega', fornecedor.prazo_entrega)
        fornecedor.prazo_pagamento = data.get('prazo_pagamento', fornecedor.prazo_pagamento)
        fornecedor.banco = data.get('banco', fornecedor.banco)
        fornecedor.agencia = data.get('agencia', fornecedor.agencia)
        fornecedor.conta = data.get('conta', fornecedor.conta)
        fornecedor.pix = data.get('pix', fornecedor.pix)
        fornecedor.contato_nome = data.get('contato_nome', fornecedor.contato_nome)
        fornecedor.contato_cargo = data.get('contato_cargo', fornecedor.contato_cargo)
        fornecedor.contato_telefone = data.get('contato_telefone', fornecedor.contato_telefone)
        fornecedor.contato_email = data.get('contato_email', fornecedor.contato_email)
        fornecedor.avaliacao = data.get('avaliacao', fornecedor.avaliacao)
        fornecedor.status = data.get('status', fornecedor.status)
        fornecedor.observacoes = data.get('observacoes', fornecedor.observacoes)
        
        db.session.commit()
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': 'Fornecedor atualizado com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400

@app.route("/api/fornecedores/<int:fornecedor_id>", methods=["DELETE"])
@login_required
@permission_required('produtos')
def api_deletar_fornecedor(fornecedor_id):
    """Exclui um fornecedor"""
    try:
        user_id = get_usuario_filter()
        
        if user_id:
            fornecedor = Fornecedor.query.filter_by(id=fornecedor_id, usuario_crm_id=user_id).first_or_404()
        else:
            fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
        
        nome_fornecedor = fornecedor.nome
        
        db.session.delete(fornecedor)
        db.session.commit()
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': f'Fornecedor "{nome_fornecedor}" excluído com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400

# ==================== FIM ROTAS FORNECEDORES ====================

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
    hora_atual = datetime.strptime("00:00", "%H:%M")
    hora_limite = datetime.strptime("23:30", "%H:%M")

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
@login_required
def salvar_evento():
    tipo = request.form["tipo"]
    cliente = request.form.get("cliente")
    data_str = request.form["data"]
    hora_str = request.form["hora"]
    descricao = request.form.get("descricao")

    # Junta a data + hora corretamente
    data_hora = datetime.strptime(f"{data_str} {hora_str}", "%Y-%m-%d %H:%M")

    novo = PlannerEvento(
        usuario_crm_id=current_user.get_usuario_principal_id(),
        tipo=tipo,
        cliente=cliente,
        data=datetime.strptime(data_str, "%Y-%m-%d").date(),
        hora=datetime.strptime(hora_str, "%H:%M").time(),
        data_hora=data_hora,
        descricao=descricao
    )

    db.session.add(novo)
    db.session.commit()

    return redirect(url_for("planner"))

@app.route("/planner/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_evento(id):
    evento = PlannerEvento.query.get(id)

    if not evento:
        return "Evento não encontrado", 404

    db.session.delete(evento)
    db.session.commit()

    return redirect(url_for("planner"))


# --- TAREFAS
@app.route("/tarefas", methods=["GET", "POST"])
@login_required
@permission_required('tarefas')
def tarefas():
    user_id = current_user.get_usuario_principal_id()

    if request.method == "POST":
        titulo = request.form.get("titulo")
        descricao = request.form.get("descricao")
        prioridade = request.form.get("prioridade") or "Normal"
        cliente_id = request.form.get("cliente_id") or None
        mesa_id = request.form.get("mesa_id") or None

        data_vencimento = request.form.get("data_vencimento")
        hora_vencimento = request.form.get("hora_vencimento")
        lembrete_em = request.form.get("lembrete_em")

        tarefa = Tarefa(
            usuario_crm_id=user_id,
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade,
            status="Pendente"
        )

        if cliente_id:
            cliente = Cliente.query.filter_by(id=int(cliente_id), usuario_crm_id=user_id).first()
            if cliente:
                tarefa.cliente_id = cliente.id
        if mesa_id:
            mesa = MesaNegocio.query.filter_by(id=int(mesa_id), usuario_crm_id=user_id).first()
            if mesa:
                tarefa.mesa_negocio_id = mesa.id
                if not tarefa.cliente_id:
                    tarefa.cliente_id = mesa.cliente_id

        if data_vencimento:
            try:
                tarefa.data_vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
            except Exception:
                pass
        if hora_vencimento:
            try:
                tarefa.hora_vencimento = datetime.strptime(hora_vencimento, "%H:%M").time()
            except Exception:
                pass
        if lembrete_em:
            try:
                tarefa.lembrete_em = datetime.strptime(lembrete_em, "%Y-%m-%dT%H:%M")
            except Exception:
                pass

        db.session.add(tarefa)
        db.session.commit()
        flash("Tarefa criada com sucesso!", "success")
        return redirect(url_for("tarefas"))

    filtro_status = request.args.get("status", "todas")

    tarefas_query = Tarefa.query.filter_by(usuario_crm_id=user_id).order_by(Tarefa.criado_em.desc())
    todas_tarefas = tarefas_query.all()
    tarefas_lista = list(todas_tarefas)

    hoje = datetime.today().date()
    agora = datetime.now().time()

    def is_atrasada(t):
        if t.status == "Concluída":
            return False
        if t.data_vencimento and t.data_vencimento < hoje:
            return True
        if t.data_vencimento == hoje and t.hora_vencimento and t.hora_vencimento < agora:
            return True
        return False

    if filtro_status == "pendentes":
        tarefas_lista = [t for t in tarefas_lista if t.status != "Concluída"]
    elif filtro_status == "concluidas":
        tarefas_lista = [t for t in tarefas_lista if t.status == "Concluída"]
    elif filtro_status == "atrasadas":
        tarefas_lista = [t for t in tarefas_lista if is_atrasada(t)]

    total = len(todas_tarefas)
    pendentes = len([t for t in todas_tarefas if t.status != "Concluída"])
    concluidas = len([t for t in todas_tarefas if t.status == "Concluída"])
    atrasadas = len([t for t in todas_tarefas if is_atrasada(t)])

    # Dados para selects
    clientes = Cliente.query.filter_by(usuario_crm_id=user_id).order_by(Cliente.nome).all()
    mesas = MesaNegocio.query.filter_by(usuario_crm_id=user_id).order_by(MesaNegocio.id.desc()).all()

    return render_template(
        "tarefas.html",
        tarefas=tarefas_lista,
        total=total,
        pendentes=pendentes,
        concluidas=concluidas,
        atrasadas=atrasadas,
        filtro_status=filtro_status,
        clientes=clientes,
        mesas=mesas
    )


@app.route("/tarefas/<int:id>/status", methods=["POST"])
@login_required
@permission_required('tarefas')
def atualizar_status_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)
    status = request.form.get("status")
    if status == "Concluída":
        tarefa.status = "Concluída"
        tarefa.concluido_em = datetime.utcnow()
    else:
        tarefa.status = "Pendente"
        tarefa.concluido_em = None
    db.session.commit()
    return redirect(url_for("tarefas"))


@app.route("/tarefas/<int:id>/excluir", methods=["POST"])
@login_required
@permission_required('tarefas')
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)
    db.session.delete(tarefa)
    db.session.commit()
    flash("Tarefa excluída com sucesso!", "success")
    return redirect(url_for("tarefas"))


# --- RELATÓRIOS
@app.route("/relatorios")
@login_required
@permission_required('relatorios')
def relatorios():
    user_id = get_usuario_filter()

    if user_id:
        base_filter_cliente = Cliente.usuario_crm_id == user_id
        base_filter_mesa = MesaNegocio.usuario_crm_id == user_id
        base_filter_ocorrencia = Ocorrencia.usuario_crm_id == user_id
    else:
        base_filter_cliente = True
        base_filter_mesa = True
        base_filter_ocorrencia = True

    mesas = MesaNegocio.query.filter(base_filter_mesa).all()
    total_mesas = len(mesas)
    mesas_ganhas = len([m for m in mesas if m.situacao == "Ganho"])
    mesas_perdidas = len([m for m in mesas if m.situacao == "Perdido"])
    mesas_andamento = len([m for m in mesas if m.situacao == "Em negociação"])
    conversao = (mesas_ganhas / total_mesas * 100) if total_mesas else 0

    # Tempo de ciclo (dias) entre registro e fechamento
    ciclos = [
        (m.data_fechamento - m.data_registro).days
        for m in mesas
        if m.data_fechamento and m.data_registro
    ]
    tempo_ciclo_medio = round(sum(ciclos) / len(ciclos), 2) if ciclos else 0

    # NPS por mês (últimos 6 meses)
    hoje = datetime.today().date()
    meses_labels = []
    nps_medias = []
    nps_quantidades = []

    for i in range(5, -1, -1):
        ref = hoje.replace(day=1) - timedelta(days=30 * i)
        ano = ref.year
        mes = ref.month
        inicio = datetime(ano, mes, 1)
        if mes == 12:
            fim = datetime(ano + 1, 1, 1)
        else:
            fim = datetime(ano, mes + 1, 1)

        clientes_mes = Cliente.query.filter(
            base_filter_cliente,
            Cliente.nps_data.isnot(None),
            Cliente.nps_data >= inicio,
            Cliente.nps_data < fim
        ).all()
        notas = [c.nps_nota for c in clientes_mes if c.nps_nota is not None]
        media = round(sum(notas) / len(notas), 2) if notas else 0

        meses_labels.append(inicio.strftime("%m/%Y"))
        nps_medias.append(media)
        nps_quantidades.append(len(notas))

    # Vendas por mês (últimos 6 meses)
    vendas_labels = meses_labels
    vendas_valores = []
    for i in range(5, -1, -1):
        ref = hoje.replace(day=1) - timedelta(days=30 * i)
        ano = ref.year
        mes = ref.month
        inicio = datetime(ano, mes, 1)
        if mes == 12:
            fim = datetime(ano + 1, 1, 1)
        else:
            fim = datetime(ano, mes + 1, 1)

        total_mes = sum(
            m.valor_total or 0
            for m in mesas
            if m.situacao == "Ganho" and m.data_registro and inicio.date() <= m.data_registro < fim.date()
        )
        vendas_valores.append(round(total_mes, 2))

    # Ocorrências por status
    ocorrencias_total = Ocorrencia.query.filter(base_filter_ocorrencia).count()

    return render_template(
        "relatorios.html",
        total_mesas=total_mesas,
        mesas_ganhas=mesas_ganhas,
        mesas_perdidas=mesas_perdidas,
        mesas_andamento=mesas_andamento,
        conversao=round(conversao, 2),
        tempo_ciclo_medio=tempo_ciclo_medio,
        meses_labels=meses_labels,
        nps_medias=nps_medias,
        nps_quantidades=nps_quantidades,
        vendas_labels=vendas_labels,
        vendas_valores=vendas_valores,
        ocorrencias_total=ocorrencias_total
    )


# quando criar cliente, emitir novo_contato para atualizar lista (opcional)
def emitir_novo_contato(cliente):
    socketio.emit('novo_contato', {
        'id': cliente.id,
        'nome': cliente.nome,
        'telefone': cliente.telefone
    }, broadcast=True)

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



