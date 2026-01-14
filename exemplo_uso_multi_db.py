# exemplo_uso_multi_db.py
"""
Exemplo de como usar o sistema com múltiplos bancos de dados
"""
from flask import Flask, g
from flask_login import current_user
from database_manager import db_central, db_manager
from models_central import UsuarioCRM
from models import Cliente, MesaNegocio

# ==========================================
# 1. CONFIGURAÇÃO INICIAL DO FLASK
# ==========================================

app = Flask(__name__)
app.secret_key = "seusegredo"

# Banco CENTRAL (apenas para UsuarioCRM)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Amovoce123%40@localhost:1222/crm_central'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db_central.init_app(app)

# Criar tabelas do banco central
with app.app_context():
    db_central.create_all()

# ==========================================
# 2. HELPER: CONEXÃO DINÂMICA POR USUÁRIO
# ==========================================

def get_cliente_db_session():
    """
    Retorna a sessão do banco de dados do cliente logado
    Usa o contexto Flask 'g' para cache por requisição
    """
    if not hasattr(g, 'cliente_db_session'):
        usuario_id = current_user.get_usuario_principal_id()
        g.cliente_db_session = db_manager.get_session(usuario_id)
    return g.cliente_db_session

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Fecha a sessão do banco do cliente ao fim da requisição"""
    session = g.pop('cliente_db_session', None)
    if session is not None:
        session.close()

# ==========================================
# 3. EXEMPLO: CRIAR NOVO CLIENTE DO CRM
# ==========================================

@app.route('/admin/criar_cliente_crm', methods=['POST'])
def criar_cliente_crm():
    """
    Quando um novo cliente assina o CRM:
    1. Cria registro no banco central
    2. Cria banco de dados exclusivo para ele
    """
    from flask import request, jsonify
    
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    # 1. Cria usuário no banco CENTRAL
    novo_usuario = UsuarioCRM(
        nome=nome,
        email=email,
        tipo_usuario='admin',
        ativo=True
    )
    novo_usuario.set_password(senha)
    
    db_central.session.add(novo_usuario)
    db_central.session.commit()
    
    # 2. Cria banco de dados DEDICADO para este cliente
    sucesso, mensagem = db_manager.criar_banco_cliente(
        usuario_crm_id=novo_usuario.id,
        usuario_nome=novo_usuario.nome
    )
    
    if sucesso:
        # Atualiza registro indicando que o banco foi criado
        novo_usuario.database_name = db_manager.get_database_name(novo_usuario.id)
        novo_usuario.database_criado = True
        db_central.session.commit()
        
        return jsonify({
            'success': True,
            'mensagem': f'Cliente {nome} criado com sucesso!',
            'database': novo_usuario.database_name
        })
    else:
        # Se falhar, remove o usuário
        db_central.session.delete(novo_usuario)
        db_central.session.commit()
        return jsonify({'success': False, 'erro': mensagem}), 500

# ==========================================
# 4. EXEMPLO: OPERAÇÕES NO BANCO DO CLIENTE
# ==========================================

@app.route('/clientes/listar')
def listar_clientes():
    """
    Lista clientes do banco do usuário logado
    Cada admin vê apenas seus próprios clientes
    """
    from flask_login import login_required
    from flask import render_template
    
    # Pega a sessão do banco específico do cliente
    session = get_cliente_db_session()
    
    # Consulta clientes NO BANCO DESTE CLIENTE
    clientes = session.query(Cliente).order_by(Cliente.nome).all()
    
    return render_template('cadastro.html', clientes=clientes)

@app.route('/clientes/adicionar', methods=['POST'])
def adicionar_cliente():
    """Adiciona cliente no banco do usuário logado"""
    from flask import request, redirect, url_for, flash
    
    nome = request.form.get('nome')
    telefone = request.form.get('telefone')
    
    # Usa context manager para operações transacionais
    usuario_id = current_user.get_usuario_principal_id()
    
    with db_manager.session_scope(usuario_id) as session:
        novo_cliente = Cliente(
            nome=nome,
            telefone=telefone,
            tipo_pessoa='Cliente'
        )
        session.add(novo_cliente)
        # Commit automático ao sair do 'with'
    
    flash('Cliente adicionado com sucesso!', 'success')
    return redirect(url_for('listar_clientes'))

# ==========================================
# 5. EXEMPLO: MIGRAR TODOS OS BANCOS
# ==========================================

def migrar_todos_os_bancos():
    """
    Executa migrações em TODOS os bancos de clientes
    Útil quando adiciona novas tabelas ou colunas
    """
    with app.app_context():
        # Busca todos os clientes admin
        admins = UsuarioCRM.query.filter_by(tipo_usuario='admin', ativo=True).all()
        
        print(f"\n🔄 Migrando {len(admins)} bancos de clientes...\n")
        
        for admin in admins:
            if admin.database_criado:
                print(f"📊 Migrando banco: {admin.database_name} ({admin.nome})")
                sucesso, msg = db_manager.migrar_banco_cliente(admin.id)
                
                if sucesso:
                    print(f"  ✅ {msg}")
                else:
                    print(f"  ❌ {msg}")
        
        print("\n✅ Migração concluída!\n")

# ==========================================
# 6. EXEMPLO: BACKUP DE UM CLIENTE
# ==========================================

def backup_cliente(usuario_crm_id):
    """
    Faz backup do banco de um cliente específico
    """
    import subprocess
    from datetime import datetime
    
    db_name = db_manager.get_database_name(usuario_crm_id)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{db_name}_{timestamp}.sql"
    
    comando = [
        'pg_dump',
        '-h', db_manager.pg_host,
        '-p', str(db_manager.pg_port),
        '-U', db_manager.pg_user,
        '-d', db_name,
        '-f', backup_file
    ]
    
    try:
        subprocess.run(comando, check=True)
        print(f"✅ Backup criado: {backup_file}")
        return True, backup_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no backup: {e}")
        return False, str(e)

# ==========================================
# 7. EXEMPLO: LISTAR TODOS OS BANCOS
# ==========================================

@app.route('/admin/bancos')
def listar_bancos():
    """Lista todos os bancos de clientes (apenas super_admin)"""
    from flask import render_template
    
    if current_user.tipo_usuario != 'super_admin':
        return "Acesso negado", 403
    
    bancos = db_manager.listar_bancos_clientes()
    
    # Busca informações dos clientes
    info_bancos = []
    for db_name in bancos:
        # Extrai ID do nome do banco (crm_cliente_123 -> 123)
        try:
            cliente_id = int(db_name.replace('crm_cliente_', ''))
            usuario = UsuarioCRM.query.get(cliente_id)
            
            info_bancos.append({
                'db_name': db_name,
                'cliente_id': cliente_id,
                'cliente_nome': usuario.nome if usuario else 'N/A',
                'ativo': usuario.ativo if usuario else False
            })
        except:
            info_bancos.append({
                'db_name': db_name,
                'cliente_id': None,
                'cliente_nome': 'Desconhecido',
                'ativo': False
            })
    
    return render_template('admin_bancos.html', bancos=info_bancos)

# ==========================================
# 8. SCRIPT DE INICIALIZAÇÃO
# ==========================================

if __name__ == '__main__':
    with app.app_context():
        # Verifica se super admin existe
        super_admin = UsuarioCRM.query.filter_by(tipo_usuario='super_admin').first()
        
        if not super_admin:
            print("\n🔧 Criando Super Admin...\n")
            super_admin = UsuarioCRM(
                nome='Administrador',
                email='admin@crm.com',
                tipo_usuario='super_admin',
                ativo=True
            )
            super_admin.set_password('admin123')
            db_central.session.add(super_admin)
            db_central.session.commit()
            print("✅ Super Admin criado: admin@crm.com / admin123\n")
        
        # Lista bancos existentes
        bancos = db_manager.listar_bancos_clientes()
        print(f"📊 Bancos de clientes ativos: {len(bancos)}")
        for banco in bancos:
            print(f"  - {banco}")
    
    app.run(debug=True)
